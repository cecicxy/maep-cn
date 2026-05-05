FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DB_PATH=/data/maep.db
RUN mkdir -p /data

EXPOSE 8000

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000", "--db", "/data/maep.db"]
