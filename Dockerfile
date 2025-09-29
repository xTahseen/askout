# Use an official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (wkhtmltopdf includes wkhtmltoimage)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wkhtmltopdf \
        xvfb \
        libfontconfig \
        libxrender1 \
        libjpeg62-turbo \
        fontconfig \
        libfreetype6 \
        libx11-6 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot files into the container
COPY . .

# Run your bot
CMD ["python", "main.py"]
