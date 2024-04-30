use std::collections::HashMap;

use anyhow::anyhow;
use axum::{debug_handler, Json};
use axum::extract::{Query, State};
use axum::response::{IntoResponse, Response};
use serde::{Deserialize, Serialize};

use crate::args::ServerState;

use super::{Error, Result};

/// A struct to represent query parameters for getting price.
#[derive(Deserialize)]
pub struct QueryPrice {
    /// The token we want to get the price of.
    pub id: String,
    #[serde(rename = "vsToken")]
    /// The token to compare price with.
    pub vs_token: String,
}

/// A struct to represent a response from price API.
#[derive(Serialize, Deserialize, Debug)]
pub struct PriceStamp {
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

impl IntoResponse for PriceStamp {
    fn into_response(self) -> Response {
        let json_body = Json(self);
        json_body.into_response()
    }
}

#[derive(Debug, Serialize)]
pub struct Price(f64);

#[debug_handler]
pub async fn price_of_token(
    State(server_config): State<ServerState>,
    params: Query<QueryPrice>,
) -> Result<Json<Price>> {
    let QueryPrice { id, vs_token } = params.0;

    // Searches for the token in the cache.
    // If cache search hits, returns the value from there.
    // Otherwise, making an API request and caching it.
    match server_config
        .cache
        .get(&(id.clone(), vs_token.clone()))
        .await
    {
        Some(val) => Ok(Json(Price(val))),
        None => {
            let uri = format!(
                "https://price.jup.ag/v4/price?ids={}&vsToken={}",
                id.clone(),
                vs_token.clone()
            );

            let response = reqwest::get(uri)
                .await
                .map_err(|e| Error::CannotGetPriceResponse { source: e })?
                .json::<PriceStamp>()
                .await
                .map_err(|e| Error::CannotCreatePriceStampJson { source: anyhow!(e) })?
                .data;

            let val = response.get(&id).ok_or(Error::NoSuchToken {
                token: vs_token.clone(),
            })?;
            server_config.cache.insert((id, vs_token), val.price).await;

            Ok(Json(Price(val.price)))
        }
    }
}
