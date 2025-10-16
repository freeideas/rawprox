use chrono::Utc;
use serde::Serialize;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::time::SystemTime;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

const BUFFER_SIZE: usize = 32 * 1024; // 32KB

// Windows UTF-8 console initialization
#[cfg(windows)]
fn init_utf8_console() {
    unsafe {
        // Set console output code page to UTF-8 (CP_UTF8 = 65001)
        // This ensures stdout outputs UTF-8 when redirected to files
        const CP_UTF8: u32 = 65001;

        #[link(name = "kernel32")]
        extern "system" {
            fn SetConsoleOutputCP(code_page: u32) -> i32;
        }

        SetConsoleOutputCP(CP_UTF8);
    }
}

// Base62 alphabet
const BASE62: &[u8] = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

// Log entry types
#[derive(Serialize)]
struct EventEntry {
    time: String,
    #[serde(rename = "ConnID")]
    conn_id: String,
    event: String,
    from: String,
    to: String,
}

#[derive(Serialize)]
struct DataEntry {
    time: String,
    #[serde(rename = "ConnID")]
    conn_id: String,
    data: String,
    from: String,
    to: String,
}

// Convert u64 to 5-character base62 string
fn to_base62(mut num: u64) -> String {
    let mut result = vec![b'0'; 5];
    for i in (0..5).rev() {
        result[i] = BASE62[(num % 62) as usize];
        num /= 62;
    }
    String::from_utf8(result).unwrap()
}

// Get current timestamp in ISO 8601 format with microsecond precision
fn get_timestamp() -> String {
    let now = Utc::now();
    now.format("%Y-%m-%dT%H:%M:%S%.6fZ").to_string()
}

// Encode data per SPECIFICATION.md §5: JSON escapes for common control chars, percent-encoding for others
fn encode_data(data: &[u8]) -> String {
    let mut result = String::with_capacity(data.len() * 2); // Reserve more space for encoding

    for &byte in data {
        match byte {
            // JSON escape sequences - include actual control character, serde_json will escape it
            b'\n' => result.push('\n'),       // 0x0A - line feed (serde_json → \n)
            b'\r' => result.push('\r'),       // 0x0D - carriage return (serde_json → \r)
            b'\t' => result.push('\t'),       // 0x09 - tab (serde_json → \t)
            0x08 => result.push('\u{0008}'),  // backspace (serde_json → \b)
            0x0C => result.push('\u{000C}'),  // form feed (serde_json → \f)
            b'"' => result.push('"'),         // quote (serde_json → \")
            b'\\' => result.push('\\'),       // backslash (serde_json → \\)

            // Percent sign (meta-character in our encoding) - percent-encode it
            b'%' => result.push_str("%25"),   // 0x25

            // Other control characters (0x00-0x1F, 0x7F) - percent-encode with %XX (uppercase hex)
            0x00..=0x1F | 0x7F => {
                result.push_str(&format!("%{:02X}", byte));
            }

            // Non-ASCII bytes (0x80-0xFF) - percent-encode with %XX (uppercase hex)
            0x80..=0xFF => {
                result.push_str(&format!("%{:02X}", byte));
            }

            // Printable ASCII (0x20-0x7E, excluding special cases above) - preserve as-is
            0x20..=0x7E => {
                result.push(byte as char);
            }
        }
    }

    result
}

// Log writer - runs in a blocking thread for immediate writes
fn log_writer_blocking(rx: std::sync::mpsc::Receiver<String>, mut writer: Box<dyn std::io::Write + Send>) {
    use std::io::Write;

    loop {
        match rx.recv() {
            Ok(line) => {
                // Write line + newline
                if let Err(e) = writer.write_all(line.as_bytes()) {
                    eprintln!("Failed to write to output: {}", e);
                    break;
                }
                if let Err(e) = writer.write_all(b"\n") {
                    eprintln!("Failed to write newline to output: {}", e);
                    break;
                }

                // Flush immediately after each line for network drive compatibility
                if let Err(e) = writer.flush() {
                    eprintln!("Failed to flush output: {}", e);
                    break;
                }
            }
            Err(std::sync::mpsc::RecvError) => {
                // Channel closed, flush and exit
                let _ = writer.flush();
                break;
            }
        }
    }
}

