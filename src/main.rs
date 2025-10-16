use std::env;
use std::path::PathBuf;
use std::process;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::Mutex;

mod output;
mod encoding;
mod connid;

use output::OutputWriter;
use connid::ConnIdGenerator;

const BUFFER_SIZE: usize = 32768; // 32KB chunks

#[derive(Debug, Clone)]
struct ForwardRule {
    local_port: u16,
    target_host: String,
    target_port: u16,
}

impl ForwardRule {
    fn parse(arg: &str) -> Result<Self, String> {
        let parts: Vec<&str> = arg.split(':').collect();
        if parts.len() != 3 {
            return Err(format!("Invalid port forwarding rule: {}", arg));
        }

        let local_port = parts[0]
            .parse::<u16>()
            .map_err(|_| format!("Invalid local port: {}", parts[0]))?;

        if local_port == 0 {
            return Err("Local port must be between 1-65535".to_string());
        }

        let target_host = parts[1].to_string();
        if target_host.is_empty() {
            return Err("Target host cannot be empty".to_string());
        }

        let target_port = parts[2]
            .parse::<u16>()
            .map_err(|_| format!("Invalid target port: {}", parts[2]))?;

        if target_port == 0 {
            return Err("Target port must be between 1-65535".to_string());
        }

        Ok(ForwardRule {
            local_port,
            target_host,
            target_port,
        })
    }
}

#[derive(Debug)]
struct Config {
    rules: Vec<ForwardRule>,
    output_file: Option<PathBuf>,
    flush_interval_ms: u64,
}

impl Config {
    fn from_args() -> Result<Self, String> {
        let args: Vec<String> = env::args().skip(1).collect();

        if args.is_empty() {
            return Err("No arguments provided".to_string());
        }

        let mut rules = Vec::new();
        let mut output_file = None;
        let mut flush_interval_ms = 2000; // Default: 2 seconds per SPECIFICATION.md
        let mut seen_ports = std::collections::HashSet::new();

        for arg in args {
            if arg.starts_with("--flush-interval-ms=") {
                let value_str = &arg["--flush-interval-ms=".len()..];
                flush_interval_ms = value_str.parse::<u64>()
                    .map_err(|_| format!("Invalid flush interval: {}", value_str))?;
            } else if arg.starts_with('@') {
                output_file = Some(PathBuf::from(&arg[1..]));
            } else {
                let rule = ForwardRule::parse(&arg)?;
                if !seen_ports.insert(rule.local_port) {
                    return Err(format!("Duplicate local port: {}", rule.local_port));
                }
                rules.push(rule);
            }
        }

        if rules.is_empty() {
            return Err("No port forwarding rules specified".to_string());
        }

        Ok(Config { rules, output_file, flush_interval_ms })
    }
}

fn print_usage() {
    eprintln!("Usage: rawprox [ARGS ...]");
    eprintln!();
    eprintln!("Arguments:");
    eprintln!("  LOCAL_PORT:TARGET_HOST:TARGET_PORT  Port forwarding rule (required, at least one)");
    eprintln!("  @FILEPATH                           Output file (optional, defaults to stdout)");
    eprintln!("  --flush-interval-ms=MILLISECONDS    Buffer flush interval (optional, defaults to 2000)");
    eprintln!();
    eprintln!("Examples:");
    eprintln!("  rawprox 8080:example.com:80");
    eprintln!("  rawprox 3306:db.example.com:3306 @traffic.ndjson");
    eprintln!("  rawprox 8080:api.example.com:80 3306:db.example.com:3306");
    eprintln!("  rawprox 8080:example.com:80 --flush-interval-ms=100 @output.ndjson");
}

