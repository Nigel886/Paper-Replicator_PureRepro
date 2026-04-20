# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port (Render/Cloud Run will ignore this but it's good practice)
EXPOSE 8000

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Run the application with dynamic port binding for cloud environments
CMD uvicorn api.py:app --host 0.0.0.0 --port ${PORT:-8000}
