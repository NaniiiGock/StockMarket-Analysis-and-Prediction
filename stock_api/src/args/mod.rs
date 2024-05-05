use std::sync::Arc;
use clap::Parser;
use scylla::Session;

#[derive(Parser, Clone)]
pub struct Args {
    /// A port to run the server at
    #[arg(long, default_value_t = 3000)]
    pub https_port: u16,
    /// An IP of the Cassandra DB of historical data 
    #[arg(long, default_value_t = String::from("stock_api_cassandra:2001"))]
    pub cassandra_node: String,
    /// An IP of the Kafka queue for streaming 
    #[arg(long, default_value_t = String::from("stock_api_kafka:2002"))]
    pub kafka_node: String,
}

#[derive(Clone)]
pub struct ServerState {
    pub session: Arc<Session>,
    pub kafka_node: String,
}
