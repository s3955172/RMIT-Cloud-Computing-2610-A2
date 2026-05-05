# Use the official Python 3.9 slim image for a lightweight container
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app.py .

# Expose port 80 to allow traffic to the Flask app
EXPOSE 80

# Command to run the application using Python
CMD ["python", "app.py"]
