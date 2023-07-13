FROM python:latest

WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-deps  --trusted-host 192.168.2.5 -v  -i http://192.168.2.5:18081/repository/pypi/simple  --extra-index-url https://pypi.org/simple -r requirements.txt
COPY  . .