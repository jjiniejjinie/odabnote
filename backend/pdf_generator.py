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
            # 시스템 한글 폰트 등록 시도
            font_paths = [
                '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf',
                '/System/Library/Fonts/AppleGothic.ttf',
            ]
            
            for font_path in font_paths:
                if Path(font_path).exists():
                    pdfmetrics.registerFont(TTFont('Korean', font_path))
                    break
            else:
                # 폰트를 찾지 못한 경우 기본 폰트 사용
                print("Warning: Korean font not found. Using default font.")
                
        except Exception as e:
            print(f"Font setup error: {e}")
    
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
        문제지 PDF 생성
        
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
        title = f"{unit.workbook.name} - {unit.name}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 10*mm))
        
        # 메타 정보
        meta_info = f"문제 수: {len(problems)}개 | 생성일: {datetime.now().strftime('%Y-%m-%d')}"
        story.append(Paragraph(meta_info, self.styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # 각 문제 추가
        for idx, problem in enumerate(problems, 1):
            # 문제 번호
            problem_num = Paragraph(f"<b>문제 {idx}</b>", self.problem_number_style)
            story.append(problem_num)
            
            # 문제 이미지
            if problem.problem_image_path:
                img_path = Path(problem.problem_image_path)
                if img_path.exists():
                    try:
                        img = Image(str(img_path))
                        # 이미지 크기 조정 (A4 너비에 맞춤)
                        img_width = 170*mm
                        aspect = img.imageHeight / img.imageWidth
                        img_height = img_width * aspect
                        
                        # 최대 높이 제한
                        max_height = 200*mm
                        if img_height > max_height:
                            img_height = max_height
                            img_width = img_height / aspect
                        
                        img.drawWidth = img_width
                        img.drawHeight = img_height
                        story.append(img)
                    except Exception as e:
                        story.append(Paragraph(f"[이미지 로드 오류: {e}]", self.body_style))
            
            # OCR 추출된 텍스트 (있는 경우)
            if problem.is_text_extracted and problem.problem_text:
                story.append(Spacer(1, 5*mm))
                story.append(Paragraph("<b>추출된 텍스트:</b>", self.body_style))
                
                # Markdown을 HTML로 변환하여 표시
                text_html = self._markdown_to_html(problem.problem_text)
                story.append(Paragraph(text_html, self.body_style))
            
            story.append(Spacer(1, 10*mm))
            
            # 페이지 나누기 (마지막 문제가 아닌 경우)
            if idx < len(problems):
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
