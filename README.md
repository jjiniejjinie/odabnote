# 오답노트 앱 📚

수식이 포함된 문제를 쉽게 관리하고 PDF로 출력할 수 있는 오답노트 애플리케이션입니다.

## 주요 기능

- 📷 **사진으로 문제 추가**: 카메라로 문제를 촬영하여 바로 추가
- 🔍 **Mathpix OCR**: 수식과 텍스트 자동 추출 (Markdown 형식)
- 📚 **계층적 구조**: 문제집 → 단원 → 문제
- 📄 **PDF 생성**: 문제지와 정답지를 별도 PDF로 생성
- ✏️ **편집 기능**: 문제집, 단원, 문제 수정/삭제
- 👤 **사용자 관리**: 로그인/회원가입 지원

## 기술 스택

### 백엔드
- **Flask**: 웹 프레임워크
- **SQLAlchemy**: ORM
- **Flask-Login**: 사용자 인증
- **Mathpix API**: OCR
- **ReportLab**: PDF 생성

### 프론트엔드
- **HTML/CSS/JavaScript**: 기본 웹 기술
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd odabnote-app
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일 수정:
```
SECRET_KEY=your-secret-key
MATHPIX_APP_ID=your_mathpix_app_id
MATHPIX_APP_KEY=your_mathpix_app_key
```

### 5. 데이터베이스 초기화

```bash
cd backend
python app.py
```

처음 실행하면 데이터베이스가 자동으로 생성됩니다.

## 실행 방법

### 개발 모드

```bash
cd backend
python app.py
```

브라우저에서 `http://localhost:5000` 접속

### 프로덕션 모드

```bash
cd backend
gunicorn --bind 0.0.0.0:8000 app:app
```

## 배포 (Render)

### 1. Render에서 새 Web Service 생성

### 2. 환경변수 설정

Render 대시보드에서 다음 환경변수를 추가:

```
SECRET_KEY=<랜덤 문자열>
MATHPIX_APP_ID=<Mathpix App ID>
MATHPIX_APP_KEY=<Mathpix App Key>
DATABASE_URL=<PostgreSQL URL>
PYTHON_VERSION=3.11
```

### 3. Build Command

```bash
pip install -r requirements.txt
```

### 4. Start Command

```bash
cd backend && gunicorn --bind 0.0.0.0:$PORT app:app
```

## 사용 방법

### 1. 회원가입/로그인
- 처음 사용시 회원가입
- 이메일과 비밀번호로 로그인

### 2. 문제집 생성
- "내 문제집" 메뉴에서 문제집 추가
- 예: "수학 오답노트", "영어 문법 정리" 등

### 3. 단원 추가
- 문제집 클릭 후 단원 추가
- 예: "1단원 - 방정식", "2단원 - 함수" 등

### 4. 문제 추가
- "문제 추가" 메뉴에서 사진 촬영/업로드
- 문제집과 단원 선택
- 저장

### 5. 텍스트 추출
- 문제 상세 페이지에서 "텍스트 추출하기" 버튼 클릭
- Mathpix가 수식과 텍스트를 Markdown 형식으로 추출

### 6. 정답 추가
- 문제 상세 페이지에서 "정답 추가" 버튼
- 이미지 또는 텍스트로 정답 입력

### 7. PDF 생성
- 단원 페이지에서 "문제지 PDF" 또는 "정답지 PDF" 버튼 클릭
- PDF 다운로드

## 프로젝트 구조

```
odabnote-app/
├── backend/
│   ├── app.py              # Flask 메인 애플리케이션
│   ├── models.py           # 데이터베이스 모델
│   ├── config.py           # 설정
│   ├── mathpix_ocr.py      # Mathpix API 연동
│   └── pdf_generator.py    # PDF 생성
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── home.html
│       ├── workbook_list.html
│       ├── unit_list.html
│       ├── problem_add.html
│       ├── problem_list.html
│       └── problem_detail.html
├── uploads/               # 업로드된 파일 저장
├── requirements.txt       # Python 패키지
├── .env.example          # 환경변수 예시
└── README.md
```

## Mathpix API

Mathpix API 키 발급: https://mathpix.com/

- 무료 플랜: 월 1,000 requests
- 유료 플랜: 월 $4.99부터

## 라이선스

이 프로젝트는 개인적인 용도로 제작되었습니다.

## 문의

문제나 질문이 있으시면 이슈를 등록해주세요.

---

Made with ❤️ for better learning
