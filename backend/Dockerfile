FROM python:3.11-slim
WORKDIR /app

# Copy and install requirements, then clean up in a single layer to reduce image size
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
    rm -rf /root/.cache/pip

# Copy the rest of the application code (respecting .dockerignore)
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
