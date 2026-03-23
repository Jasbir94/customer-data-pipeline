# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies (only backend requirements for the API server)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code and frontend static files
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Expose port 8000
EXPOSE 8000

# Run the FastAPI server using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
