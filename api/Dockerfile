FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src

EXPOSE 5000

ENV FLASK_APP=src/main.py

ENV FLASK_RUN_HOST=0.0.0.0

ENV FLASK_ENV=development

CMD ["flask", "run"]
