docker build -f Dockerfile -t producer .

docker run --network final_project_default --rm producer
