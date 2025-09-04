use chrono::Utc;
use serde::Serialize;
use std::env;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::Mutex;

static CONNECTION_ID: AtomicU64 = AtomicU64::new(1);

#[derive(Serialize)]
#[serde(untagged)]
enum LogEntry {
    Connection {
        id: u64,
        stamp: String,
        #[serde(rename = "type")]
        event_type: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        client: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        target: Option<String>,
    },
    Data {
        id: u64,
        stamp: String,
        direction: String,
        data: String,
    },
}

fn get_timestamp() -> String {
    let now = Utc::now();
    now.format("%Y-%m-%d_%H:%M:%S%.6f").to_string()
}

fn escape_data(bytes: &[u8]) -> String {
    let mut result = String::new();
    for &byte in bytes {
        match byte {
            b'\r' => result.push_str("\\r"),
            b'\n' => result.push_str("\\n"),
            b'\t' => result.push_str("\\t"),
            b'\\' => result.push_str("\\\\"),
            b'"' => result.push_str("\\\""),
            0x20..=0x7E => result.push(byte as char),
            _ => result.push_str(&format!("\\u{:04x}", byte)),
        }
    }
    result
}

async fn handle_connection(
    inbound: TcpStream,
    target_host: String,
    target_port: u16,
    client_addr: SocketAddr,
    output_lock: Arc<Mutex<()>>,
) {
    let conn_id = CONNECTION_ID.fetch_add(1, Ordering::SeqCst);
    
    let log_client_open = LogEntry::Connection {
        id: conn_id,
        stamp: get_timestamp(),
        event_type: "local_open".to_string(),
        client: Some(client_addr.to_string()),
        target: None,
    };
    {
        let _guard = output_lock.lock().await;
        println!("{}", serde_json::to_string(&log_client_open).unwrap());
    }
    
    let target_addr = format!("{}:{}", target_host, target_port);
    let outbound = match TcpStream::connect(&target_addr).await {
        Ok(stream) => stream,
        Err(_) => {
            let log_close = LogEntry::Connection {
                id: conn_id,
                stamp: get_timestamp(),
                event_type: "local_close".to_string(),
                client: None,
                target: None,
            };
            {
                let _guard = output_lock.lock().await;
                println!("{}", serde_json::to_string(&log_close).unwrap());
            }
            return;
        }
    };
    
    let log_remote_open = LogEntry::Connection {
        id: conn_id,
        stamp: get_timestamp(),
        event_type: "remote_open".to_string(),
        client: None,
        target: Some(target_addr.clone()),
    };
    {
        let _guard = output_lock.lock().await;
        println!("{}", serde_json::to_string(&log_remote_open).unwrap());
    }
    
    let (inbound_read, inbound_write) = tokio::io::split(inbound);
    let (outbound_read, outbound_write) = tokio::io::split(outbound);
    
    let output_lock_clone1 = output_lock.clone();
    let client_to_server = tokio::spawn(async move {
        let mut buf = vec![0u8; 32768];
        let mut inbound_read = inbound_read;
        let mut outbound_write = outbound_write;
        loop {
            match inbound_read.read(&mut buf).await {
                Ok(0) => break,
                Ok(n) => {
                    let data = &buf[..n];
                    let log_data = LogEntry::Data {
                        id: conn_id,
                        stamp: get_timestamp(),
                        direction: ">".to_string(),
                        data: escape_data(data),
                    };
                    {
                        let _guard = output_lock_clone1.lock().await;
                        println!("{}", serde_json::to_string(&log_data).unwrap());
                    }
                    
                    if outbound_write.write_all(data).await.is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
    });
    
    let output_lock_clone2 = output_lock.clone();
    let server_to_client = tokio::spawn(async move {
        let mut buf = vec![0u8; 32768];
        let mut outbound_read = outbound_read;
        let mut inbound_write = inbound_write;
        loop {
            match outbound_read.read(&mut buf).await {
                Ok(0) => break,
                Ok(n) => {
                    let data = &buf[..n];
                    let log_data = LogEntry::Data {
                        id: conn_id,
                        stamp: get_timestamp(),
                        direction: "<".to_string(),
                        data: escape_data(data),
                    };
                    {
                        let _guard = output_lock_clone2.lock().await;
                        println!("{}", serde_json::to_string(&log_data).unwrap());
                    }
                    
                    if inbound_write.write_all(data).await.is_err() {
                        break;
                    }
                }
                Err(_) => break,
            }
        }
    });
    
    let _ = tokio::join!(client_to_server, server_to_client);
    
    // Always log both close events if they haven't been logged yet
    {
        let _guard = output_lock.lock().await;
        let log_remote = LogEntry::Connection {
            id: conn_id,
            stamp: get_timestamp(),
            event_type: "remote_close".to_string(),
            client: None,
            target: None,
        };
        println!("{}", serde_json::to_string(&log_remote).unwrap());
        
        let log_local = LogEntry::Connection {
            id: conn_id,
            stamp: get_timestamp(),
            event_type: "local_close".to_string(),
            client: None,
            target: None,
        };
        println!("{}", serde_json::to_string(&log_local).unwrap());
    }
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() != 4 {
        eprintln!("Usage: {} <local_port> <target_host> <target_port>", args[0]);
        std::process::exit(1);
    }
    
    let local_port: u16 = args[1].parse().expect("Invalid local port");
    let target_host = args[2].clone();
    let target_port: u16 = args[3].parse().expect("Invalid target port");
    
    let listener = TcpListener::bind(format!("0.0.0.0:{}", local_port))
        .await
        .expect("Failed to bind to local port");
    
    let output_lock = Arc::new(Mutex::new(()));
    
    loop {
        let (inbound, client_addr) = listener.accept().await.unwrap();
        let target_host_clone = target_host.clone();
        let output_lock_clone = output_lock.clone();
        
        tokio::spawn(handle_connection(
            inbound,
            target_host_clone,
            target_port,
            client_addr,
            output_lock_clone,
        ));
    }
}