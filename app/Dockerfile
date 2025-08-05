FROM python:3.11-slim

# Install system dependencies for Manim
RUN apt-get update && apt-get install -y \
    ffmpeg \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Manim
RUN pip install manim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create necessary directories
RUN mkdir -p /app/videos /tmp/manim_videos

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]