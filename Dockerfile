FROM python:3.11-slim
WORKDIR /app
COPY src/ ./src/
COPY data/ ./data/
COPY logs/ ./logs/
ENV PYTHONPATH=/app
CMD ["python", "src/main.py"]
