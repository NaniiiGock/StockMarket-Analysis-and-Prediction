docker build -f Engine.Dockerfile -t engine .

docker run --network my-network --rm engine
