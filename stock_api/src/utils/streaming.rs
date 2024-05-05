use std::sync::Arc;

use anyhow::anyhow;
use axum::extract::Query;
use rdkafka::error::KafkaError;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::ClientConfig;
use scylla::Session;
use serde_json::to_string;
use thiserror::Error;
use tokio::time::{Duration, Instant};

use crate::db::insert_into_prices;
use crate::models::PriceStamp;
use crate::routes::price::{price_of_token, QueryPrice};

pub static TOKEN_LIST: [&str; 6] = ["HNT", "SOL", "soLINK", "tBTC", "Bonk", "W"];
pub static VS_TOKEN: &str = "USDT";

#[derive(Debug, Error)]
pub enum Error {
    #[error(transparent)]
    DB {
        #[from]
        source: crate::db::Error,
    },
    #[error(transparent)]
    Price {
        #[from]
        source: crate::routes::price::Error,
    },
    #[error("kafka connection error: {}", source)]
    UnableToCreateKafkaProducer {
        #[from]
        source: KafkaError,
    },
    #[error("kafka limit error: {}", source)]
    UnableToSendToKafka {
        #[from]
        source: anyhow::Error,
    },
    #[error("serde error: {}", source)]
    Serde {
        #[from]
        source: serde_json::error::Error,
    },
}

pub type Result<T> = std::result::Result<T, Error>;

pub async fn populate_prices(session: Arc<Session>, kafka_node: String) -> Result<()> {
    let producer: FutureProducer = ClientConfig::new()
        .set("bootstrap.servers", kafka_node)
        .set("message.timeout.ms", "50000")
        .create()?;

    let counter = 0_usize;

    println!("Sending messages...");

    let mut last_db_update = Instant::now();

    loop {
        for (idx, &token) in TOKEN_LIST.iter().enumerate() {
            let price = price_of_token(Query(QueryPrice {
                id: token.to_owned(),
                vs_token: VS_TOKEN.to_owned(),
            }))
            .await?;

            let message = to_string(&price.0)?;

            let key = counter.to_string();

            let record = FutureRecord::to("prices")
                .payload(&message)
                .key(&key)
                .partition(idx as i32);

            // sending to kafka
            producer
                .send(record, std::time::Duration::from_secs(0))
                .await
                .map_err(|e| anyhow!(e.0.to_string() + &format!("({:?})", e.0)))?;

            // storing to historical DB
            // Check if a second has passed to update the database
            if last_db_update.elapsed() >= Duration::from_secs(1) {
                for &token in TOKEN_LIST.iter() {
                    let price = price_of_token(Query(QueryPrice {
                        id: token.to_owned(),
                        vs_token: VS_TOKEN.to_owned(),
                    }))
                    .await?;

                    insert_into_prices(
                        session.clone(),
                        PriceStamp {
                            token: token.to_owned(),
                            datetime: price.0.datetime,
                            value: price.0.value,
                        },
                    )
                    .await?;
                }
                // Reset the timer
                last_db_update = Instant::now();
            }

            // Yield to the scheduler to prevent hogging the CPU
            tokio::task::yield_now().await;
        }
    }
}
