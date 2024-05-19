use std::sync::Arc;

use anyhow::anyhow;
use axum::extract::Query;
use rdkafka::ClientConfig;
use rdkafka::error::KafkaError;
use rdkafka::producer::{FutureProducer, FutureRecord};
use scylla::Session;
use thiserror::Error;
use tokio::time::Duration;

use crate::db::insert_into_prices;
use crate::models::PriceStamp;
use crate::routes::price::{price_of_token, QueryPrice};

pub static TOKEN_LIST: [&str; 6] = ["HNT", "SOL", "soLINK", "TBTC", "Bonk", "W"];
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

pub async fn stream_prices(kafka_node: String) -> Result<()> {
    let producer: FutureProducer = ClientConfig::new()
        .set("bootstrap.servers", kafka_node)
        .set("message.timeout.ms", "50000")
        .create()?;

    loop {
        for token in TOKEN_LIST {
            let price = price_of_token(Query(QueryPrice {
                id: token.to_owned(),
                vs_token: VS_TOKEN.to_owned(),
            }))
            .await?.0;

            let message = serde_json::to_string(&price)?;

            let record = FutureRecord::to("prices")
                .payload(&message)
                .key("");

            // sending to kafka
            producer
                .send(record, Duration::from_secs(0))
                .await
                .map_err(|e| anyhow!(e.0.to_string() + &format!("({:?})", e.0)))?;
        }
    }
}

pub async fn populate_prices(session: Arc<Session>) -> Result<()> {
    let mut interval = tokio::time::interval(Duration::from_secs(1));
    loop {
        interval.tick().await;

        for token in TOKEN_LIST {
            let price = price_of_token(Query(QueryPrice {
                id: token.to_owned(),
                vs_token: VS_TOKEN.to_owned(),
            }))
            .await?;

            insert_into_prices(
                session.clone(),
                PriceStamp {
                    token_: token.to_owned(),
                    datetime: price.0.datetime,
                    value: price.0.value,
                },
            )
            .await?;
        }
    }
}
