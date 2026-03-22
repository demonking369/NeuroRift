use anyhow::Result;
use futures::future::join_all;
use reqwest::Client;
use serde_json::{json, Value};
use std::fs;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Semaphore;

/// HTTP endpoint/directory fuzzer.
/// Sends GET requests for each wordlist entry, reports live paths (200/301/302/403).
pub async fn run(base_url: &str, wordlist_path: &str, concurrency: usize, timeout_secs: u64) -> Result<Value> {
    let base_url = base_url.trim_end_matches('/').to_string();

    let paths: Vec<String> = if wordlist_path.is_empty() {
        vec!["admin", "api", "login", "dashboard", "config", "health", "version",
             "backup", "debug", "test", "robots.txt", ".env", "sitemap.xml"]
            .into_iter().map(|s| s.to_string()).collect()
    } else {
        fs::read_to_string(wordlist_path)
            .unwrap_or_default()
            .lines()
            .filter(|l| !l.is_empty() && !l.starts_with('#'))
            .map(|l| l.trim().trim_start_matches('/').to_string())
            .collect()
    };

    let client = Arc::new(
        Client::builder()
            .timeout(Duration::from_secs(timeout_secs))
            .redirect(reqwest::redirect::Policy::none())
            .build()?
    );
    let semaphore = Arc::new(Semaphore::new(concurrency));

    let tasks: Vec<_> = paths
        .into_iter()
        .map(|path| {
            let url = format!("{}/{}", base_url, path);
            let client = client.clone();
            let sem = semaphore.clone();
            tokio::spawn(async move {
                let _permit = sem.acquire().await;
                match client.get(&url).send().await {
                    Ok(resp) => {
                        let status = resp.status().as_u16();
                        if matches!(status, 200 | 201 | 301 | 302 | 307 | 401 | 403 | 405) {
                            Some(json!({"url": url, "status": status}))
                        } else {
                            None
                        }
                    }
                    Err(_) => None,
                }
            })
        })
        .collect();

    let live_endpoints: Vec<Value> = join_all(tasks)
        .await
        .into_iter()
        .filter_map(|r| r.ok().flatten())
        .collect();

    Ok(json!({
        "mode": "fuzz",
        "target": base_url,
        "count": live_endpoints.len(),
        "endpoints": live_endpoints
    }))
}
