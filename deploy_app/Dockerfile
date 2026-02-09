# Step 1: Use an official Python base image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Copy the rest of the application code (main.py)
COPY . .

# Step 5: Start the web server using Gunicorn
# We bind it to the 0.0.0.0 address and the port specified by the PORT variable
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app