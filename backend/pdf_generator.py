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
        self.font_name = 'Helvetica'  # 기본 폰트
        
        try:
            # 프로젝트 내 폰트 파일 경로 (우선순위)
            font_path = Path(__file__).parent / 'fonts' / 'NanumGothic.ttf'
            
            if font_path.exists():
                pdfmetrics.registerFont(TTFont('Korean', str(font_path)))
                self.font_name = 'Korean'
                print(f"Korean font loaded from project: {font_path}")
            else:
                # 시스템 한글 폰트 시도
                system_font_paths = [
                    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                    '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf',
                    '/System/Library/Fonts/AppleGothic.ttf',
                ]
                
                for sys_font_path in system_font_paths:
                    if Path(sys_font_path).exists():
                        pdfmetrics.registerFont(TTFont('Korean', sys_font_path))
                        self.font_name = 'Korean'
                        print(f"Korean font loaded from system: {sys_font_path}")
                        break
                else:
                    print("Warning: Korean font not found. Using default font (Helvetica).")
                
        except Exception as e:
            print(f"Font setup error: {e}. Using default font.")
    
    def _setup_custom_styles(self):
        """커스텀 스타일 설정"""
        # 제목 스타일
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name,
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # 문제 번호 스타일
        self.problem_number_style = ParagraphStyle(
            'ProblemNumber',
            parent=self.styles['Normal'],
            fontName=self.font_name,
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
            fontName=self.font_name,
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
        
        # 제목과 날짜를 테이블로 배치
        title_text = f"{unit.workbook.name} - {unit.name}"
        date_text = f"{datetime.now().strftime('%Y-%m-%d')}"
        
        # 오른쪽 정렬 스타일
        right_align_style = ParagraphStyle(
            'RightAlign',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            alignment=TA_LEFT  # 테이블 셀 내에서 오른쪽 정렬
        )
        
        header_data = [[
            Paragraph(title_text, self.title_style),
            Paragraph(f"<para align='right'>{date_text}</para>", right_align_style)
        ]]
        
        header_table = Table(header_data, colWidths=[140*mm, 40*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 5*mm))
        
        # 2x3 그리드로 문제 배치
        problems_per_page = 3
        cell_width = 90*mm
        
        for page_idx in range(0, len(problems), problems_per_page):
            page_problems = problems[page_idx:page_idx + problems_per_page]
            
            table_data = []
            
            for problem in page_problems:
                # 왼쪽: 문제 번호 + 추출된 텍스트
                left_content = []
                problem_num_text = f"문제 {problem.problem_number}"
                left_content.append(Paragraph(f"<b>{problem_num_text}</b>", self.problem_number_style))
                
                # 추출된 텍스트가 있으면 텍스트 표시
                if problem.is_text_extracted and problem.problem_text:
                    # LaTeX 수식을 유니코드로 변환
                    text_display = self._convert_latex_to_unicode(problem.problem_text)
                    # HTML 특수문자 이스케이프 (< > &만)
                    text_display = text_display.replace('&', '&amp;')
                    text_display = text_display.replace('<br/>', '<br />')  # ReportLab 호환 형식
                    left_content.append(Paragraph(text_display, self.body_style))
                elif problem.problem_image_path:
                    # 추출된 텍스트가 없으면 이미지 표시
                    img_path = Path(problem.problem_image_path)
                    if img_path.exists():
                        try:
                            img = Image(str(img_path))
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
                
                # 오른쪽: 풀이 공간
                right_content = [Paragraph("<b>풀이</b>", self.problem_number_style)]
                
                table_data.append([left_content, right_content])
            
            # 테이블 생성 (높이 제한)
            cell_height = 85*mm
            row_heights = [cell_height] * len(table_data)
            
            table = Table(table_data, colWidths=[cell_width, cell_width], rowHeights=row_heights)
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(table)
            
            if page_idx + problems_per_page < len(problems):
                story.append(PageBreak())
        
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
    
    def _convert_latex_to_unicode(self, text):
        """
        LaTeX 수식을 유니코드로 변환하고 선지를 줄바꿈 처리
        """
        import re
        
        # 먼저 선지 줄바꿈 처리 (1), (2), (3) 등을 찾아서 앞에 줄바꿈 추가)
        # 패턴: (1), (2), (3), (4), (5) 형태
        text = re.sub(r'(\s*)\((\d)\)', r'<br/>\n(\2)', text)
        # 첫 번째 선지 앞의 줄바꿈 제거
        text = re.sub(r'^<br/>\n', '', text)
        
        # LaTeX 괄호 제거
        result = text.replace(r'\(', '').replace(r'\)', '')
        result = result.replace(r'\[', '').replace(r'\]', '')
        
        # mathrm, text 등 제거
        result = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', result)
        result = re.sub(r'\\text\{([^}]+)\}', r'\1', result)
        
        # ~ 기호 제거
        result = result.replace('~', ' ')
        
        # square 기호
        result = result.replace(r'\square', '□')
        
        # 연산 기호
        result = result.replace(r'\times', '×')
        result = result.replace(r'\div', '÷')
        result = result.replace(r'\cdot', '·')
        result = result.replace(r'\pm', '±')
        result = result.replace(r'\mp', '∓')
        
        # 비교 기호
        result = result.replace(r'\le', '≤')
        result = result.replace(r'\ge', '≥')
        result = result.replace(r'\leq', '≤')
        result = result.replace(r'\geq', '≥')
        result = result.replace(r'\ne', '≠')
        result = result.replace(r'\neq', '≠')
        result = result.replace(r'\approx', '≈')
        result = result.replace(r'\equiv', '≡')
        
        # 기타 수학 기호
        result = result.replace(r'\infty', '∞')
        result = result.replace(r'\sqrt', '√')
        result = result.replace(r'\pi', 'π')
        result = result.replace(r'\alpha', 'α')
        result = result.replace(r'\beta', 'β')
        result = result.replace(r'\gamma', 'γ')
        result = result.replace(r'\delta', 'δ')
        result = result.replace(r'\theta', 'θ')
        result = result.replace(r'\lambda', 'λ')
        result = result.replace(r'\mu', 'μ')
        result = result.replace(r'\sigma', 'σ')
        result = result.replace(r'\omega', 'ω')
        
        # 분수 변환
        fraction_map = {
            r'\\frac\{1\}\{2\}': '½',
            r'\\frac\{1\}\{3\}': '⅓',
            r'\\frac\{2\}\{3\}': '⅔',
            r'\\frac\{1\}\{4\}': '¼',
            r'\\frac\{3\}\{4\}': '¾',
            r'\\frac\{1\}\{5\}': '⅕',
            r'\\frac\{2\}\{5\}': '⅖',
            r'\\frac\{3\}\{5\}': '⅗',
            r'\\frac\{4\}\{5\}': '⅘',
            r'\\frac\{1\}\{6\}': '⅙',
            r'\\frac\{5\}\{6\}': '⅚',
            r'\\frac\{1\}\{8\}': '⅛',
            r'\\frac\{3\}\{8\}': '⅜',
            r'\\frac\{5\}\{8\}': '⅝',
            r'\\frac\{7\}\{8\}': '⅞',
        }
        
        # 분수 변환
        for latex, unicode_char in fraction_map.items():
            result = re.sub(latex, unicode_char, result)
        
        # 일반 분수 패턴 (위에 없는 것들) - 분자/분모 형식으로
        result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', result)
        
        # 중괄호 제거
        result = result.replace('{', '').replace('}', '')
        
        # 백슬래시 제거 (남은 LaTeX 명령어들)
        result = re.sub(r'\\[a-zA-Z]+', '', result)
        
        return result
    
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
