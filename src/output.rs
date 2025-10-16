use chrono::Utc;
use serde_json::json;
use std::fs::OpenOptions;
use std::io::{self, Write};
use std::net::SocketAddr;
use std::path::PathBuf;
use std::time::Duration;
use tokio::time;

use crate::encoding::encode_data;

pub struct OutputWriter {
    mode: OutputMode,
    input_buffer: Vec<String>,
    output_buffer: Vec<String>,
    last_swap: time::Instant,
    flush_interval: Duration,
}

enum OutputMode {
    Stdout,
    File(PathBuf),
}

impl OutputWriter {
    pub async fn new(output_file: Option<PathBuf>, flush_interval_ms: u64) -> Result<Self, String> {
        let mode = if let Some(path) = output_file {
            // Validate file can be created/written
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent).map_err(|e| {
                    format!("Cannot create output directory: {}", e)
                })?;
            }

            // Test file write
            OpenOptions::new()
                .create(true)
                .append(true)
                .open(&path)
                .map_err(|e| format!("Cannot open output file: {}", e))?;

            OutputMode::File(path)
        } else {
            OutputMode::Stdout
        };

        let flush_interval = Duration::from_millis(flush_interval_ms);

        Ok(OutputWriter {
            mode,
            input_buffer: Vec::new(),
            output_buffer: Vec::new(),
            last_swap: time::Instant::now(),
            flush_interval,
        })
    }

    /// Add a line to the input buffer
    fn add_line(&mut self, line: String) {
        self.input_buffer.push(line);
    }

    /// Swap buffers if flush interval has elapsed and there's data to flush
    async fn maybe_swap(&mut self) {
        if self.last_swap.elapsed() >= self.flush_interval {
            // Only swap if there's actually data to flush
            if !self.input_buffer.is_empty() {
                std::mem::swap(&mut self.input_buffer, &mut self.output_buffer);
                self.last_swap = time::Instant::now();

                // Flush output buffer
                self.flush_output_buffer().await;
            }
        }
    }

    /// Flush the output buffer to stdout or file
    async fn flush_output_buffer(&mut self) {
        if self.output_buffer.is_empty() {
            return;
        }

        let content = self.output_buffer.join("\n") + "\n";
        self.output_buffer.clear();

        match &self.mode {
            OutputMode::Stdout => {
                let _ = io::stdout().write_all(content.as_bytes());
                let _ = io::stdout().flush();
            }
            OutputMode::File(path) => {
                if let Ok(mut file) = OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(path)
                {
                    let _ = file.write_all(content.as_bytes());
                    let _ = file.flush();
                }
            }
        }
    }

    /// Force flush all buffers (both input and output) - used during shutdown
    pub async fn flush_all(&mut self) {
        // First, swap to move input buffer to output buffer
        std::mem::swap(&mut self.input_buffer, &mut self.output_buffer);

        // Flush what we just swapped
        self.flush_output_buffer().await;

        // Now flush any remaining data in the new output buffer (old input)
        if !self.input_buffer.is_empty() {
            std::mem::swap(&mut self.input_buffer, &mut self.output_buffer);
            self.flush_output_buffer().await;
        }
    }

    /// Periodic flush check - called by background task
    pub async fn periodic_flush(&mut self) {
        self.maybe_swap().await;
    }

    pub async fn log_event(
        &mut self,
        connid: &str,
        event: &str,
        from: &SocketAddr,
        to: &SocketAddr,
    ) {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S%.6fZ").to_string();

        let entry = json!({
            "time": timestamp,
            "ConnID": connid,
            "event": event,
            "from": format_addr(from),
            "to": format_addr(to),
        });

        self.add_line(entry.to_string());
        self.maybe_swap().await;
    }

    pub async fn log_data(
        &mut self,
        connid: &str,
        data: &[u8],
        from: &SocketAddr,
        to: &SocketAddr,
    ) {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S%.6fZ").to_string();
        let encoded_data = encode_data(data);

        let entry = json!({
            "time": timestamp,
            "ConnID": connid,
            "data": encoded_data,
            "from": format_addr(from),
            "to": format_addr(to),
        });

        self.add_line(entry.to_string());
        self.maybe_swap().await;
    }
}

fn format_addr(addr: &SocketAddr) -> String {
    match addr {
        SocketAddr::V4(v4) => format!("{}:{}", v4.ip(), v4.port()),
        SocketAddr::V6(v6) => format!("[{}]:{}", v6.ip(), v6.port()),
    }
}
