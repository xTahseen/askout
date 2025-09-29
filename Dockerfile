FROM python:3.11-slim

WORKDIR /app

# Install dependencies needed at runtime
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
    rm -rf /var/lib/apt/lists/*

# Download & install wkhtmltox generic binary
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1-linux-generic-amd64.tar.xz && \
    tar -xJf wkhtmltox-0.12.6-1-linux-generic-amd64.tar.xz && \
    cp wkhtmltox/bin/wkhtmlto* /usr/local/bin/ && \
    rm -rf wkhtmltox-0.12.6-1-linux-generic-amd64.tar.xz wkhtmltox

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
