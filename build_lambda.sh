#!/bin/sh

docker build -t streakanalyzer:latest .

rm -rf BUILD
mkdir BUILD
docker run -v $(pwd)/BUILD:/working2 --rm streakanalyzer:latest cp lambda.zip /working2
