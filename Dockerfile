# Use a slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# [NEW] Force Python's stdout and stderr to be unbuffered
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy the model directory (THIS WAS MISSING)
COPY model/ ./model/

# Copy the history data to /data/history.csv as expected by the spec
# (The spec says the environment provides this file at /data/history.csv) [cite: 54]
COPY data/history.csv ./data/history.csv

# Set PYTHONPATH so python can find the 'src' module
ENV PYTHONPATH=/app

# Command to run your application
CMD ["python", "-m", "src.main"]