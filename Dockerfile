FROM amazonlinux:latest

# Inspired by https://github.com/tomelliff/py-s3-sftp-bridge/blob/master/Dockerfile

RUN yum install -y zip
RUN yum install -y python3
RUN curl -O -s https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

WORKDIR /working
COPY requirements.txt /working
RUN pip3 install -r requirements.txt -t .
COPY analyzer.py /working
COPY templates/compare_gamers.jinja2 /working/templates

RUN zip -r lambda.zip *
