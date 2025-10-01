FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app_clean:app", "--host", "0.0.0.0", "--port", "8000"]
