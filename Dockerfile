FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0

WORKDIR /app

RUN pip install --no-cache-dir "pydantic==2.11.7"

COPY src ./src
COPY run.sh ./run.sh

ENTRYPOINT ["bash", "/app/run.sh"]
