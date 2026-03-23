# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install all dependencies (backend + data pipeline)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files to generate data
COPY . .

# Generate the data during build process so the CSVs are baked into the image
RUN python generate_data.py && python clean_data.py && python analyze.py

# Expose default port (Render will dynamically assign PORT env var)
EXPOSE 8000

# Run the FastAPI server using Uvicorn, respecting Render's PORT environment variable
CMD sh -c "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
