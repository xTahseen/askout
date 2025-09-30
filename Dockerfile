# Use an official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements if you have them
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot files into the container
COPY . .

# Run your bot
CMD ["python", "main.py"]
