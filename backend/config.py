"""
애플리케이션 설정
"""
import os
from pathlib import Path

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

class Config:
    """기본 설정"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    database_url = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "odabnote.db"}'
    # Heroku/Render compatibility: postgres:// → postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 파일 업로드 (로컬 개발용 - Cloudinary 사용 시 불필요)
    UPLOAD_FOLDER = str(UPLOAD_FOLDER)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB 제한
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}  # gif 제거 (용량 큼)
    
    # Cloudinary 설정 (URL 방식)
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL') or ''
    
    # Mathpix API
    MATHPIX_APP_ID = os.environ.get('MATHPIX_APP_ID') or ''
    MATHPIX_APP_KEY = os.environ.get('MATHPIX_APP_KEY') or ''
    MATHPIX_API_URL = 'https://api.mathpix.com/v3/text'
    
    # 페이지네이션
    PROBLEMS_PER_PAGE = 20
    WORKBOOKS_PER_PAGE = 10


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    TESTING = False
    
    # 프로덕션에서는 반드시 환경변수로 설정해야 함
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")


# 환경에 따른 설정 선택
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
