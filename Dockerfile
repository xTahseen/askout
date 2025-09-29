# Use an official Python image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xfonts-base \
    xfonts-75dpi \
    libjpeg62-turbo \
    libxrender1 \
    libfontconfig \
    libfreetype6 \
    libx11-6 \
    xvfb && \
    wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bookworm_amd64.deb && \
    apt-get install -y ./wkhtmltox_0.12.6-1.bookworm_amd64.deb && \
    rm -f wkhtmltox_0.12.6-1.bookworm_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot files
COPY . .

CMD ["python", "main.py"]
