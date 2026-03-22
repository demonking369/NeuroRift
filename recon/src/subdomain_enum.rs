use anyhow::Result;
use futures::future::join_all;
use hickory_resolver::{
    config::{ResolverConfig, ResolverOpts},
    TokioAsyncResolver,
};
use serde_json::{json, Value};
use std::fs;
use std::sync::Arc;
use tokio::sync::Semaphore;

/// Async DNS brute-force subdomain enumeration.
/// Resolves each wordlist entry as a potential subdomain of target.
/// Returns JSON array of live subdomains.
pub async fn run(target: &str, wordlist_path: &str, concurrency: usize, _timeout: u64) -> Result<Value> {
    let resolver = TokioAsyncResolver::tokio(
        ResolverConfig::cloudflare(),
        ResolverOpts::default(),
    );

    let words: Vec<String> = if wordlist_path.is_empty() {
        // Built-in minimal wordlist for testing without external file
        vec!["www", "api", "dev", "staging", "admin", "mail", "vpn", "cdn", "assets", "app"]
            .into_iter().map(|s| s.to_string()).collect()
    } else {
        fs::read_to_string(wordlist_path)
            .unwrap_or_default()
            .lines()
            .filter(|l| !l.is_empty() && !l.starts_with('#'))
            .map(|l| l.trim().to_string())
            .collect()
    };

    let semaphore = Arc::new(Semaphore::new(concurrency));
    let resolver = Arc::new(resolver);

    let tasks: Vec<_> = words
        .into_iter()
        .map(|word| {
            let fqdn = format!("{}.{}", word, target);
            let resolver = resolver.clone();
            let sem = semaphore.clone();
            tokio::spawn(async move {
                let _permit = sem.acquire().await;
                match resolver.lookup_ip(fqdn.as_str()).await {
                    Ok(response) => {
                        let ips: Vec<String> = response.iter().map(|ip| ip.to_string()).collect();
                        if !ips.is_empty() {
                            Some(json!({"subdomain": fqdn, "ips": ips}))
                        } else {
                            None
                        }
                    }
                    Err(_) => None,
                }
            })
        })
        .collect();

    let results: Vec<Value> = join_all(tasks)
        .await
        .into_iter()
        .filter_map(|r| r.ok().flatten())
        .collect();

    Ok(json!({
        "mode": "subdomain",
        "target": target,
        "count": results.len(),
        "subdomains": results
    }))
}
