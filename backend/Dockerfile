FROM python:3.11-slim

WORKDIR /app

# Ensure output is unbuffered so logs flow directly to standard out
ENV PYTHONUNBUFFERED=1

# Install requirements first for optimal layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port and start Uvicorn
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
