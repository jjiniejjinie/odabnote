// 메인 JavaScript 파일

// 알림 자동 닫기
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// 이미지 미리보기
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById(previewId).src = e.target.result;
            document.getElementById(previewId).style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// 모달 제어
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }
});

// 확인 다이얼로그
function confirmDelete(message) {
    return confirm(message || '정말 삭제하시겠습니까?');
}

// 로딩 인디케이터
function showLoading() {
    const loading = document.createElement('div');
    loading.id = 'loading-overlay';
    loading.innerHTML = '<div class="loading-spinner">⏳ 처리 중...</div>';
    loading.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        loading.remove();
    }
}

// 텍스트 복사
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('클립보드에 복사되었습니다!');
    } catch (err) {
        console.error('복사 실패:', err);
        showToast('복사에 실패했습니다.', 'error');
    }
}

// Toast 메시지
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#2ecc71' : '#e74c3c'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 폼 유효성 검사
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#e74c3c';
            isValid = false;
        } else {
            field.style.borderColor = '';
        }
    });
    
    if (!isValid) {
        showToast('모든 필수 항목을 입력해주세요.', 'error');
    }
    
    return isValid;
}

// 이미지 로드 에러 처리
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.onerror = function() {
            this.src = '/static/img/placeholder.png';
            this.alt = '이미지를 불러올 수 없습니다';
        };
    });
});

// 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 스크롤 탑 버튼
window.addEventListener('scroll', function() {
    const scrollTop = document.getElementById('scrollTop');
    if (scrollTop) {
        if (window.pageYOffset > 300) {
            scrollTop.style.display = 'block';
        } else {
            scrollTop.style.display = 'none';
        }
    }
});

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 파일 크기 체크
function checkFileSize(input, maxSizeMB = 16) {
    if (input.files && input.files[0]) {
        const fileSize = input.files[0].size / 1024 / 1024; // MB
        if (fileSize > maxSizeMB) {
            showToast(`파일 크기는 ${maxSizeMB}MB를 초과할 수 없습니다.`, 'error');
            input.value = '';
            return false;
        }
    }
    return true;
}

// 날짜 포맷팅
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// LocalStorage 헬퍼
const storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('LocalStorage 저장 실패:', e);
        }
    },
    
    get: function(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('LocalStorage 읽기 실패:', e);
            return null;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('LocalStorage 삭제 실패:', e);
        }
    }
};

// AJAX 요청 헬퍼
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch 오류:', error);
        showToast('서버 요청에 실패했습니다.', 'error');
        throw error;
    }
}

// 텍스트 추출 기능
async function extractText(problemId) {
    const button = event.target;
    const originalText = button.textContent;
    
    try {
        // 버튼 비활성화
        button.disabled = true;
        button.textContent = '⏳ 추출 중...';
        
        // API 호출
        const response = await fetch(`/problems/${problemId}/extract`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 추출된 텍스트를 문제 입력 필드에 표시
            const problemTextarea = document.querySelector('textarea[name="problem_text"]');
            if (problemTextarea) {
                problemTextarea.value = data.text;
                showToast('✅ 텍스트 추출 완료!');
            } else {
                showToast('✅ 텍스트 추출 완료: ' + data.text.substring(0, 50) + '...');
            }
        } else {
            showToast('텍스트 추출에 실패했습니다: ' + (data.error || '알 수 없는 오류'), 'error');
        }
    } catch (error) {
        console.error('추출 오류:', error);
        showToast('텍스트 추출 중 오류가 발생했습니다.', 'error');
    } finally {
        // 버튼 복원
        button.disabled = false;
        button.textContent = originalText;
    }
}

// 초기화
console.log('오답노트 앱 로드 완료');
