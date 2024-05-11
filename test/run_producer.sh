docker build -f Producer.Dockerfile -t producer .

docker run --network my-network --rm producer
