use std::net::SocketAddr;
use std::sync::Arc;

use anyhow::anyhow;
use axum::Router;
use axum::routing::get;
use clap::Parser;
use thiserror::Error;
use tokio::net::TcpListener;
use tokio::signal;

use crate::args::{Args, ServerState};
use crate::db::create_session;
use crate::utils::streaming::{populate_prices, stream_prices};

pub mod args;
pub mod db;
pub mod models;
pub mod routes;
mod utils;

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

#[derive(Debug, Error)]
pub enum Error {
    #[error(transparent)]
    Error {
        #[from]
        source: anyhow::Error,
    },
}

pub type Result<T> = std::result::Result<T, Error>;

#[tokio::main]
async fn main() -> Result<()> {
    let Args {
        https_port,
        cassandra_node,
        kafka_node,
    } = Args::parse();

    let addr = SocketAddr::from(([0, 0, 0, 0], https_port));
    let session = Arc::new(
        create_session(&cassandra_node)
            .await
            .map_err(|e| anyhow!(e.to_string()))?,
    );

    let state = ServerState {
        session,
        kafka_node,
    };
    let clonned_state = state.clone();

    println!("Starting server at {}", addr);

    let listener = TcpListener::bind(addr).await.unwrap();

    tokio::spawn(async move {
        match stream_prices(state.kafka_node.clone()).await {
            Ok(_) => {}
            Err(e) => {
                println!("{e:?}")
            }
        }
    });
    
    tokio::spawn(async move {
        match populate_prices(state.session.clone()).await {
            Ok(_) => {}
            Err(e) => {
                println!("{e:?}")
            }
        }
    });

    let app = Router::new()
        .route("/", get(|| async { "Placeholder for main page" }))
        .route("/price", get(routes::price::price_of_token))
        .route("/tokens", get(routes::tokens::get_token_list))
        .route(
            "/price/interval",
            get(routes::price::price_of_token_interval),
        )
        .with_state(clonned_state);

    axum::serve(listener, app.into_make_service())
        .with_graceful_shutdown(graceful_shutdown())
        .await
        .map_err(|e| anyhow!(e.to_string()))?;

    Ok(())
}
