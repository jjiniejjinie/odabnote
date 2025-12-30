"""
PDF 생성 모듈
문제지 PDF, 정답지 PDF 생성
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from datetime import datetime
from pathlib import Path
import markdown
from io import BytesIO


class PDFGenerator:
    """PDF 생성기 클래스"""
    
    def __init__(self):
        """PDF 생성기 초기화"""
        self.styles = getSampleStyleSheet()
        self._setup_korean_font()
        self._setup_custom_styles()
    
    def _setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            # 1. 시스템 한글 폰트 등록 시도
            font_paths = [
                '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf',
                '/System/Library/Fonts/AppleGothic.ttf',
            ]
            
            for font_path in font_paths:
                if Path(font_path).exists():
                    pdfmetrics.registerFont(TTFont('Korean', font_path))
                    print(f"Korean font loaded: {font_path}")
                    return
            
            # 2. 시스템 폰트 없으면 Google Fonts에서 다운로드
            print("System Korean font not found. Downloading Noto Sans KR...")
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Regular.ttf"
            
            import urllib.request
            font_dir = Path(__file__).parent / 'fonts'
            font_dir.mkdir(exist_ok=True)
            font_path = font_dir / 'NotoSansKR-Regular.ttf'
            
            if not font_path.exists():
                urllib.request.urlretrieve(font_url, str(font_path))
                print(f"Downloaded font to: {font_path}")
            
            pdfmetrics.registerFont(TTFont('Korean', str(font_path)))
            print("Korean font loaded successfully!")
                
        except Exception as e:
            print(f"Font setup error: {e}")
            print("WARNING: Korean text will not display correctly!")
    
    def _setup_custom_styles(self):
        """커스텀 스타일 설정"""
        # 제목 스타일
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName='Korean',
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # 문제 번호 스타일
        self.problem_number_style = ParagraphStyle(
            'ProblemNumber',
            parent=self.styles['Normal'],
            fontName='Korean',
            fontSize=12,
            textColor=colors.HexColor('#3498DB'),
            spaceBefore=15,
            spaceAfter=10,
            leftIndent=0
        )
        
        # 본문 스타일
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontName='Korean',
            fontSize=11,
            leading=16,
            leftIndent=10
        )
    
    def generate_problem_pdf(self, unit, problems, output_path):
        """
        문제지 PDF 생성 (2x3 그리드 형식)
        왼쪽: 문제 이미지, 오른쪽: 풀이 공간
        
        Args:
            unit: Unit 모델 객체
            problems: Problem 모델 객체 리스트
            output_path: 저장할 파일 경로
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=10*mm,
            bottomMargin=10*mm,
            leftMargin=10*mm,
            rightMargin=10*mm
        )
        
        story = []
        
        # 제목
        title = f"{unit.workbook.name} - {unit.name}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 5*mm))
        
        # 메타 정보
        meta_info = f"문제 수: {len(problems)}개 | 생성일: {datetime.now().strftime('%Y-%m-%d')}"
        story.append(Paragraph(meta_info, self.styles['Normal']))
        story.append(Spacer(1, 5*mm))
        story.append(PageBreak())
        
        # 2x3 그리드로 문제 배치
        problems_per_page = 3
        cell_width = 90*mm  # 한 셀의 너비
        cell_height = 90*mm  # 한 셀의 높이
        
        for page_idx in range(0, len(problems), problems_per_page):
            page_problems = problems[page_idx:page_idx + problems_per_page]
            
            # 한 페이지에 들어갈 테이블 데이터 생성
            table_data = []
            
            for problem in page_problems:
                # 왼쪽 셀: 문제 번호 + 이미지
                left_content = []
                problem_num_text = f"문제 {problem.problem_number}"
                left_content.append(Paragraph(f"<b>{problem_num_text}</b>", self.problem_number_style))
                
                if problem.problem_image_path:
                    img_path = Path(problem.problem_image_path)
                    if img_path.exists():
                        try:
                            img = Image(str(img_path))
                            # 이미지 크기를 셀에 맞게 조정
                            max_width = 85*mm
                            max_height = 80*mm
                            
                            aspect = img.imageHeight / img.imageWidth
                            img_width = max_width
                            img_height = img_width * aspect
                            
                            if img_height > max_height:
                                img_height = max_height
                                img_width = img_height / aspect
                            
                            img.drawWidth = img_width
                            img.drawHeight = img_height
                            left_content.append(img)
                        except Exception as e:
                            left_content.append(Paragraph(f"[이미지 로드 오류]", self.body_style))
                
                # 오른쪽 셀: 풀이 공간 (빈 칸)
                right_content = [Paragraph("<b>풀이</b>", self.problem_number_style)]
                
                # 테이블 행 추가
                table_data.append([left_content, right_content])
            
            # 테이블 생성
            table = Table(table_data, colWidths=[cell_width, cell_width])
            table.setStyle(TableStyle([
                # 테두리
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                
                # 셀 정렬
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                
                # 패딩
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(table)
            
            # 다음 페이지로 (마지막 페이지가 아니면)
            if page_idx + problems_per_page < len(problems):
                story.append(PageBreak())
        
        # PDF 생성
        doc.build(story)
        return output_path
    
    def generate_answer_pdf(self, unit, problems, output_path):
        """
        정답지 PDF 생성
        
        Args:
            unit: Unit 모델 객체
            problems: Problem 모델 객체 리스트
            output_path: 저장할 파일 경로
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=20*mm,
            bottomMargin=20*mm,
            leftMargin=20*mm,
            rightMargin=20*mm
        )
        
        story = []
        
        # 제목
        title = f"{unit.workbook.name} - {unit.name} [정답]"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 10*mm))
        
        # 각 문제의 정답 추가
        for idx, problem in enumerate(problems, 1):
            if not problem.has_answer:
                continue
            
            # 문제 번호
            problem_num = Paragraph(f"<b>문제 {idx} 정답</b>", self.problem_number_style)
            story.append(problem_num)
            
            # 정답 이미지
            if problem.answer_image_path:
                img_path = Path(problem.answer_image_path)
                if img_path.exists():
                    try:
                        img = Image(str(img_path))
                        img_width = 170*mm
                        aspect = img.imageHeight / img.imageWidth
                        img_height = img_width * aspect
                        
                        max_height = 200*mm
                        if img_height > max_height:
                            img_height = max_height
                            img_width = img_height / aspect
                        
                        img.drawWidth = img_width
                        img.drawHeight = img_height
                        story.append(img)
                    except Exception as e:
                        story.append(Paragraph(f"[이미지 로드 오류: {e}]", self.body_style))
            
            # 정답 텍스트
            if problem.answer_text:
                story.append(Spacer(1, 5*mm))
                text_html = self._markdown_to_html(problem.answer_text)
                story.append(Paragraph(text_html, self.body_style))
            
            story.append(Spacer(1, 10*mm))
        
        # PDF 생성
        doc.build(story)
        return output_path
    
    def _markdown_to_html(self, markdown_text):
        """
        Markdown 텍스트를 HTML로 변환
        수식 표시를 위한 간단한 변환
        """
        # Markdown을 HTML로 변환
        html = markdown.markdown(
            markdown_text,
            extensions=['extra', 'codehilite']
        )
        
        # LaTeX 수식을 적절히 표시 ($ ... $ → <i>...</i>)
        html = html.replace('$', '<i>').replace('$', '</i>')
        
        return html
    
    def generate_preview_pdf(self, problems, output_buffer):
        """
        미리보기용 간단한 PDF 생성 (BytesIO 반환)
        
        Args:
            problems: Problem 객체 리스트
            output_buffer: BytesIO 객체
        """
        doc = SimpleDocTemplate(output_buffer, pagesize=A4)
        story = []
        
        story.append(Paragraph("문제 미리보기", self.title_style))
        story.append(Spacer(1, 10*mm))
        
        for idx, problem in enumerate(problems[:5], 1):  # 최대 5개만
            story.append(Paragraph(f"문제 {idx}", self.problem_number_style))
            
            if problem.problem_image_path:
                img_path = Path(problem.problem_image_path)
                if img_path.exists():
                    img = Image(str(img_path), width=100*mm, height=70*mm)
                    story.append(img)
            
            story.append(Spacer(1, 5*mm))
        
        doc.build(story)
        return output_buffer
