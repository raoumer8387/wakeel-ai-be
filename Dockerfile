# Use official Python lightweight image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=7860

# Set working directory
WORKDIR /code

# Install system dependencies (required for pytesseract/pdf conversions if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the HuggingFace default port
EXPOSE 7860

# Command to run uvicorn on HF's expected port (7860)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
