"""
데이터베이스 마이그레이션 스크립트
기존 사용자에게 is_approved, is_admin 필드 추가
"""

from app import app, db
from models import User

with app.app_context():
    # 1. 새 컬럼 추가 (models.py에서 이미 정의됨)
    # SQLite는 ALTER TABLE ADD COLUMN을 지원하므로 자동으로 추가됨
    
    # 2. 기존 사용자들 업데이트
    print("기존 사용자 확인 중...")
    users = User.query.all()
    
    if not users:
        print("기존 사용자가 없습니다.")
    else:
        print(f"{len(users)}명의 기존 사용자 발견!")
        
        # 첫 번째 사용자를 관리자로 설정하고 승인
        first_user = users[0]
        first_user.is_admin = True
        first_user.is_approved = True
        print(f"✓ {first_user.username}을(를) 관리자로 설정하고 승인했습니다.")
        
        # 나머지 사용자들은 승인만
        for user in users[1:]:
            if not hasattr(user, 'is_approved') or user.is_approved is None:
                user.is_approved = True
                print(f"✓ {user.username}을(를) 승인했습니다.")
        
        db.session.commit()
        print("\n마이그레이션 완료!")
        print(f"관리자: {first_user.username} ({first_user.email})")
