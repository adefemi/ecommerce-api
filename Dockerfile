FROM python:3.7

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /ecommerce_api

WORKDIR /ecommerce_api

COPY . /ecommerce_api/

RUN pip install -r requirements.txt