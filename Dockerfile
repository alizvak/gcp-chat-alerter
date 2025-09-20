# Dockerfile

# Use an official lightweight Python image as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main.py file from your local machine to /app in the container
COPY main.py .

# Define an environment variable for the port number
ENV PORT 8080

# Tell the container to listen on the specified port
EXPOSE 8080

# This is the command that will run when the container starts.
# It starts the functions-framework server, points to your function (send_dataform_alert),
# and tells it to expect a CloudEvent trigger.
CMD ["functions-framework", "--target=send_dataform_alert", "--signature-type=cloudevent", "--port=8080"]
