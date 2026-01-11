# Python 3.11 베이스
FROM python:3.11-slim

# 작업 디렉토리
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Node.js 18.x 설치
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 프로젝트 파일 복사
COPY requirements.txt .
COPY package.json .
COPY package-lock.json* .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Node.js 패키지 설치 (Puppeteer + Chromium)
RUN npm install

# Puppeteer 캐시 디렉토리 설정
ENV PUPPETEER_CACHE_DIR=/app/.cache/puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false

# 앱 파일 복사
COPY . .

# 포트 설정
EXPOSE 10000

# 실행 명령
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--chdir", "backend", "app:app"]
