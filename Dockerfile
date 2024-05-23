FROM python:3.10.13

WORKDIR /competition_flask

COPY app.py .
COPY requirements.txt .

RUN pip install -r requirements.txt
