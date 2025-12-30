"""
데이터베이스 모델
문제집 -> 단원 -> 문제 계층 구조
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계
    workbooks = db.relationship('Workbook', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """비밀번호 해시화"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Workbook(db.Model):
    """문제집 모델"""
    __tablename__ = 'workbooks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    units = db.relationship('Unit', backref='workbook', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workbook {self.name}>'


class Unit(db.Model):
    """단원 모델"""
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    order = db.Column(db.Integer, default=0)  # 순서
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    problems = db.relationship('Problem', backref='unit', lazy=True, cascade='all, delete-orphan')
    
    @property
    def problem_count(self):
        """단원의 문제 수"""
        return len(self.problems)
    
    def __repr__(self):
        return f'<Unit {self.name}>'


class Problem(db.Model):
    """문제 모델"""
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    # 문제 이미지
    problem_image_path = db.Column(db.String(255), nullable=False)
    
    # OCR 추출된 텍스트 (Markdown)
    problem_text = db.Column(db.Text)
    is_text_extracted = db.Column(db.Boolean, default=False)
    
    # 정답 (이미지 또는 텍스트)
    answer_image_path = db.Column(db.String(255))
    answer_text = db.Column(db.Text)
    has_answer = db.Column(db.Boolean, default=False)
    
    # 메타데이터
    problem_number = db.Column(db.Integer)  # 단원 내 문제 번호
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Problem {self.id} - Unit {self.unit_id}>'
