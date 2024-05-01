To launch container 

docker compose up --build


TO enter psql

docker exec -it psqldb /bin/bash
psql -U user -d psqldb


Request examples

curl -X POST -H "Content-Type: application/json" -d '{"username":"testuser", "email":"test@example.com", "password":"test123"}' http://127.0.0.1:5000/register

curl -X POST -H "Content-Type: application/json" -d '{"username":"testuser", "password":"test123"}' http://127.0.0.1:5000/login

