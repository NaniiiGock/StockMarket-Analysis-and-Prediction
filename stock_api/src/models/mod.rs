use chrono::{DateTime, Utc};
use scylla::{FromRow, FromUserType, SerializeCql, SerializeRow};
use serde::Serialize;

#[derive(Serialize, FromRow, FromUserType, SerializeCql, SerializeRow, Debug)]
pub struct PriceStamp {
    pub token_: String,
    pub datetime: DateTime<Utc>,
    pub value: f64,
}