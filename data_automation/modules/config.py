# -*- coding: utf-8 -*-
import os
import sys
import logging

def get_exe_directory():
    """exe 파일이 위치한 디렉토리 반환 (개발 환경에서는 프로젝트 루트)"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller로 빌드된 경우: exe 파일이 있는 실제 디렉토리
        return os.path.dirname(sys.executable)
    else:
        # 개발 환경: 프로젝트 루트 디렉토리
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 기본 경로 설정 ---
# 개발 환경에서는 프로젝트 루트, exe에서는 exe 파일 위치
BASE_DIR = get_exe_directory()

# --- 폴더 경로 --- 
DOWNLOAD_DIR = None # This will be set by desktop_app.py

def validate_directory(path):
    """디렉토리 경로 검증"""
    if not path or not isinstance(path, str):
        raise ValueError("경로는 비어있지 않은 문자열이어야 합니다.")
    
    # 경로 순회 공격 방지 (Windows와 Unix 모두 고려)
    normalized_path = os.path.normpath(path)
    if '..' in normalized_path:
        raise ValueError("안전하지 않은 경로입니다: 상위 디렉토리 참조 금지")
    
    # Windows의 절대 경로는 허용 (C:\, D:\ 등)
    if os.name == 'nt':  # Windows
        if not (normalized_path[1:3] == ':\\' and normalized_path[0].isalpha()):
            raise ValueError("Windows에서는 절대 경로(드라이브 문자 포함)만 허용됩니다.")
    else:  # Unix/Linux
        if normalized_path.startswith('/'):
            raise ValueError("Unix 시스템에서 루트 경로는 허용되지 않습니다.")
    
    return normalized_path

def get_processing_dir():
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")
    
    validated_path = validate_directory(DOWNLOAD_DIR)
    return os.path.join(validated_path, '작업폴더')

def get_archive_dir():
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")
    
    validated_path = validate_directory(DOWNLOAD_DIR)
    return os.path.join(validated_path, '원본_보관함')

def get_report_archive_dir():
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")
    
    validated_path = validate_directory(DOWNLOAD_DIR)
    return os.path.join(validated_path, '리포트보관함')

MARGIN_FILE = os.path.join(BASE_DIR, '마진정보.xlsx')

# --- 암호 설정 ---
# 주문조회 파일의 기본 암호
ORDER_FILE_PASSWORD = "1234"  # 기본 암호, 필요시 외부에서 변경 가능

# --- 리포트 설정 ---
COLUMNS_TO_KEEP = [
    '상품ID', '상품명', '옵션정보', '실판매개수', '수량', '환불수량', '가구매 개수', '결제금액', '환불금액',
    '판매가', '마진율', '광고비율', '이윤율', '가구매 금액', '가구매 비용',
    '개당 가구매 금액', '개당 가구매 비용', '순매출', '매출', '판매마진', '순이익', '리워드'
]

# --- 데이터 처리 설정 ---
CANCEL_OR_REFUND_STATUSES = ['취소완료', '반품요청', '반품완료', '수거중']

# --- 리포트 분류 시스템 ---
REPORT_STRUCTURE = {
    "individual": "개별리포트/{year}-{month:02d}/{month:02d}-{day:02d}",
    "daily_consolidated": "일간통합리포트",
    "weekly": "주간통합리포트"
}

def get_categorized_report_path(report_type, date_obj, filename):
    """리포트 타입과 날짜에 따른 분류된 경로 반환"""
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")
    
    validated_path = validate_directory(DOWNLOAD_DIR)
    base_report_dir = os.path.join(validated_path, '리포트보관함')
    
    if report_type == "individual":
        sub_path = REPORT_STRUCTURE["individual"].format(
            year=date_obj.year, 
            month=date_obj.month, 
            day=date_obj.day
        )
    else:
        sub_path = REPORT_STRUCTURE[report_type]
    
    categorized_dir = os.path.join(base_report_dir, sub_path)
    
    # 디렉토리가 없으면 생성
    os.makedirs(categorized_dir, exist_ok=True)
    
    return os.path.join(categorized_dir, filename)

def detect_report_type(filename):
    """파일명으로 리포트 타입 감지"""
    if '주간_전체_통합_리포트' in filename or '주간_통합_리포트' in filename:
        return 'weekly'
    elif '전체_통합_리포트' in filename:
        return 'daily_consolidated'
    elif '_통합_리포트_' in filename and not filename.startswith('전체_'):
        return 'individual'
    return 'unknown'

def create_report_folder_structure(date_obj):
    """날짜에 따른 모든 리포트 폴더 구조 사전 생성"""
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")
    
    validated_path = validate_directory(DOWNLOAD_DIR)
    base_report_dir = os.path.join(validated_path, '리포트보관함')
    
    # 개별리포트 폴더 생성
    individual_dir = os.path.join(base_report_dir, REPORT_STRUCTURE["individual"].format(
        year=date_obj.year, month=date_obj.month, day=date_obj.day
    ))
    os.makedirs(individual_dir, exist_ok=True)
    
    # 일간통합리포트 폴더 생성
    daily_dir = os.path.join(base_report_dir, REPORT_STRUCTURE["daily_consolidated"])
    os.makedirs(daily_dir, exist_ok=True)
    
    # 주간통합리포트 폴더 생성
    weekly_dir = os.path.join(base_report_dir, REPORT_STRUCTURE["weekly"])
    os.makedirs(weekly_dir, exist_ok=True)
    
    return {
        'individual': individual_dir,
        'daily_consolidated': daily_dir,
        'weekly': weekly_dir
    }
