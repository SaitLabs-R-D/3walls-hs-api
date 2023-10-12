FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update -y \
    && apt-get install -y \
         cron

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]