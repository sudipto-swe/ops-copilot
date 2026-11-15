FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY target/ ./target/
EXPOSE 8001
CMD ["uvicorn", "target.gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]
