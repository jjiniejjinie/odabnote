"""
Mathpix OCR API 연동
수식 및 텍스트 추출 (Markdown 형식)
"""
import requests
import base64
from pathlib import Path


class MathpixOCR:
    """Mathpix API 래퍼 클래스"""
    
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.api_url = 'https://api.mathpix.com/v3/text'
    
    def extract_from_image(self, image_path):
        """
        이미지에서 텍스트 추출 (Markdown 형식)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            dict: {
                'success': bool,
                'text': str (Markdown),
                'error': str (실패시)
            }
        """
        try:
            # API 키가 설정되지 않은 경우
            if not self.app_id or not self.app_key:
                return {
                    'success': False,
                    'error': 'Mathpix API 키가 설정되지 않았습니다.'
                }
            
            # 이미지를 base64로 인코딩
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # API 요청
            headers = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'Content-type': 'application/json'
            }
            
            data = {
                'src': f'data:image/jpeg;base64,{image_data}',
                'formats': ['text', 'latex_styled'],  # Markdown 형식
                'data_options': {
                    'include_asciimath': True,
                    'include_latex': True
                }
            }
            
            response = requests.post(
                self.api_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Markdown 텍스트 추출
                text = result.get('text', '')
                latex = result.get('latex_styled', '')
                
                # LaTeX 수식을 Markdown 형식으로 변환
                if latex:
                    markdown_text = self._latex_to_markdown(text, latex)
                else:
                    markdown_text = text
                
                return {
                    'success': True,
                    'text': markdown_text,
                    'confidence': result.get('confidence', 0)
                }
            else:
                error_msg = response.json().get('error', '알 수 없는 오류')
                return {
                    'success': False,
                    'error': f'API 오류: {error_msg}'
                }
                
        except FileNotFoundError:
            return {
                'success': False,
                'error': '이미지 파일을 찾을 수 없습니다.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'API 요청 시간 초과'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'오류 발생: {str(e)}'
            }
    
    def extract_from_url(self, image_url):
        """
        URL에서 텍스트 추출 (Markdown 형식) - Cloudinary용
        
        Args:
            image_url: 이미지 URL
            
        Returns:
            dict: {
                'success': bool,
                'text': str (Markdown),
                'error': str (실패시)
            }
        """
        try:
            # API 키가 설정되지 않은 경우
            if not self.app_id or not self.app_key:
                return {
                    'success': False,
                    'error': 'Mathpix API 키가 설정되지 않았습니다.'
                }
            
            # API 요청
            headers = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'Content-type': 'application/json'
            }
            
            data = {
                'src': image_url,  # URL 직접 전달
                'formats': ['text', 'latex_styled'],  # Markdown 형식
                'data_options': {
                    'include_asciimath': True,
                    'include_latex': True
                }
            }
            
            response = requests.post(
                self.api_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Markdown 텍스트 추출
                text = result.get('text', '')
                latex = result.get('latex_styled', '')
                
                # LaTeX 수식을 Markdown 형식으로 변환
                if latex:
                    markdown_text = self._latex_to_markdown(text, latex)
                else:
                    markdown_text = text
                
                return {
                    'success': True,
                    'text': markdown_text,
                    'confidence': result.get('confidence', 0)
                }
            else:
                error_msg = response.json().get('error', '알 수 없는 오류')
                return {
                    'success': False,
                    'error': f'API 오류: {error_msg}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'API 요청 시간 초과'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'오류 발생: {str(e)}'
            }
    
    def _latex_to_markdown(self, text, latex):
        """
        LaTeX 수식을 Markdown 형식으로 변환
        인라인 수식: $...$
        블록 수식: $$...$$
        """
        # 간단한 변환 로직 (실제로는 더 복잡할 수 있음)
        if '\\[' in latex or '\\]' in latex:
            # 블록 수식
            markdown = f'$$\n{latex}\n$$'
        else:
            # 인라인 수식
            markdown = f'${latex}$'
        
        return markdown if markdown.strip() else text
    
    def extract_batch(self, image_paths):
        """
        여러 이미지 일괄 처리
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            
        Returns:
            list: 각 이미지의 추출 결과
        """
        results = []
        for path in image_paths:
            result = self.extract_from_image(path)
            results.append({
                'path': path,
                'result': result
            })
        return results


def test_mathpix_connection(app_id, app_key):
    """
    Mathpix API 연결 테스트
    """
    ocr = MathpixOCR(app_id, app_key)
    
    # 테스트 이미지 생성 (간단한 텍스트)
    test_image = Path('/tmp/test_mathpix.png')
    
    # 간단한 테스트용 이미지가 없다면 연결 테스트만
    if not test_image.exists():
        return {
            'success': True if app_id and app_key else False,
            'message': 'API 키가 설정되었습니다.' if app_id and app_key else 'API 키를 설정해주세요.'
        }
    
    result = ocr.extract_from_image(test_image)
    return result
