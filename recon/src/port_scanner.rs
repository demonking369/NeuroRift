use anyhow::Result;
use futures::future::join_all;
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::Duration;
use tokio::net::TcpStream;
use tokio::sync::Semaphore;
use tokio::time::timeout;

/// Async TCP port scanner with banner grabbing.
/// Returns JSON {host, ports: [{port, state, banner}]}
pub async fn run(target: &str, start: u16, end: u16, concurrency: usize, timeout_secs: u64) -> Result<Value> {
    let semaphore = Arc::new(Semaphore::new(concurrency));
    let target = Arc::new(target.to_string());

    let tasks: Vec<_> = (start..=end)
        .map(|port| {
            let target = target.clone();
            let sem = semaphore.clone();
            tokio::spawn(async move {
                let _permit = sem.acquire().await;
                let addr = format!("{}:{}", target, port);
                let parsed: SocketAddr = match addr.parse() {
                    Ok(a) => a,
                    Err(_) => return None,
                };

                let connect = timeout(
                    Duration::from_secs(timeout_secs),
                    TcpStream::connect(parsed),
                )
                .await;

                match connect {
                    Ok(Ok(mut stream)) => {
                        // Attempt banner grab
                        let mut banner = String::new();
                        let _ = timeout(Duration::from_millis(300), async {
                            use tokio::io::AsyncReadExt;
                            let mut buf = [0u8; 256];
                            if let Ok(n) = stream.read(&mut buf).await {
                                banner = String::from_utf8_lossy(&buf[..n]).trim().to_string();
                            }
                        })
                        .await;

                        Some(json!({
                            "port": port,
                            "state": "open",
                            "banner": banner
                        }))
                    }
                    _ => None,
                }
            })
        })
        .collect();

    let open_ports: Vec<Value> = join_all(tasks)
        .await
        .into_iter()
        .filter_map(|r| r.ok().flatten())
        .collect();

    Ok(json!({
        "mode": "port",
        "host": target.as_str(),
        "count": open_ports.len(),
        "ports": open_ports
    }))
}
