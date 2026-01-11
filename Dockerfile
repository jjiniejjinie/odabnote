# Python 3.11 + Node 20
FROM python:3.11-slim

WORKDIR /app

# Chromium + Node.js 20 설치
RUN apt-get update && apt-get install -y \
    chromium \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 파일 복사
COPY requirements.txt package*.json ./

# Python 설치
RUN pip install --no-cache-dir -r requirements.txt

# Puppeteer 설정
ENV PUPPETEER_SKIP_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Node 설치
RUN npm ci --omit=dev || npm install

COPY . .

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--chdir", "backend", "app:app"]
