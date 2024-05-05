#![allow(unused)]

use serde::Deserialize;
use std::collections::HashMap;
use axum::{debug_handler, Json};

pub mod error {
    use axum::http::StatusCode;
    use axum::response::{IntoResponse, Response};
    use serde::{Serialize, Serializer};
    use thiserror::Error;

    #[derive(Debug, Error)]
    pub enum Error {
        #[error("Bad response from token list API, {}", source)]
        UnableToGetTokenList {
            #[from]
            source: reqwest::Error,
        },
    }

    impl Serialize for Error {
        fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error> where S: Serializer {
            serializer.serialize_str(&self.to_string())
        }
    }
    
    impl IntoResponse for Error {
        fn into_response(self) -> Response {
            let body = self.to_string();
            (StatusCode::INTERNAL_SERVER_ERROR, body).into_response() 
        }
    }
    
}
pub mod result {
    pub type Result<T> = std::result::Result<T, super::error::Error>;
}

use result::Result;

const TOKEN_LIST_URI: &str = "https://token.jup.ag/strict";

/// A struct that represents a token. Used for parsing from response of `get_token_list()`.
#[derive(Deserialize)]
pub struct Token {
    address: String,
    #[serde(rename = "chainId")]
    chain_id: usize,
    decimals: u8,
    name: String,
    symbol: String,
    #[serde(rename = "logoURI")]
    logo_uri: Option<String>,
    tags: Option<Vec<String>>,
    extensions: Option<HashMap<String, String>>,
}

#[derive(Deserialize)]
pub struct Tokens {
    tokens: Vec<Token>,
}

/// Loads STRICT token list from Jupiter.
#[debug_handler]
pub async fn get_token_list() -> Result<Json<Vec<String>>> {
    let tokens = reqwest::get(TOKEN_LIST_URI).await?;

    let tokens: Vec<Token> = tokens.json().await?;

    let mut token_addresses = vec![];

    for token in tokens {
        token_addresses.push(token.symbol);
    }

    Ok(Json(token_addresses))
}
