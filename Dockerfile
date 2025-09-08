# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache, which reduces the image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# Default command to run when the container starts.
# This will be overridden by the arguments provided to the Cloud Run Job.
CMD ["echo", "Container built successfully. Specify a script to run via Cloud Run Job arguments."]