async fn handle_connection(
    mut client: TcpStream,
    rule: ForwardRule,
    connid_gen: Arc<ConnIdGenerator>,
    output: Arc<Mutex<OutputWriter>>,
) {
    let client_addr = match client.peer_addr() {
        Ok(addr) => addr,
        Err(_) => return,
    };

    // Connect to target
    let target_addr = format!("{}:{}", rule.target_host, rule.target_port);
    let mut server = match TcpStream::connect(&target_addr).await {
        Ok(s) => s,
        Err(_) => return, // Failed connection, no log entries
    };

    let server_addr = match server.peer_addr() {
        Ok(addr) => addr,
        Err(_) => return,
    };

    // Generate connection ID
    let connid = connid_gen.next();

    // Log open event
    {
        let mut out = output.lock().await;
        out.log_event(&connid, "open", &client_addr, &server_addr).await;
    }

    // Split connections for bidirectional forwarding
    let (mut client_read, mut client_write) = client.into_split();
    let (mut server_read, mut server_write) = server.into_split();

    let output_c2s = output.clone();
    let output_s2c = output.clone();
    let connid_c2s = connid.clone();
    let connid_s2c = connid.clone();

    // Client to server task
    let c2s = tokio::spawn(async move {
        let mut buffer = vec![0u8; BUFFER_SIZE];
        loop {
            match client_read.read(&mut buffer).await {
                Ok(0) => {
                    // Client closed
                    let mut out = output_c2s.lock().await;
                    out.log_event(&connid_c2s, "close", &client_addr, &server_addr).await;
                    break;
                }
                Ok(n) => {
                    let data = &buffer[..n];

                    // Log data
                    {
                        let mut out = output_c2s.lock().await;
                        out.log_data(&connid_c2s, data, &client_addr, &server_addr).await;
                    }

                    // Forward to server
                    if server_write.write_all(data).await.is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
    });

    // Server to client task
    let s2c = tokio::spawn(async move {
        let mut buffer = vec![0u8; BUFFER_SIZE];
        loop {
            match server_read.read(&mut buffer).await {
                Ok(0) => {
                    // Server closed
                    let mut out = output_s2c.lock().await;
                    out.log_event(&connid_s2c, "close", &server_addr, &client_addr).await;
                    break;
                }
                Ok(n) => {
                    let data = &buffer[..n];

                    // Log data
                    {
                        let mut out = output_s2c.lock().await;
                        out.log_data(&connid_s2c, data, &server_addr, &client_addr).await;
                    }

                    // Forward to client
                    if client_write.write_all(data).await.is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
    });

    // Wait for both directions to complete
    let _ = tokio::join!(c2s, s2c);
}

async fn run_listener(
    rule: ForwardRule,
    connid_gen: Arc<ConnIdGenerator>,
    output: Arc<Mutex<OutputWriter>>,
) -> Result<(), String> {
    let bind_addr = format!("0.0.0.0:{}", rule.local_port);
    let listener = TcpListener::bind(&bind_addr).await.map_err(|e| {
        if e.kind() == std::io::ErrorKind::AddrInUse {
            format!("Error: Port {} is already in use", rule.local_port)
        } else {
            format!("Error binding to port {}: {}", rule.local_port, e)
        }
    })?;

    loop {
        match listener.accept().await {
            Ok((client, _)) => {
                let rule_clone = rule.clone();
                let connid_gen_clone = connid_gen.clone();
                let output_clone = output.clone();

                tokio::spawn(async move {
                    handle_connection(client, rule_clone, connid_gen_clone, output_clone).await;
                });
            }
            Err(e) => {
                eprintln!("Accept error: {}", e);
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let config = match Config::from_args() {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Error: {}", e);
            eprintln!();
            print_usage();
            process::exit(1);
        }
    };

    // Initialize output writer
    let output = match OutputWriter::new(config.output_file, config.flush_interval_ms).await {
        Ok(o) => Arc::new(Mutex::new(o)),
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    };

    let connid_gen = Arc::new(ConnIdGenerator::new());

    // Set up signal handler for graceful shutdown
    let output_for_signal = output.clone();
    tokio::spawn(async move {
        match tokio::signal::ctrl_c().await {
            Ok(()) => {
                // Flush all buffers before exit
                let mut out = output_for_signal.lock().await;
                out.flush_all().await;
                process::exit(0);
            }
            Err(err) => {
                eprintln!("Unable to listen for shutdown signal: {}", err);
            }
        }
    });

    // Periodic flush task - triggers swaps even without new log entries
    let output_for_flush = output.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
            let mut out = output_for_flush.lock().await;
            out.periodic_flush().await;
        }
    });

    // Spawn listeners
    let mut tasks = Vec::new();
    for rule in config.rules {
        let connid_gen_clone = connid_gen.clone();
        let output_clone = output.clone();

        let task = tokio::spawn(async move {
            if let Err(e) = run_listener(rule, connid_gen_clone, output_clone).await {
                eprintln!("{}", e);
                process::exit(1);
            }
        });

        tasks.push(task);
    }

    // Wait for all listeners (they run forever)
    for task in tasks {
        let _ = task.await;
    }
}
