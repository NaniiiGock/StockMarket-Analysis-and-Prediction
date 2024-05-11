To launch container 

docker compose up --build


To enter psql

docker exec -it psqldb /bin/bash
psql -U user -d psqldb


Request examples

Register:

curl -X POST -H "Content-Type: application/json" -d '{"username":"testuser", "email":"test@example.com", "password":"test123"}' http://127.0.0.1:2010/register


Login:
curl -X POST -H "Content-Type: application/json" -d '{"username":"testuser", "password":"test123"}' http://127.0.0.1:2010/login


Add transaction into history:
curl -X POST -H "Content-Type: application/json" -d '{                      
    "user_id_sold": 2,                                                                              
    "user_id_bought": 1,
    "item": "Product A",
    "price": 10.99,
    "quantity": 2
}' http://127.0.0.1:2011/add_transaction

Retrieve user history:
curl http://localhost:2011/user_transactions/{user id}
