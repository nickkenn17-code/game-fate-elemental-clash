# Use an official, lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the Python game logic files into the container
COPY app.py worker.py game_logic.py ./

# The command to run (will be overridden by docker-compose for the worker)
CMD ["python3", "app.py"]