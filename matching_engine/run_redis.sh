docker network create my-network

docker run --name my-redis --network my-network -p 6379:6379 -d redis