// Handle a single connection
async fn handle_connection(
    client: TcpStream,
    client_addr: SocketAddr,
    target_host: String,
    target_port: u16,
    conn_id: String,
    log_tx: std::sync::mpsc::SyncSender<String>,
) {
    // Connect to target server
    let target_addr = format!("{}:{}", target_host, target_port);
    let server = match TcpStream::connect(&target_addr).await {
        Ok(s) => s,
        Err(_) => {
            // Connection failed, close client socket without logging
            return;
        }
    };

    let server_addr = match server.peer_addr() {
        Ok(addr) => addr,
        Err(_) => return,
    };

    // Format addresses
    let client_addr_str = format!("{}", client_addr);
    let server_addr_str = format!("{}", server_addr);

    // Log open event
    let open_event = EventEntry {
        time: get_timestamp(),
        conn_id: conn_id.clone(),
        event: "open".to_string(),
        from: client_addr_str.clone(),
        to: server_addr_str.clone(),
    };
    let _ = log_tx.try_send(serde_json::to_string(&open_event).unwrap());

    // Split streams
    let (mut client_read, mut client_write) = tokio::io::split(client);
    let (mut server_read, mut server_write) = tokio::io::split(server);

    let log_tx_c2s = log_tx.clone();
    let log_tx_s2c = log_tx.clone();
    let conn_id_c2s = conn_id.clone();
    let conn_id_s2c = conn_id.clone();
    let client_addr_c2s = client_addr_str.clone();
    let server_addr_c2s = server_addr_str.clone();
    let client_addr_s2c = client_addr_str.clone();
    let server_addr_s2c = server_addr_str.clone();

    // Client to server forwarding
    let c2s = tokio::spawn(async move {
        let mut buffer = vec![0u8; BUFFER_SIZE];
        let mut close_from_client = false;

        loop {
            match client_read.read(&mut buffer).await {
                Ok(0) => {
                    // EOF from client
                    close_from_client = true;
                    break;
                }
                Ok(n) => {
                    // Forward to server first
                    if let Err(_) = server_write.write_all(&buffer[..n]).await {
                        break;
                    }

                    // Then log data (after forwarding to avoid blocking)
                    let data_entry = DataEntry {
                        time: get_timestamp(),
                        conn_id: conn_id_c2s.clone(),
                        data: encode_data(&buffer[..n]),
                        from: client_addr_c2s.clone(),
                        to: server_addr_c2s.clone(),
                    };
                    let _ = log_tx_c2s.try_send(serde_json::to_string(&data_entry).unwrap());
                }
                Err(_) => break,
            }
        }

        close_from_client
    });

    // Server to client forwarding
    let s2c = tokio::spawn(async move {
        let mut buffer = vec![0u8; BUFFER_SIZE];
        let mut close_from_server = false;

        loop {
            match server_read.read(&mut buffer).await {
                Ok(0) => {
                    // EOF from server
                    close_from_server = true;
                    break;
                }
                Ok(n) => {
                    // Forward to client first
                    if let Err(_) = client_write.write_all(&buffer[..n]).await {
                        break;
                    }

                    // Then log data (after forwarding to avoid blocking)
                    let data_entry = DataEntry {
                        time: get_timestamp(),
                        conn_id: conn_id_s2c.clone(),
                        data: encode_data(&buffer[..n]),
                        from: server_addr_s2c.clone(),
                        to: client_addr_s2c.clone(),
                    };
                    let _ = log_tx_s2c.try_send(serde_json::to_string(&data_entry).unwrap());
                }
                Err(_) => break,
            }
        }

        close_from_server
    });

    // Wait for both directions to complete
    let (c2s_result, s2c_result) = tokio::join!(c2s, s2c);

    // Determine who closed the connection
    let (close_from, close_to) = match (c2s_result, s2c_result) {
        (Ok(true), _) => (client_addr_str, server_addr_str),
        (_, Ok(true)) => (server_addr_str, client_addr_str),
        _ => (server_addr_str, client_addr_str), // Default to server closed
    };

    // Log close event
    let close_event = EventEntry {
        time: get_timestamp(),
        conn_id,
        event: "close".to_string(),
        from: close_from,
        to: close_to,
    };
    let _ = log_tx.try_send(serde_json::to_string(&close_event).unwrap());
}

