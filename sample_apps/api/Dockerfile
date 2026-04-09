FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./sample_apps/api/requirements.txt
RUN pip install --no-cache-dir -r sample_apps/api/requirements.txt

# Copy API source into the expected package path
COPY . ./sample_apps/api/

# Create __init__.py files so Python treats these as packages
RUN touch sample_apps/__init__.py sample_apps/api/__init__.py

EXPOSE 8000

CMD ["uvicorn", "sample_apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
