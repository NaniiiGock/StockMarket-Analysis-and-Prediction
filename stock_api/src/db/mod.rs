use std::sync::Arc;
use std::time::Duration;

use chrono::{DateTime, Utc};
use scylla::{Session, SessionBuilder};
use scylla::prepared_statement::PreparedStatement;
use scylla::transport::errors::{NewSessionError, QueryError};
use scylla::transport::query_result::RowsExpectedError;
use thiserror::Error;
use tokio::time::sleep;

use crate::models::PriceStamp;

#[derive(Debug, Error)]
pub enum Error {
    #[error("failed to prepare query: {}", source)]
    FailedToPrepareQuery {
        #[from]
        source: QueryError
    },
    #[error("failed to create new session: {}", source)]
    FailedToCreateSession {
        #[from]
        source: NewSessionError
    },
    #[error("failed to create a value from a row: {}", source)]
    UnableToCreateAValueFromRow {
        #[from]
        source: RowsExpectedError
    },
}

pub type Result<T> = std::result::Result<T, Error>;


pub async fn prepare_query(
    session: &Arc<Session>,
    query: &str,
) -> Result<PreparedStatement> {
    let prepared_statement = session.prepare(query).await?;
    Ok(prepared_statement)
}

pub async fn create_session(node: &str) -> Result<Session> {
    let mut attempt = 0;
    loop {
        match SessionBuilder::new()
            .known_node(node)
            .use_keyspace("prices", false)
            .build()
            .await
        {
            Ok(session) => return Ok(session),
            Err(e) => {
                attempt += 1;
                eprintln!(
                    "Failed to connect to Cassandra on attempt {}: {}",
                    attempt, e
                );
                sleep(Duration::from_secs(5)).await;
            }
        }
    }
}

pub async fn check_keyspace_exist(session: Arc<Session>, keyspace: &str) -> bool {
    let query = format!(
        "SELECT * FROM system_schema.keyspaces WHERE keyspace_name = '{}';",
        keyspace
    );

    match session.query(query, &[]).await {
        Ok(_) => true,
        Err(_) => {
            eprintln!("Failed to connect to keyspace: {}", keyspace);
            false
        }
    }
}


pub async fn insert_into_prices(
    session: Arc<Session>,
    pricestamp: PriceStamp,
) -> Result<()> {
    let query = r#"INSERT INTO prices.prices (token, datetime, value) VALUES (?, ?, ?)"#;

    let prepared_query = prepare_query(&session, query).await?;

    session.execute(&prepared_query, pricestamp).await?;

    Ok(())
}

pub async fn get_from_prices(
    session: Arc<Session>,
    token: String,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<PriceStamp>> {
    let query = "SELECT * FROM prices.prices WHERE token = ? AND datetime >= ? AND datetime <= ? ALLOW FILTERING;";

    let prepared_query = prepare_query(&session, query).await?;

    let prices = session.execute(&prepared_query, (token, start, end)).await?;

    let prices = prices.rows_typed::<PriceStamp>()?;

    Ok(prices.flatten().collect())
}

