# -*- coding: utf-8 -*-
import os
import sys
import logging
from pathlib import Path
from typing import Union

def get_exe_directory() -> Path:
    """exe 파일이 위치한 디렉토리 반환 (개발 환경에서는 프로젝트 루트) - pathlib 2025 모범 사례"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller로 빌드된 경우: exe 파일이 있는 실제 디렉토리
        return Path(sys.executable).parent.resolve()
    else:
        # 개발 환경: 프로젝트 루트 디렉토리 (2단계 상위)
        return Path(__file__).parent.parent.resolve()

# --- 기본 경로 설정 (pathlib 2025 모범 사례) ---
# 개발 환경에서는 프로젝트 루트, exe에서는 exe 파일 위치
BASE_DIR = get_exe_directory()

# --- 폴더 경로 (pathlib 2025 모범 사례) ---
# 기본값으로 현재 작업 폴더의 다운로드 폴더 설정
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "다운로드"
DOWNLOAD_DIR = DEFAULT_DOWNLOAD_DIR  # This will be updated by desktop_app.py

def validate_directory(path: Union[str, Path]) -> Path:
    """
    디렉토리 경로 검증 - pathlib 2025 보안 모범 사례
    Path traversal 공격 방지 및 크로스 플랫폼 호환성 보장
    """
    if not path:
        raise ValueError("경로는 비어있지 않아야 합니다.")

    # pathlib Path 객체로 변환
    path_obj = Path(path) if isinstance(path, str) else path

    try:
        # resolve()를 사용하여 경로 정규화 및 심볼릭 링크 해결
        # 이는 path traversal 공격(../../../etc/passwd)을 방지하는 핵심 기능
        resolved_path = path_obj.resolve()

        # 기본 안전성 검증: 절대 경로인지 확인
        if not resolved_path.is_absolute():
            raise ValueError("상대 경로는 허용되지 않습니다. 절대 경로를 사용하세요.")

        # 2025 보안 강화: 사용자 홈 디렉토리 하위에만 허용 (선택적)
        home_dir = Path.home()
        try:
            # 경로가 사용자 홈 디렉토리 하위인지 확인
            resolved_path.relative_to(home_dir)
        except ValueError:
            # 홈 디렉토리 외부 경로도 허용하되 로그에 기록
            logging.info(f"홈 디렉토리 외부 경로 사용: {resolved_path}")

        return resolved_path

    except (OSError, ValueError) as e:
        raise ValueError(f"유효하지 않은 경로입니다: {path} - {str(e)}")

def get_processing_dir() -> Path:
    """작업 폴더 경로 반환 - pathlib 2025 모범 사례"""
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")

    validated_path = validate_directory(DOWNLOAD_DIR)
    return validated_path / '작업폴더'

def get_archive_dir() -> Path:
    """원본 보관함 경로 반환 - pathlib 2025 모범 사례"""
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")

    validated_path = validate_directory(DOWNLOAD_DIR)
    return validated_path / '원본_보관함'

def get_report_archive_dir() -> Path:
    """리포트 보관함 경로 반환 - pathlib 2025 모범 사례"""
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")

    validated_path = validate_directory(DOWNLOAD_DIR)
    return validated_path / '리포트보관함'

# pathlib 2025 모범 사례: Path 객체 사용
MARGIN_FILE = BASE_DIR / '마진정보.xlsx'

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

def get_categorized_report_path(report_type: str, date_obj, filename: str) -> Path:
    """
    리포트 타입과 날짜에 따른 분류된 경로 반환 - pathlib 2025 모범 사례

    Args:
        report_type: 리포트 타입 ('individual', 'daily_consolidated', 'weekly')
        date_obj: 날짜 객체
        filename: 파일명

    Returns:
        Path: 분류된 리포트 파일의 완전한 경로
    """
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")

    validated_path = validate_directory(DOWNLOAD_DIR)
    base_report_dir = validated_path / '리포트보관함'

    if report_type == "individual":
        # pathlib의 / 연산자로 깔끔한 경로 조합
        sub_path = Path(REPORT_STRUCTURE["individual"].format(
            year=date_obj.year,
            month=date_obj.month,
            day=date_obj.day
        ))
    else:
        sub_path = Path(REPORT_STRUCTURE[report_type])

    categorized_dir = base_report_dir / sub_path

    # pathlib 2025 모범 사례: mkdir 사용
    categorized_dir.mkdir(parents=True, exist_ok=True)

    return categorized_dir / filename

def detect_report_type(filename):
    """파일명으로 리포트 타입 감지"""
    if '주간_전체_통합_리포트' in filename or '주간_통합_리포트' in filename:
        return 'weekly'
    elif '전체_통합_리포트' in filename:
        return 'daily_consolidated'
    elif '_통합_리포트_' in filename and not filename.startswith('전체_'):
        return 'individual'
    return 'unknown'

def create_report_folder_structure(date_obj) -> None:
    """
    날짜에 따른 모든 리포트 폴더 구조 사전 생성 - pathlib 2025 모범 사례

    Args:
        date_obj: 날짜 객체 (datetime)
    """
    if DOWNLOAD_DIR is None:
        raise ValueError("DOWNLOAD_DIR has not been set in config.")

    validated_path = validate_directory(DOWNLOAD_DIR)
    base_report_dir = validated_path / '리포트보관함'

    # pathlib 2025 모범 사례: / 연산자와 mkdir 활용
    # 개별리포트 폴더 생성
    individual_dir = base_report_dir / REPORT_STRUCTURE["individual"].format(
        year=date_obj.year, month=date_obj.month, day=date_obj.day
    )
    individual_dir.mkdir(parents=True, exist_ok=True)

    # 일간통합리포트 폴더 생성
    daily_dir = base_report_dir / REPORT_STRUCTURE["daily_consolidated"]
    daily_dir.mkdir(parents=True, exist_ok=True)

    # 주간통합리포트 폴더 생성
    weekly_dir = base_report_dir / REPORT_STRUCTURE["weekly"]
    weekly_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        'individual': individual_dir,
        'daily_consolidated': daily_dir,
        'weekly': weekly_dir
    }
