FROM python:3.9-slim

WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    wget ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcairo2 libcups2 libdbus-1-3 libgbm1 libglib2.0-0 \
    libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libxss1 libxtst6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

# Install Playwright system dependencies first, then browsers
RUN playwright install-deps chromium firefox && \
    playwright install chromium firefox

COPY . .

EXPOSE 8000

# Use shell form to allow PORT variable expansion
CMD sh -c "uvicorn web_app:app --host 0.0.0.0 --port ${PORT:-8000}"
