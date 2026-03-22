use anyhow::Result;
use hickory_resolver::{
    config::{ResolverConfig, ResolverOpts},
    TokioAsyncResolver,
};
use serde_json::{json, Value};

/// Bulk DNS resolver — resolves A, AAAA, CNAME, MX, TXT, NS records for a domain.
pub async fn run(target: &str) -> Result<Value> {
    let resolver = TokioAsyncResolver::tokio(
        ResolverConfig::cloudflare(),
        ResolverOpts::default(),
    );

    let mut records: serde_json::Map<String, Value> = serde_json::Map::new();

    // A records
    if let Ok(resp) = resolver.lookup_ip(target).await {
        let ips: Vec<String> = resp.iter().map(|ip| ip.to_string()).collect();
        records.insert("A".into(), json!(ips));
    }

    // CNAME
    if let Ok(resp) = resolver.lookup(target, hickory_resolver::proto::rr::RecordType::CNAME).await {
        let cnames: Vec<String> = resp.record_iter()
            .filter_map(|r| r.data().map(|d| d.to_string()))
            .collect();
        if !cnames.is_empty() {
            records.insert("CNAME".into(), json!(cnames));
        }
    }

    // MX
    if let Ok(resp) = resolver.mx_lookup(target).await {
        let mx: Vec<Value> = resp.iter()
            .map(|r| json!({"priority": r.preference(), "exchange": r.exchange().to_string()}))
            .collect();
        records.insert("MX".into(), json!(mx));
    }

    // TXT
    if let Ok(resp) = resolver.txt_lookup(target).await {
        let txt: Vec<String> = resp.iter().map(|r| r.to_string()).collect();
        records.insert("TXT".into(), json!(txt));
    }

    // NS
    if let Ok(resp) = resolver.ns_lookup(target).await {
        let ns: Vec<String> = resp.iter().map(|r| r.to_string()).collect();
        records.insert("NS".into(), json!(ns));
    }

    Ok(json!({
        "mode": "dns",
        "target": target,
        "records": records
    }))
}
