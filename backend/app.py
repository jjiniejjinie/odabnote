from dotenv import load_dotenv
load_dotenv()

"""
Flask 메인 애플리케이션
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api

from models import db, User, Workbook, Unit, Problem
from config import config
from mathpix_ocr import MathpixOCR
from pdf_generator import PDFGenerator

# Flask 앱 생성
def create_app(config_name='development'):
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    # 설정 로드
    app.config.from_object(config[config_name])
    
    # Cloudinary 설정 (환경변수에서 직접 읽기)
    import os
    cloudinary_url = os.environ.get('CLOUDINARY_URL') or app.config.get('CLOUDINARY_URL')
    if cloudinary_url:
        # URL 파싱해서 설정
        # cloudinary://API_KEY:API_SECRET@CLOUD_NAME 형식
        try:
            from urllib.parse import urlparse
            parsed = urlparse(cloudinary_url)
            cloudinary.config(
                cloud_name=parsed.hostname,
                api_key=parsed.username,
                api_secret=parsed.password,
                secure=True
            )
        except Exception as e:
            print(f"Cloudinary config error: {e}")
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 로그인 매니저 초기화
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = '로그인이 필요합니다.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # OCR 및 PDF 생성기
    mathpix = MathpixOCR(
        app.config['MATHPIX_APP_ID'],
        app.config['MATHPIX_APP_KEY']
    )
    pdf_generator = PDFGenerator()
    
    # 파일 업로드 헬퍼
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    def save_uploaded_file(file, subfolder='problems'):
        """파일 업로드 및 Cloudinary에 저장"""
        if file and allowed_file(file.filename):
            try:
                # 고유한 public_id 생성
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(file.filename)
                public_id = f"odabnote/{subfolder}/{current_user.id}/{timestamp}_{filename.rsplit('.', 1)[0]}"
                
                # Cloudinary에 업로드
                result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder=f"odabnote/{subfolder}",
                    resource_type="image"
                )
                
                # Cloudinary URL 반환 (public_id 저장)
                return result['public_id']
            except Exception as e:
                print(f"Cloudinary upload error: {e}")
                return None
        return None
    
    # ==================== 라우트 ====================
    
    @app.route('/')
    def index():
        """메인 페이지"""
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        return redirect(url_for('login'))
    
    # ==================== 인증 ====================
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """로그인"""
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                # 승인 여부 확인
                if not user.is_approved:
                    flash('관리자 승인 대기 중입니다. 승인 후 로그인할 수 있습니다.', 'warning')
                    return render_template('login.html')
                
                login_user(user, remember=True)
                flash('로그인 성공!', 'success')
                return redirect(url_for('home'))
            else:
                flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'danger')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """회원가입"""
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            agree_terms = request.form.get('agree_terms')  # 이용약관 동의
            
            # 이용약관 동의 체크
            if not agree_terms:
                flash('이용약관에 동의해주세요.', 'danger')
                return render_template('register.html')
            
            # 유효성 검사
            if password != confirm_password:
                flash('비밀번호가 일치하지 않습니다.', 'danger')
                return render_template('register.html')
            
            if User.query.filter_by(email=email).first():
                flash('이미 사용 중인 이메일입니다.', 'danger')
                return render_template('register.html')
            
            if User.query.filter_by(username=username).first():
                flash('이미 사용 중인 사용자명입니다.', 'danger')
                return render_template('register.html')
            
            # 사용자 생성 (기본적으로 승인 안 됨)
            user = User(username=username, email=email)
            user.set_password(password)
            # is_approved는 기본값 False
            
            db.session.add(user)
            db.session.commit()
            
            flash('회원가입 성공! 관리자 승인 후 로그인할 수 있습니다.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """로그아웃"""
        logout_user()
        flash('로그아웃되었습니다.', 'info')
        return redirect(url_for('login'))
    
    # ==================== 홈 ====================
    
    @app.route('/home')
    @login_required
    def home():
        """홈 화면"""
        workbooks = Workbook.query.filter_by(user_id=current_user.id).all()
        return render_template('home.html', workbooks=workbooks)
    
    # ==================== 문제집 관리 ====================
    
    @app.route('/workbooks')
    @login_required
    def workbook_list():
        """문제집 목록"""
        workbooks = Workbook.query.filter_by(user_id=current_user.id)\
                                  .order_by(Workbook.created_at.desc()).all()
        return render_template('workbook_list.html', workbooks=workbooks)
    
    @app.route('/workbooks/create', methods=['POST'])
    @login_required
    def workbook_create():
        """문제집 생성"""
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('문제집 이름을 입력해주세요.', 'danger')
            return redirect(url_for('workbook_list'))
        
        workbook = Workbook(
            name=name,
            description=description,
            user_id=current_user.id
        )
        db.session.add(workbook)
        db.session.commit()
        
        flash(f'문제집 "{name}"이 생성되었습니다.', 'success')
        return redirect(url_for('workbook_list'))
    
    @app.route('/workbooks/<int:workbook_id>/edit', methods=['POST'])
    @login_required
    def workbook_edit(workbook_id):
        """문제집 수정"""
        workbook = Workbook.query.get_or_404(workbook_id)
        
        if workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('workbook_list'))
        
        workbook.name = request.form.get('name')
        workbook.description = request.form.get('description', '')
        workbook.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('문제집이 수정되었습니다.', 'success')
        return redirect(url_for('workbook_list'))
    
    @app.route('/workbooks/<int:workbook_id>/delete', methods=['POST'])
    @login_required
    def workbook_delete(workbook_id):
        """문제집 삭제"""
        workbook = Workbook.query.get_or_404(workbook_id)
        
        if workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('workbook_list'))
        
        db.session.delete(workbook)
        db.session.commit()
        
        flash('문제집이 삭제되었습니다.', 'info')
        return redirect(url_for('workbook_list'))
    
    # ==================== 단원 관리 ====================
    
    @app.route('/workbooks/<int:workbook_id>/units')
    @login_required
    def unit_list(workbook_id):
        """단원 목록"""
        workbook = Workbook.query.get_or_404(workbook_id)
        
        if workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('workbook_list'))
        
        units = Unit.query.filter_by(workbook_id=workbook_id)\
                         .order_by(Unit.order).all()
        return render_template('unit_list.html', workbook=workbook, units=units)
    
    @app.route('/workbooks/<int:workbook_id>/units/create', methods=['POST'])
    @login_required
    def unit_create(workbook_id):
        """단원 생성"""
        workbook = Workbook.query.get_or_404(workbook_id)
        
        if workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('unit_list', workbook_id=workbook_id))
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('단원 이름을 입력해주세요.', 'danger')
            return redirect(url_for('unit_list', workbook_id=workbook_id))
        
        # 순서 자동 할당
        max_order = db.session.query(db.func.max(Unit.order))\
                              .filter_by(workbook_id=workbook_id).scalar() or 0
        
        unit = Unit(
            name=name,
            description=description,
            workbook_id=workbook_id,
            order=max_order + 1
        )
        db.session.add(unit)
        db.session.commit()
        
        flash(f'단원 "{name}"이 생성되었습니다.', 'success')
        return redirect(url_for('unit_list', workbook_id=workbook_id))
    
    @app.route('/units/<int:unit_id>/edit', methods=['POST'])
    @login_required
    def unit_edit(unit_id):
        """단원 수정"""
        unit = Unit.query.get_or_404(unit_id)
        
        if unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('workbook_list'))
        
        unit.name = request.form.get('name')
        unit.description = request.form.get('description', '')
        unit.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('단원이 수정되었습니다.', 'success')
        return redirect(url_for('unit_list', workbook_id=unit.workbook_id))
    
    @app.route('/units/<int:unit_id>/delete', methods=['POST'])
    @login_required
    def unit_delete(unit_id):
        """단원 삭제"""
        unit = Unit.query.get_or_404(unit_id)
        workbook_id = unit.workbook_id
        
        if unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('workbook_list'))
        
        db.session.delete(unit)
        db.session.commit()
        
        flash('단원이 삭제되었습니다.', 'info')
        return redirect(url_for('unit_list', workbook_id=workbook_id))
    
    # ==================== 문제 관리 ====================
    
    @app.route('/units/<int:unit_id>/problems')
    @login_required
    def problem_list(unit_id):
        """문제 목록"""
        unit = Unit.query.get_or_404(unit_id)
        
        if unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('workbook_list'))
        
        problems = Problem.query.filter_by(unit_id=unit_id)\
                                .order_by(Problem.problem_number).all()
        return render_template('problem_list.html', unit=unit, problems=problems)
    
    @app.route('/problems/add', methods=['GET', 'POST'])
    @login_required
    def problem_add():
        """문제 추가"""
        if request.method == 'GET':
            workbooks = Workbook.query.filter_by(user_id=current_user.id).all()
            return render_template('problem_add.html', workbooks=workbooks)
        
        # POST 요청
        unit_id = request.form.get('unit_id')
        problem_image = request.files.get('problem_image')
        
        if not unit_id or not problem_image:
            flash('단원과 문제 이미지를 선택해주세요.', 'danger')
            return redirect(url_for('problem_add'))
        
        unit = Unit.query.get_or_404(unit_id)
        if unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('home'))
        
        # 이미지 저장
        image_path = save_uploaded_file(problem_image, f'problems/{unit_id}')
        
        if not image_path:
            flash('이미지 업로드에 실패했습니다.', 'danger')
            return redirect(url_for('problem_add'))
        
        # 문제 번호 자동 할당
        max_number = db.session.query(db.func.max(Problem.problem_number))\
                               .filter_by(unit_id=unit_id).scalar() or 0
        
        problem = Problem(
            unit_id=unit_id,
            problem_image_path=image_path,
            problem_number=max_number + 1
        )
        db.session.add(problem)
        db.session.commit()
        
        flash('문제가 추가되었습니다.', 'success')
        return redirect(url_for('problem_list', unit_id=unit_id))
    
    @app.route('/problems/<int:problem_id>')
    @login_required
    def problem_detail(problem_id):
        """문제 상세"""
        problem = Problem.query.get_or_404(problem_id)
        
        if problem.unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('home'))
        
        return render_template('problem_detail.html', problem=problem)
    
    @app.route('/problems/<int:problem_id>/extract', methods=['POST'])
    @login_required
    def problem_extract_text(problem_id):
        """문제 텍스트 추출 (Mathpix OCR) - 임시로만 반환"""
        problem = Problem.query.get_or_404(problem_id)
        
        if problem.unit.workbook.user_id != current_user.id:
            return jsonify({'success': False, 'error': '권한이 없습니다.'}), 403
        
        # 절대 경로로 변환
        from pathlib import Path
        base_dir = Path(__file__).parent.parent
        absolute_path = base_dir / problem.problem_image_path
        
        # OCR 실행
        result = mathpix.extract_from_image(str(absolute_path))
        
        if result['success']:
            # DB에 저장하지 않고 텍스트만 반환
            return jsonify({
                'success': True,
                'text': result['text']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    @app.route('/problems/<int:problem_id>/text/save', methods=['POST'])
    @login_required
    def problem_save_text(problem_id):
        """문제 텍스트 저장"""
        problem = Problem.query.get_or_404(problem_id)
        
        if problem.unit.workbook.user_id != current_user.id:
            return jsonify({'success': False, 'error': '권한이 없습니다.'}), 403
        
        data = request.get_json()
        text = data.get('text', '')
        
        problem.problem_text = text
        problem.is_text_extracted = True
        db.session.commit()
        
        return jsonify({'success': True})
    
    @app.route('/problems/<int:problem_id>/answer/add', methods=['POST'])
    @login_required
    def problem_add_answer(problem_id):
        """정답 추가/수정"""
        problem = Problem.query.get_or_404(problem_id)
        
        if problem.unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('problem_detail', problem_id=problem_id))
        
        answer_type = request.form.get('answer_type')  # 'image' or 'text'
        
        if answer_type == 'image':
            answer_image = request.files.get('answer_image')
            if answer_image:
                image_path = save_uploaded_file(answer_image, f'answers/{problem.unit_id}')
                # 기존 정답 덮어쓰기
                problem.answer_image_path = image_path
                problem.answer_text = None  # 텍스트 정답 제거
        elif answer_type == 'text':
            answer_text = request.form.get('answer_text')
            # 기존 정답 덮어쓰기
            problem.answer_text = answer_text
            problem.answer_image_path = None  # 이미지 정답 제거
        
        problem.has_answer = True
        db.session.commit()
        
        flash('정답이 저장되었습니다.', 'success')
        return redirect(url_for('problem_detail', problem_id=problem_id))
    
    @app.route('/problems/<int:problem_id>/delete', methods=['POST'])
    @login_required
    def problem_delete(problem_id):
        """문제 삭제"""
        problem = Problem.query.get_or_404(problem_id)
        unit_id = problem.unit_id
        
        if problem.unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('home'))
        
        db.session.delete(problem)
        db.session.commit()
        
        flash('문제가 삭제되었습니다.', 'info')
        return redirect(url_for('problem_list', unit_id=unit_id))
    
    # ==================== PDF 생성 ====================
    
    @app.route('/units/<int:unit_id>/pdf/problems')
    @login_required
    def generate_problem_pdf(unit_id):
        """문제지 PDF 생성"""
        unit = Unit.query.get_or_404(unit_id)
        
        if unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('home'))
        
        problems = Problem.query.filter_by(unit_id=unit_id)\
                                .order_by(Problem.problem_number).all()
        
        if not problems:
            flash('문제가 없습니다.', 'warning')
            return redirect(url_for('problem_list', unit_id=unit_id))
        
        # PDF 생성
        pdf_dir = Path(app.config['UPLOAD_FOLDER']) / 'pdfs'
        pdf_dir.mkdir(exist_ok=True)
        
        filename = f"문제지_{unit.workbook.name}_{unit.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = pdf_dir / filename
        
        # PDF 생성 시 현재 사용자명 전달 (워터마크용)
        pdf_generator.generate_problem_pdf(unit, problems, str(output_path), username=current_user.username)
        
        return send_file(str(output_path), as_attachment=True, download_name=filename)
    
    @app.route('/units/<int:unit_id>/pdf/answers')
    @login_required
    def generate_answer_pdf(unit_id):
        """정답지 PDF 생성"""
        unit = Unit.query.get_or_404(unit_id)
        
        if unit.workbook.user_id != current_user.id:
            flash('권한이 없습니다.', 'danger')
            return redirect(url_for('home'))
        
        problems = Problem.query.filter_by(unit_id=unit_id)\
                                .order_by(Problem.problem_number).all()
        
        if not problems:
            flash('문제가 없습니다.', 'warning')
            return redirect(url_for('problem_list', unit_id=unit_id))
        
        # PDF 생성
        pdf_dir = Path(app.config['UPLOAD_FOLDER']) / 'pdfs'
        pdf_dir.mkdir(exist_ok=True)
        
        filename = f"정답지_{unit.workbook.name}_{unit.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = pdf_dir / filename
        
        # PDF 생성 시 현재 사용자명 전달 (워터마크용)
        pdf_generator.generate_answer_pdf(unit, problems, str(output_path), username=current_user.username)
        
        return send_file(str(output_path), as_attachment=True, download_name=filename)
    
    # ==================== API (AJAX용) ====================
    
    @app.route('/api/units/by-workbook/<int:workbook_id>')
    @login_required
    def api_get_units(workbook_id):
        """특정 문제집의 단원 목록 반환 (AJAX)"""
        workbook = Workbook.query.get_or_404(workbook_id)
        
        if workbook.user_id != current_user.id:
            return jsonify({'error': '권한이 없습니다.'}), 403
        
        units = Unit.query.filter_by(workbook_id=workbook_id)\
                         .order_by(Unit.order).all()
        
        return jsonify({
            'units': [{'id': u.id, 'name': u.name} for u in units]
        })
    
    # ==================== 관리자 ====================
    
    @app.route('/admin/users')
    @login_required
    def admin_users():
        """관리자 페이지 - 사용자 승인 관리"""
        # 관리자만 접근 가능
        if not current_user.is_admin:
            flash('관리자만 접근할 수 있습니다.', 'danger')
            return redirect(url_for('home'))
        
        # 승인 대기 중인 사용자 목록
        pending_users = User.query.filter_by(is_approved=False).order_by(User.created_at.desc()).all()
        
        # 승인된 사용자 목록
        approved_users = User.query.filter_by(is_approved=True).order_by(User.created_at.desc()).all()
        
        return render_template('admin_users.html', 
                             pending_users=pending_users,
                             approved_users=approved_users)
    
    @app.route('/admin/users/<int:user_id>/approve', methods=['POST'])
    @login_required
    def admin_approve_user(user_id):
        """사용자 승인"""
        if not current_user.is_admin:
            flash('관리자만 접근할 수 있습니다.', 'danger')
            return redirect(url_for('home'))
        
        user = User.query.get_or_404(user_id)
        user.is_approved = True
        db.session.commit()
        
        flash(f'{user.username}님을 승인했습니다.', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/<int:user_id>/reject', methods=['POST'])
    @login_required
    def admin_reject_user(user_id):
        """사용자 거부 (삭제)"""
        if not current_user.is_admin:
            flash('관리자만 접근할 수 있습니다.', 'danger')
            return redirect(url_for('home'))
        
        user = User.query.get_or_404(user_id)
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'{username}님의 가입 신청을 거부했습니다.', 'info')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/<int:user_id>/revoke', methods=['POST'])
    @login_required
    def admin_revoke_user(user_id):
        """사용자 승인 취소"""
        if not current_user.is_admin:
            flash('관리자만 접근할 수 있습니다.', 'danger')
            return redirect(url_for('home'))
        
        user = User.query.get_or_404(user_id)
        user.is_approved = False
        db.session.commit()
        
        flash(f'{user.username}님의 승인을 취소했습니다.', 'warning')
        return redirect(url_for('admin_users'))
    
    # ==================== 정적 파일 서빙 ====================
    
    # Jinja2 템플릿 헬퍼 함수
    @app.template_filter('cloudinary_url')
    def cloudinary_url_filter(public_id, width=None, height=None):
        """Cloudinary 이미지 URL 생성"""
        if not public_id:
            return ''
        
        # 이미 http로 시작하면 그대로 반환 (기존 로컬 URL 호환)
        if public_id.startswith('http'):
            return public_id
        
        # Cloudinary URL 생성
        from cloudinary import CloudinaryImage
        transformation = {}
        if width:
            transformation['width'] = width
        if height:
            transformation['height'] = height
        
        return CloudinaryImage(public_id).build_url(**transformation)
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """
        업로드된 파일 서빙 (하위 호환성)
        새 파일은 Cloudinary 사용, 기존 파일은 로컬에서 서빙
        """
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        if (upload_folder / filename).exists():
            return send_from_directory(upload_folder, filename)
        else:
            # 파일이 없으면 404
            return "File not found", 404
    
    return app


# Railway/Render/Gunicorn용: app 객체를 모듈 레벨로 노출
app = create_app(os.environ.get('FLASK_ENV', 'production'))

# 데이터베이스 테이블 자동 생성 및 마이그레이션 (배포 환경)
with app.app_context():
    db.create_all()
    print("Database tables created!")
    
    # PostgreSQL 컬럼 추가 마이그레이션 (한 번만 실행)
    try:
        # is_approved 컬럼이 없으면 추가
        db.session.execute(db.text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT FALSE NOT NULL;
        """))
        
        db.session.execute(db.text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL;
        """))
        
        db.session.commit()
        print("✓ 컬럼 추가 완료 (또는 이미 존재)")
        
        # 기존 사용자 승인 처리
        users = User.query.all()
        if users:
            # 승인되지 않은 사용자가 있는지 확인
            unapproved = [u for u in users if not u.is_approved]
            if unapproved:
                print(f"기존 사용자 {len(users)}명 승인 처리 중...")
                
                # 첫 번째 사용자를 관리자로
                first_user = users[0]
                if not first_user.is_admin:
                    first_user.is_admin = True
                    first_user.is_approved = True
                    print(f"✓ {first_user.username} → 관리자")
                
                # 나머지 사용자 승인
                for user in users[1:]:
                    if not user.is_approved:
                        user.is_approved = True
                        print(f"✓ {user.username} → 승인")
                
                db.session.commit()
                print("✅ 기존 사용자 마이그레이션 완료!")
                
    except Exception as e:
        print(f"마이그레이션 오류 (무시 가능): {e}")
        db.session.rollback()

# 개발 서버 실행
if __name__ == '__main__':
    # 개발 환경 재생성
    app = create_app('development')
    
    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
