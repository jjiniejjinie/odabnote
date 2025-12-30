"""
WSGI 엔트리포인트
"""
import os
import sys

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

# 환경 설정
config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)

# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()