// Port forwarding rule
#[derive(Clone)]
struct ForwardingRule {
    local_port: u16,
    target_host: String,
    target_port: u16,
}

// Parse a port forwarding rule from the format LOCAL_PORT:TARGET_HOST:TARGET_PORT
fn parse_forwarding_rule(arg: &str) -> Result<ForwardingRule, String> {
    let parts: Vec<&str> = arg.split(':').collect();

    if parts.len() != 3 {
        return Err(format!("Invalid format '{}'. Expected LOCAL_PORT:TARGET_HOST:TARGET_PORT", arg));
    }

    let local_port = parts[0].parse::<u16>()
        .map_err(|_| format!("Invalid local port '{}'. Must be 1-65535", parts[0]))?;

    let target_host = parts[1].to_string();

    if target_host.is_empty() {
        return Err("Target host cannot be empty".to_string());
    }

    let target_port = parts[2].parse::<u16>()
        .map_err(|_| format!("Invalid target port '{}'. Must be 1-65535", parts[2]))?;

    Ok(ForwardingRule {
        local_port,
        target_host,
        target_port,
    })
}

// Listener task for a single port forwarding rule
async fn run_listener(
    rule: ForwardingRule,
    conn_counter: Arc<AtomicU64>,
    log_tx: std::sync::mpsc::SyncSender<String>,
    shutdown: Arc<AtomicBool>,
) {
    // Bind to local port
    let bind_addr = format!("0.0.0.0:{}", rule.local_port);
    let listener = match TcpListener::bind(&bind_addr).await {
        Ok(l) => l,
        Err(e) => {
            // Provide user-friendly error messages for common cases
            let error_kind = e.kind();
            match error_kind {
                std::io::ErrorKind::AddrInUse => {
                    eprintln!("Error: Port {} is already in use", rule.local_port);
                    eprintln!("Another process is listening on this port. Choose a different port or stop the conflicting process.");
                }
                std::io::ErrorKind::PermissionDenied => {
                    eprintln!("Error: Permission denied to bind to port {}", rule.local_port);
                    eprintln!("Ports below 1024 typically require administrator/root privileges.");
                }
                _ => {
                    eprintln!("Error: Failed to bind to port {}: {}", rule.local_port, e);
                }
            }
            std::process::exit(1);
        }
    };

    // Accept connections
    loop {
        // Check if shutdown has been requested
        if shutdown.load(Ordering::Relaxed) {
            break;
        }

        // Use a timeout so we can check shutdown flag periodically
        let accept_result = tokio::time::timeout(
            std::time::Duration::from_millis(100),
            listener.accept()
        ).await;

        match accept_result {
            Ok(Ok((client, client_addr))) => {
                let conn_id = to_base62(conn_counter.fetch_add(1, Ordering::SeqCst));
                let target_host_clone = rule.target_host.clone();
                let log_tx_clone = log_tx.clone();

                tokio::spawn(handle_connection(
                    client,
                    client_addr,
                    target_host_clone,
                    rule.target_port,
                    conn_id,
                    log_tx_clone,
                ));
            }
            Ok(Err(e)) => {
                eprintln!("Error: Failed to accept connection on port {}: {}", rule.local_port, e);
            }
            Err(_) => {
                // Timeout - just loop and check shutdown flag again
                continue;
            }
        }
    }
}

