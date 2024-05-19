use std::collections::HashMap;

use anyhow::anyhow;
use axum::extract::{Query, State};
use axum::http::StatusCode;
use axum::Json;
use axum::response::{IntoResponse, Response};
use chrono::{DateTime, Utc};
use serde::Deserialize;
use serde::Serialize;
use thiserror::Error;

use crate::args::ServerState;
use crate::db::get_from_prices;
use crate::models::PriceStamp;

/// A struct to represent query parameters for getting price.
#[derive(Deserialize)]
pub struct QueryPrice {
    /// The token we want to get the price of.
    pub id: String,
    #[serde(rename = "vsToken")]
    /// The token to compare price with.
    pub vs_token: String,
}

#[derive(Deserialize)]
pub struct QueryPriceInterval {
    /// The token we want to get the price of.
    pub id: String,
    #[serde(rename = "vsToken")]
    /// The token to compare price with.
    pub vs_token: String,
    pub start_time: DateTime<Utc>,
    pub end_time: DateTime<Utc>,
}

/// A struct to represent a response from price API.
#[derive(Serialize, Deserialize, Debug)]
pub struct PriceResponse {
    pub data: HashMap<String, PriceStampData>,
    #[serde(rename = "timeTaken")]
    pub time_taken: f64,
}

/// A struct to represent single token info from price API.
#[derive(Serialize, Deserialize, Debug)]
pub struct PriceStampData {
    pub id: String,
    #[serde(rename = "mintSymbol")]
    pub mint_symbol: String,
    #[serde(rename = "vsToken")]
    pub vs_token: String,
    #[serde(rename = "vsTokenSymbol")]
    pub vs_token_symbol: String,
    pub price: f64,
}

impl IntoResponse for PriceResponse {
    fn into_response(self) -> Response {
        let json_body = Json(self);
        json_body.into_response()
    }
}

#[derive(Debug, Serialize)]
pub struct Price {
    pub value: f64,
    pub datetime: DateTime<Utc>,
    pub token: String,
}

impl Price {
    pub fn new(value: f64, token: String) -> Price {
        Price {
            value,
            datetime: chrono::offset::Utc::now(),
            token
        }
    }
}

pub async fn price_of_token(
    params: Query<QueryPrice>,
) -> Result<Json<Price>> {
    let QueryPrice { id, vs_token } = params.0;
    
    let uri = format!(
        "https://price.jup.ag/v4/price?ids={}&vsToken={}",
        id.clone(),
        vs_token.clone()
    );

    let response = reqwest::get(uri)
        .await
        .map_err(|e| Error::CannotGetPriceResponse { source: e })?
        .json::<PriceResponse>()
        .await
        .map_err(|e| Error::CannotCreatePriceStampJson { source: anyhow!(e) })?
        .data;

    let val = response.get(&id).ok_or(Error::NoSuchToken {
        token: vs_token.clone(),
    })?;

    Ok(Json(Price::new(val.price, id)))
}

pub async fn price_of_token_interval(
    state: State<ServerState>,
    params: Query<QueryPriceInterval>,
) -> Result<Json<Vec<PriceStamp>>> {
    let result = get_from_prices(state.session.clone(), params.id.clone(), params.start_time, params.end_time).await?;
    Ok(Json(result))
}

#[derive(Debug, Error)]
pub enum Error {
    #[error("cannot deserialize json for PriceStamp: {source}")]
    CannotCreatePriceStampJson { source: anyhow::Error },
    #[error("cannot get response from Jupiter API /price route: {:?}", source)]
    CannotGetPriceResponse { source: reqwest::Error },
    #[error("no such token in response: {token}")]
    NoSuchToken { token: String },
    #[error(transparent)]
    DBError {
        #[from]
        source: crate::db::Error,
    }
}

pub type Result<T> = std::result::Result<T, Error>;

impl Serialize for Error {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
        where
            S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let body = self.to_string();
        (StatusCode::INTERNAL_SERVER_ERROR, body).into_response()
    }
}
