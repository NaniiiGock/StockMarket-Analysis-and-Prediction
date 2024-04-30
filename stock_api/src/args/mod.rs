use std::time::Duration;

use clap::Parser;

#[derive(Parser, Clone)]
pub struct Args {
    /// A port to run the server at
    #[arg(long, default_value_t = 3000)]
    pub https_port: u16,

    /// Cache timeout in milliseconds.
    #[arg(long, default_value = "5000", value_parser = parse_duration)]
    pub cache_timeout: Duration,

    /// Cache capacity in bytes.
    #[arg(long, default_value_t = 10_000_000)]
    pub cache_capacity: u64,
}


/// A helper function for parsing duration.
fn parse_duration(arg: &str) -> Result<Duration, std::num::ParseIntError> {
    let seconds = arg.parse()?;
    Ok(Duration::from_millis(seconds))
}

/// A state of the server to pass to handlers.
#[derive(Clone)]
pub struct ServerState {
    pub cache: moka::future::Cache<(String, String), f64>,
}
