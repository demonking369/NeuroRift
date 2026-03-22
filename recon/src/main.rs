use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};
use serde_json;

mod dns_resolver;
mod endpoint_fuzzer;
mod http_prober;
mod port_scanner;
mod subdomain_enum;

/// NeuroRift v2 Recon Engine — high-speed async reconnaissance tool
#[derive(Parser, Debug)]
#[command(name = "recon", version = "0.1.0", author = "demonking369")]
struct Cli {
    /// Recon mode
    #[arg(long, value_enum)]
    mode: Mode,

    /// Target domain, IP, or URL
    #[arg(long)]
    target: String,

    /// Optional wordlist path (used by subdomain and fuzzer modes)
    #[arg(long, default_value = "")]
    wordlist: String,

    /// Max concurrent connections
    #[arg(long, default_value = "1000")]
    concurrency: usize,

    /// Timeout per operation in seconds
    #[arg(long, default_value = "5")]
    timeout: u64,

    /// Port range for port scanner (e.g. "1-1024")
    #[arg(long, default_value = "1-65535")]
    ports: String,
}

#[derive(ValueEnum, Clone, Debug)]
enum Mode {
    Subdomain,
    Port,
    Fuzz,
    Dns,
    Probe,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    let result = match cli.mode {
        Mode::Subdomain => {
            subdomain_enum::run(&cli.target, &cli.wordlist, cli.concurrency, cli.timeout).await?
        }
        Mode::Port => {
            let (start, end) = parse_port_range(&cli.ports)?;
            port_scanner::run(&cli.target, start, end, cli.concurrency, cli.timeout).await?
        }
        Mode::Fuzz => {
            endpoint_fuzzer::run(&cli.target, &cli.wordlist, cli.concurrency, cli.timeout).await?
        }
        Mode::Dns => dns_resolver::run(&cli.target).await?,
        Mode::Probe => http_prober::run(&cli.target, cli.timeout).await?,
    };

    // All output is JSON to stdout — errors/debug go to stderr
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

fn parse_port_range(range: &str) -> Result<(u16, u16)> {
    let parts: Vec<&str> = range.split('-').collect();
    if parts.len() == 2 {
        let start = parts[0].parse::<u16>().context("Invalid start port")?;
        let end = parts[1].parse::<u16>().context("Invalid end port")?;
        Ok((start, end))
    } else {
        let port = range.parse::<u16>().context("Invalid port")?;
        Ok((port, port))
    }
}
