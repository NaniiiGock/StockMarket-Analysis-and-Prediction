#!/bin/bash
docker build -t stock_api .
docker run -d --rm --name=stock_api  -p 3000:3000 stock_api
