# Use official Python image
FROM python:3.11-slim

# Install system dependencies for Playwright and PyMuPDF
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies and browsers
RUN pip install --upgrade pip \
    && pip install playwright==1.53.0 \
    && playwright install --with-deps

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Copy Streamlit secrets (if present)
COPY .streamlit/secrets.toml /app/.streamlit/secrets.toml

# Expose Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"] 