#[tokio::main]
async fn main() {
    // Initialize UTF-8 console mode on Windows
    #[cfg(windows)]
    init_utf8_console();

    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: {} [ARGS ...]", args[0]);
        eprintln!();
        eprintln!("Arguments:");
        eprintln!("  LOCAL_PORT:TARGET_HOST:TARGET_PORT  Port forwarding rule (at least one required)");
        eprintln!("  @FILEPATH                           Output to file instead of stdout (optional)");
        eprintln!();
        eprintln!("Examples:");
        eprintln!("  {} 8080:example.com:80", args[0]);
        eprintln!("  {} 8080:api.example.com:80 3306:db.example.com:3306", args[0]);
        eprintln!("  {} 8080:example.com:80 @traffic.ndjson", args[0]);
        std::process::exit(1);
    }

    // Parse forwarding rules and optional output file
    let mut rules = Vec::new();
    let mut output_file: Option<String> = None;

    for arg in &args[1..] {
        if arg.starts_with('@') {
            // Output file specifier (last one wins if multiple specified)
            output_file = Some(arg[1..].to_string());
        } else {
            // Port forwarding rule
            match parse_forwarding_rule(arg) {
                Ok(rule) => rules.push(rule),
                Err(e) => {
                    eprintln!("Error: {}", e);
                    std::process::exit(1);
                }
            }
        }
    }

    // Ensure at least one forwarding rule was specified
    if rules.is_empty() {
        eprintln!("Error: At least one port forwarding rule is required");
        eprintln!();
        eprintln!("Usage: {} [ARGS ...]", args[0]);
        eprintln!("See {} --help for more information", args[0]);
        std::process::exit(1);
    }

    // Check for duplicate local ports
    let mut seen_ports = std::collections::HashSet::new();
    for rule in &rules {
        if !seen_ports.insert(rule.local_port) {
            eprintln!("Error: Duplicate local port {}", rule.local_port);
            eprintln!("Each local port must be unique");
            std::process::exit(1);
        }
    }

    // Open output file if specified (fail-fast: test that we can write immediately)
    let output_writer: Box<dyn std::io::Write + Send> = if let Some(filepath) = output_file {
        use std::io::Write;

        // Create parent directories if they don't exist
        if let Some(parent) = std::path::Path::new(&filepath).parent() {
            if let Err(e) = std::fs::create_dir_all(parent) {
                eprintln!("Error: Cannot create parent directories for '{}': {}", filepath, e);
                std::process::exit(1);
            }
        }

        match std::fs::OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(&filepath)
        {
            Ok(mut file) => {
                // Test write immediately to fail fast
                if let Err(e) = file.write_all(b"") {
                    eprintln!("Error: Cannot write to output file '{}': {}", filepath, e);
                    std::process::exit(1);
                }
                if let Err(e) = file.flush() {
                    eprintln!("Error: Cannot flush output file '{}': {}", filepath, e);
                    std::process::exit(1);
                }
                Box::new(file)
            }
            Err(e) => {
                eprintln!("Error: Cannot open output file '{}': {}", filepath, e);
                std::process::exit(1);
            }
        }
    } else {
        Box::new(std::io::stdout())
    };

    // Initialize ConnID counter from last 5 base62 digits of Unix timestamp
    let now_secs = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    let conn_counter = Arc::new(AtomicU64::new(now_secs));

    // Create log writer channel (using std::sync::mpsc with buffer for blocking thread)
    // Use a large buffer to prevent blocking async tasks
    let (log_tx, log_rx) = std::sync::mpsc::sync_channel(10000);

    // Spawn log writer in a blocking thread
    let log_writer_handle = std::thread::spawn(|| log_writer_blocking(log_rx, output_writer));

    // Create shutdown flag
    let shutdown = Arc::new(AtomicBool::new(false));

    // Setup signal handler for graceful shutdown
    let shutdown_clone = Arc::clone(&shutdown);
    tokio::spawn(async move {
        #[cfg(unix)]
        {
            use tokio::signal::unix::{signal, SignalKind};
            let mut sigterm = signal(SignalKind::terminate()).unwrap();
            let mut sigint = signal(SignalKind::interrupt()).unwrap();

            tokio::select! {
                _ = sigterm.recv() => {},
                _ = sigint.recv() => {},
            }
        }

        #[cfg(windows)]
        {
            let mut ctrl_c = tokio::signal::windows::ctrl_c().unwrap();
            ctrl_c.recv().await;
        }

        shutdown_clone.store(true, Ordering::Relaxed);
    });

    // Spawn listener tasks for each forwarding rule
    let mut handles = Vec::new();
    for rule in rules {
        let conn_counter_clone = Arc::clone(&conn_counter);
        let log_tx_clone = log_tx.clone();
        let shutdown_clone = Arc::clone(&shutdown);

        let handle = tokio::spawn(run_listener(
            rule,
            conn_counter_clone,
            log_tx_clone,
            shutdown_clone,
        ));
        handles.push(handle);
    }

    // Wait for all listeners to finish
    for handle in handles {
        let _ = handle.await;
    }

    // Drop the log_tx sender to signal the log_writer to finish
    drop(log_tx);

    // Wait for the log_writer thread to finish processing all pending messages
    let _ = log_writer_handle.join();
}
