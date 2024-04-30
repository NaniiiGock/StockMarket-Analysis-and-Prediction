use std::net::SocketAddr;
use std::time::Duration;
use axum::Router;
use axum::routing::get;

use clap::Parser;
use moka::future::Cache;
use tokio::net::TcpListener;
use tokio::signal;

use crate::args::{Args, ServerState};

pub mod args;
pub mod db;
pub mod models;
pub mod routes;

/// This function is used for graceful shutdown.
/// Probably should be replaced with something more robust.
/// It was decided to panic in case we were unable to install a signal handler
pub async fn graceful_shutdown() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
        let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
        let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
}

/// A helper function to build cache for the server.
pub fn build_token_price_cache(
    max_capacity: u64,
    timeout: Duration,
) -> Cache<(String, String), f64> {
    Cache::builder()
        .max_capacity(max_capacity)
        .time_to_live(timeout)
        .build()
}


#[tokio::main]
async fn main() {
    let Args {
        https_port,
        cache_timeout,
        cache_capacity,
    } = Args::parse();

    let cache = build_token_price_cache(cache_capacity, cache_timeout);
    
    let addr = SocketAddr::from(([0, 0, 0, 0], https_port));

    println!("Starting server at {}", addr);
    
    
    let listener = TcpListener::bind(addr)
        .await
        .unwrap();

    let server_state = ServerState { cache };

    let app = Router::new()
        .route("/", get(|| async {"Placeholder for main page"}))
        .route("/price", get(routes::price::price_of_token))
        .with_state(server_state);

    
    axum::serve(listener, app.into_make_service())
        .with_graceful_shutdown(graceful_shutdown())
        .await
        .unwrap();
}
