# Using official python runtime base image
FROM python:3.6-alpine

# Set the application directory
WORKDIR /app

# Install our requirements.txt
ADD ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy our code from the current folder to /app inside the container
ADD ./src/fileserver /app
ADD ./src/lib /app/lib

# Make port 80 available for links and/or publish
EXPOSE 8070


# Define our command to be run when launching the container
CMD ["python", "main.py"]
