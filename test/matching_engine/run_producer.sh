docker build -f Dockerfile -t producer .

docker run --network stockmarket-analysis-and-prediction_matching_engine_to_frontend --rm producer
