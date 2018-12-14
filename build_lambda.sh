#!/bin/sh

mkdir BUILD
mkdir BUILD/templates
cp analyzer.py BUILD/
cp templates/compare_gamers.jinja2 BUILD/templates/
cp requirements.txt BUILD/
cd BUILD
pip install -r requirements.txt -t .
rm requirements.txt
zip -r lambda.zip *
mv lambda.zip ..
