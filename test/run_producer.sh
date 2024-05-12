docker build -f Dockerfile -t producer .

docker run --network stockmarket-analysis-and-prediction_default --rm producer
