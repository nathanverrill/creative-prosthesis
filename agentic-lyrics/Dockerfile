# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container at /code
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code, config file, and static files
COPY ./app /code/app
COPY ./config.yaml /code/config.yaml
COPY ./static /code/static

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run uvicorn server
# Use 0.0.0.0 to make it accessible outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]