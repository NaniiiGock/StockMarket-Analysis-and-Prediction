use std::sync::Arc;

use anyhow::anyhow;
use axum::extract::Query;
use rdkafka::ClientConfig;
use rdkafka::error::KafkaError;
use rdkafka::producer::{FutureProducer, FutureRecord};
use scylla::Session;
use serde_json::to_string;
use thiserror::Error;

use crate::db::{insert_into_prices, TOKEN_LIST, VS_TOKEN};
use crate::models::PriceStamp;
use crate::routes::price::{price_of_token, QueryPrice};

#[derive(Debug, Error)]
pub enum Error {
    #[error(transparent)]
    DB{
        #[from]
        source: crate::db::Error,
    },
    #[error(transparent)]
    Price{
        #[from]
        source: crate::routes::price::Error,
    },
    #[error("kafka connection error: {}", source)]
    UnableToCreateKafkaProducer{
        #[from]
        source: KafkaError,
    },
    #[error("kafka limit error: {}", source)]
    UnableToSendToKafka{
        #[from]
        source: anyhow::Error,
    },
    #[error("serde error: {}", source)]
    Serde {
        #[from]
        source: serde_json::error::Error,
    }
}

pub type Result<T> = std::result::Result<T, Error>;

pub async fn populate_prices(session: Arc<Session>, kafka_node: String) -> Result<()> {
    
    let producer: FutureProducer = ClientConfig::new()
        .set("bootstrap.servers", kafka_node)
        .set("message.timeout.ms", "50000")
        .create()?;
    
    let counter = 0_usize;

    println!("Sending messages...");
    
    loop {
        for token in TOKEN_LIST {
            let price = price_of_token(Query(QueryPrice { id: token.to_owned(), vs_token: VS_TOKEN.to_owned() })).await?;
            
            let message = to_string(&price.0)?;

            let key = counter.to_string();
            
            let record = FutureRecord::to("payments").payload(&message).key(&key);

            // sending to kafka
            producer
                .send(record, std::time::Duration::from_secs(0))
                .await
                .map_err(|e| anyhow!(e.0.to_string() + &format!("({:?})", e.0)))?;
            
            // storing to historical DB
            insert_into_prices(session.clone(), PriceStamp {
                token: token.to_owned(),
                datetime: price.0.datetime,
                value: price.value,
            }).await?;
        }
    }
}