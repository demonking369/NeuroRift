use anyhow::Result;
use reqwest::Client;
use serde_json::{json, Value};
use std::time::Duration;

/// HTTP/S prober — probes a URL, extracts status, headers, and tech fingerprint.
pub async fn run(target: &str, timeout_secs: u64) -> Result<Value> {
    // Normalize
    let url = if target.starts_with("http") {
        target.to_string()
    } else {
        format!("https://{}", target)
    };

    let client = Client::builder()
        .timeout(Duration::from_secs(timeout_secs))
        .danger_accept_invalid_certs(true)
        .redirect(reqwest::redirect::Policy::none())
        .build()?;

    let resp = client.get(&url).send().await?;

    let status = resp.status().as_u16();
    let headers = resp.headers().clone();

    // Tech fingerprinting based on response headers
    let mut tech: Vec<String> = vec![];
    let header_map = [
        ("server", "Server"),
        ("x-powered-by", "X-Powered-By"),
        ("x-framework", "X-Framework"),
        ("x-generator", "X-Generator"),
        ("via", "Via"),
    ];
    for (key, label) in &header_map {
        if let Some(val) = headers.get(*key) {
            let s = val.to_str().unwrap_or("").to_string();
            if !s.is_empty() {
                tech.push(format!("{}: {}", label, s));
            }
        }
    }

    // CDN / WAF detection
    if headers.get("cf-ray").is_some() {
        tech.push("CDN: Cloudflare".into());
    }
    if headers.get("x-akamai-transformed").is_some() {
        tech.push("CDN: Akamai".into());
    }

    let headers_json: serde_json::Map<String, Value> = headers
        .iter()
        .map(|(k, v)| (k.to_string(), json!(v.to_str().unwrap_or(""))))
        .collect();

    Ok(json!({
        "mode": "probe",
        "url": url,
        "status": status,
        "tech": tech,
        "headers": headers_json
    }))
}
