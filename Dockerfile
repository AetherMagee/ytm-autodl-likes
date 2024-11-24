FROM python:3.13-alpine

RUN apk add --no-cache ffmpeg

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "main.py"]