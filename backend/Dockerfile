# backend/Dockerfile

FROM python:3.11-slim
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
# The PyTorch extra-index-url and the model pre-loading command are no longer needed
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Use the "shell" form of CMD
CMD uvicorn main:app --host 0.0.0.0 --port $PORT