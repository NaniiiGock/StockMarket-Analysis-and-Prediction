use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use serde::Serialize;
use thiserror::Error;

pub mod price;

#[derive(Debug, Error)]
pub enum Error {
    #[error("cannot deserialize json for PriceStamp: {source}")]
    CannotCreatePriceStampJson { source: anyhow::Error },
    #[error("cannot get response from Jupiter API /price route: {:?}", source)]
    CannotGetPriceResponse { source: reqwest::Error },
    #[error("no such token in response: {token}")]
    NoSuchToken { token: String },
}

pub type Result<T> = std::result::Result<T, Error>;

impl Serialize for Error {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
        where
            S: serde::Serializer,
    {
        match self {
            Error::CannotCreatePriceStampJson { source } => {
                serializer.serialize_str(&format!("{}", source))
            }
            Error::CannotGetPriceResponse { source } => {
                serializer.serialize_str(&format!("{}", source))
            }
            error @ Error::NoSuchToken { .. } => serializer.serialize_str(&error.to_string()),
        }
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let body = self.to_string();
        (StatusCode::INTERNAL_SERVER_ERROR, body).into_response()
    }
}

