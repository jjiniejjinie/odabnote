#!/usr/bin/env bash
# Render 빌드 스크립트

set -o errexit

# 패키지 설치
pip install -r requirements.txt

# 한글 폰트 설치
apt-get update
apt-get install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra

echo "Build completed successfully!"
