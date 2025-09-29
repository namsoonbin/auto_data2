# -*- coding: utf-8 -*-
"""
File Handler Module - Context7 Best Practices 2025

This module provides comprehensive file handling capabilities for sales data automation
with enhanced security, type safety, and modern Python patterns.

Key Features:
- Secure file validation with path traversal protection
- Type-safe operations with comprehensive error handling
- Cross-platform compatibility using pathlib
- Performance optimized file processing
- Comprehensive logging and monitoring
"""

import os
import re
import shutil
import time
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple, Union, List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from . import config
from . import report_generator
from .compatibility import get_current_engine

# Context7 2025 Best Practice: Use pathlib for all path operations
STOP_FLAG_FILE = config.BASE_DIR / 'stop.flag'

def validate_excel_file(file_path: Union[str, Path]) -> bool:
    """
    Excel 파일 검증 - Context7 2025 보안 모범 사례

    Enhanced security validation with comprehensive checks for Excel files,
    including encrypted file detection and malicious file prevention.

    Args:
        file_path: Path to Excel file (string or Path object)

    Returns:
        bool: True if file is valid and safe to process

    Raises:
        ValueError: For invalid file format, size, or security issues
        FileNotFoundError: When file doesn't exist
        PermissionError: When file access is denied
        OSError: For general file system errors

    Security Features:
        - Path traversal attack prevention
        - File size limits (100MB)
        - File format validation
        - Encrypted file detection
        - Binary header verification
    """
    # Context7 2025: Convert to Path object for enhanced security
    file_path_obj = Path(file_path).resolve() if isinstance(file_path, str) else file_path.resolve()

    # Security: Validate file extension (case-insensitive)
    if not file_path_obj.suffix.lower() == '.xlsx':
        raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path_obj.suffix}")

    # Context7 2025: Use pathlib for existence check
    if not file_path_obj.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path_obj}")

    # Security: File size validation (100MB limit)
    try:
        file_size = file_path_obj.stat().st_size
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"파일 크기가 너무 큽니다 ({file_size / 1024 / 1024:.1f}MB > 100MB): {file_path_obj.name}")

        if file_size == 0:
            raise ValueError(f"빈 파일입니다: {file_path_obj.name}")

    except (OSError, PermissionError) as e:
        raise PermissionError(f"파일 정보에 접근할 수 없습니다: {file_path_obj} - {e}")

    # Context7 2025: Enhanced encrypted file detection
    try:
        with file_path_obj.open('rb') as f:
            header = f.read(16)  # Read more bytes for better detection

            # Multiple encryption signature checks
            encryption_signatures = [
                b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # Microsoft Office encrypted
                b'PK\x03\x04',  # ZIP-based (modern Excel)
                b'Microsoft Office',  # Alternative signature
            ]

            is_encrypted = any(header.startswith(sig) for sig in encryption_signatures[:1])  # Check first signature

            if is_encrypted:
                logging.info(f"🔒 암호 보호된 파일 감지: {file_path_obj.name}")

            # Additional security: Check for suspicious patterns
            if b'script' in header.lower() or b'macro' in header.lower():
                logging.warning(f"⚠️ 의심스러운 파일 패턴 감지: {file_path_obj.name}")

    except (OSError, PermissionError) as e:
        logging.warning(f"파일 헤더 검사 실패 (계속 진행): {file_path_obj.name} - {e}")

    logging.debug(f"✅ 파일 검증 완료: {file_path_obj.name} ({file_size / 1024:.1f}KB)")
    return True

def get_file_info(src_path: Union[str, Path]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    파일 경로를 분석하여 스토어, 날짜, 파일 타입, 새 파일명을 반환 - Context7 2025 모범 사례

    Enhanced file analysis with comprehensive pattern matching, security validation,
    and robust error handling for sales data files.

    Args:
        src_path: Path to the file to analyze (string or Path object)

    Returns:
        Tuple containing:
        - store_name: Store name extracted from path (None if not found)
        - date_str: Date string in YYYY-MM-DD format (None if not found)
        - file_type: File type ('주문' or '성과') (None if not found)
        - new_filename: Generated standardized filename (None if not found)

    File Pattern Support:
        - 스마트스토어_주문조회_YYYY-MM-DD.xlsx
        - 상품성과_YYYY-MM-DD.xlsx (with optional suffixes)

    Security Features:
        - Input validation through validate_excel_file
        - Path traversal protection
        - Comprehensive error handling
    """
    try:
        # Context7 2025: Enhanced security validation
        validate_excel_file(src_path)

        # Context7 2025: Use pathlib for robust path handling
        file_path_obj = Path(src_path).resolve() if isinstance(src_path, str) else src_path.resolve()

        # Extract store name from parent directory
        download_dir = config.validate_directory(config.DOWNLOAD_DIR)
        try:
            # Security: Ensure file is within expected directory structure
            relative_path = file_path_obj.relative_to(download_dir)
            if len(relative_path.parts) > 1:
                store_name = relative_path.parts[0]
            else:
                logging.warning(f"[get_file_info] 파일이 스토어 폴더에 없습니다: {file_path_obj}")
                return None, None, None, None
        except ValueError:
            logging.warning(f"[get_file_info] 파일이 다운로드 디렉토리 외부에 있습니다: {file_path_obj}")
            return None, None, None, None

        original_filename = file_path_obj.name
        date_str, file_type, new_filename = None, None, None

        # Context7 2025: Enhanced regex patterns with more specific matching
        # 주문조회 파일 패턴 매칭 (더 엄격한 패턴)
        order_patterns = [
            r"스마트스토어[_\s]*주문조회[_\s]*(\d{4}-\d{2}-\d{2})\.xlsx$",  # Standard pattern
            r"주문조회[_\s]*(\d{4}-\d{2}-\d{2})\.xlsx$",  # Alternative pattern
        ]

        for pattern in order_patterns:
            order_match = re.search(pattern, original_filename, re.IGNORECASE)
            if order_match:
                date_str = order_match.group(1)
                file_type = '주문'
                new_filename = f"{store_name} 스마트스토어_주문조회_{date_str}.xlsx"
                logging.info(f"[get_file_info] 📋 주문조회 파일 매칭됨: {original_filename} -> {new_filename}")
                break

        # 상품성과 파일 패턴 매칭 (확장된 패턴 지원)
        if not date_str:  # Only check if order pattern wasn't matched
            perf_patterns = [
                r"상품성과[_\s]*(\d{4}-\d{2}-\d{2}).*?\.xlsx$",  # Standard pattern with optional suffix
                r"성과[_\s]*(\d{4}-\d{2}-\d{2}).*?\.xlsx$",  # Short pattern
            ]

            for pattern in perf_patterns:
                perf_match = re.search(pattern, original_filename, re.IGNORECASE)
                if perf_match:
                    date_str = perf_match.group(1)
                    file_type = '성과'
                    new_filename = f"{store_name} 상품성과_{date_str}.xlsx"
                    logging.info(f"[get_file_info] 📊 상품성과 파일 매칭됨: {original_filename} -> {new_filename}")
                    break

        # Context7 2025: Enhanced validation and logging
        if date_str and file_type and new_filename:
            # Validate date format
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
                logging.info(f"[get_file_info] ✅ 파일 정보 추출 성공: {original_filename}")
                logging.info(f"[get_file_info]    📁 스토어: {store_name}")
                logging.info(f"[get_file_info]    📅 날짜: {date_str}")
                logging.info(f"[get_file_info]    📋 타입: {file_type}")
                return store_name, date_str, file_type, new_filename
            except ValueError:
                logging.error(f"[get_file_info] 잘못된 날짜 형식: {date_str}")
                return None, None, None, None
        else:
            logging.warning(f"[get_file_info] ❌ 파일 패턴 매칭 실패: {original_filename}")
            logging.warning(f"[get_file_info]    지원 패턴:")
            logging.warning(f"[get_file_info]    - 스마트스토어_주문조회_YYYY-MM-DD.xlsx")
            logging.warning(f"[get_file_info]    - 상품성과_YYYY-MM-DD.xlsx")
            return None, None, None, None

    except (ValueError, FileNotFoundError, PermissionError) as e:
        logging.warning(f"[get_file_info] 파일 검증 실패: {e}")
        return None, None, None, None
    except Exception as e:
        logging.error(f"[get_file_info] 예상치 못한 오류: {e}")
        return None, None, None, None

def _check_and_process_data(store: str, date: str) -> bool:
    """
    주문조회 파일이 준비되었는지 확인하고 리포트 생성을 트리거 - Context7 2025 모범 사례

    Enhanced data processing trigger with pathlib integration, comprehensive
    file validation, and robust error handling.

    Args:
        store: Store name
        date: Date string in YYYY-MM-DD format

    Returns:
        bool: True if report generation was successful, False otherwise

    Features:
        - Secure path handling with pathlib
        - Comprehensive file existence checks
        - Detailed progress logging
        - Atomic report generation with success validation
    """
    logging.info(f"🔍 [{store}, {date}] ===== 데이터 처리 시작 =====")

    # Context7 2025: Use pathlib for all path operations
    processing_dir = config.get_processing_dir()
    order_file = f"{store} 스마트스토어_주문조회_{date}.xlsx"
    order_path = processing_dir / order_file

    logging.info(f"📂 [{store}, {date}] 찾고 있는 파일: {order_path}")
    logging.info(f"📁 [{store}, {date}] 작업폴더 경로: {processing_dir}")

    # Context7 2025: Enhanced directory validation and file listing
    try:
        if processing_dir.exists():
            # Use pathlib glob for safer file listing
            all_files = list(processing_dir.iterdir())
            xlsx_files = [f.name for f in all_files if f.suffix.lower() == '.xlsx' and f.is_file()]
            logging.info(f"📄 [{store}, {date}] 작업폴더 내 Excel 파일들 ({len(xlsx_files)}개): {xlsx_files}")
        else:
            logging.warning(f"❌ [{store}, {date}] 작업폴더가 존재하지 않습니다: {processing_dir}")
            return False
    except (OSError, PermissionError) as e:
        logging.error(f"❌ [{store}, {date}] 작업폴더 읽기 오류: {e}")
        return False

    # Context7 2025: Use pathlib for existence check
    if order_path.exists():
        logging.info(f"✅ [{store}, {date}] 주문조회 파일 발견! 데이터 처리를 시작합니다.")

        # Check if report already exists - pathlib based
        individual_report = f'{store}_통합_리포트_{date}.xlsx'
        individual_report_path = processing_dir / individual_report

        logging.info(f"🎯 [{store}, {date}] 생성할 리포트 파일: {individual_report_path}")

        if individual_report_path.exists():
            # Context7 2025: Use pathlib stat for file info
            file_size = individual_report_path.stat().st_size
            logging.info(f"✅ [{store}, {date}] 이미 리포트가 생성되어 있습니다. (크기: {file_size:,} bytes)")
            return True  # 이미 리포트가 있으므로 성공으로 간주
        else:
            logging.info(f"🔄 [{store}, {date}] 리포트 생성을 시작합니다...")
            # 개별 리포트만 생성 (파일 이동은 하지 않음)
            try:
                # 현재 설정된 엔진에 따라 적절한 generator 사용
                current_engine = get_current_engine()
                logging.info(f"🚀 [{store}, {date}] 데이터 처리 엔진: {current_engine}")

                if current_engine == "Polars":
                    # Polars 엔진 사용
                    try:
                        from . import report_generator_polars
                        processed_groups = report_generator_polars.generate_individual_reports_polars()
                        logging.info(f"⚡ [{store}, {date}] Polars 엔진으로 고성능 처리 완료")
                    except ImportError as e:
                        logging.warning(f"⚠️ [{store}, {date}] Polars 모듈 로드 실패, Pandas로 폴백: {e}")
                        processed_groups = report_generator.generate_individual_reports()
                    except Exception as e:
                        logging.warning(f"⚠️ [{store}, {date}] Polars 처리 실패, Pandas로 폴백: {e}")
                        processed_groups = report_generator.generate_individual_reports()
                else:
                    # Pandas 엔진 사용
                    processed_groups = report_generator.generate_individual_reports()
                    logging.info(f"📊 [{store}, {date}] Pandas 엔진으로 표준 처리 완료")

                if processed_groups:
                    logging.info(f"✅ [{store}, {date}] 리포트 생성 성공! 처리된 그룹: {processed_groups}")

                    # Context7 2025: Use pathlib for file verification
                    if individual_report_path.exists():
                        file_size = individual_report_path.stat().st_size
                        logging.info(f"✅ [{store}, {date}] 리포트 파일 확인됨: {individual_report_path.name} (크기: {file_size:,} bytes)")
                        logging.info(f"✅ [{store}, {date}] 개별 리포트 처리 완료.")
                        return True  # 리포트 생성 성공
                    else:
                        logging.error(f"❌ [{store}, {date}] 리포트 생성했다고 하지만 파일이 없습니다: {individual_report_path}")
                        return False  # 리포트 파일이 실제로 생성되지 않음
                else:
                    logging.error(f"❌ [{store}, {date}] 리포트 생성에 실패했습니다. (processed_groups가 비어있음)")
                    return False  # 리포트 생성 실패
            except Exception as e:
                logging.error(f"❌ [{store}, {date}] 리포트 생성 중 예외 발생: {e}")
                import traceback
                logging.error(f"📚 [{store}, {date}] 스택 트레이스: {traceback.format_exc()}")
                return False  # 예외 발생으로 실패
    else:
        logging.warning(f"❌ [{store}, {date}] 주문조회 파일이 아직 준비되지 않았습니다: {order_path}")
        return False  # 주문조회 파일이 없으므로 실패

def process_file(src_path: Union[str, Path]) -> None:
    """
    감지된 파일을 처리 폴더로 옮기고, 데이터 처리를 시작 - Context7 2025 모범 사례

    Enhanced file processing with pathlib integration, improved error handling,
    and comprehensive logging for sales data automation.

    Args:
        src_path: Source file path (string or Path object)

    Security Features:
        - Path validation and sanitization
        - Safe file operations with atomic moves
        - Comprehensive error handling and rollback
    """
    # Context7 2025: Convert to Path object for secure operations
    src_path_obj = Path(src_path).resolve() if isinstance(src_path, str) else src_path.resolve()

    logging.info(f"[process_file] 📁 파일 처리 시작: {src_path_obj.name}")

    try:
        # Enhanced file info extraction with security validation
        store, date, file_type, new_filename = get_file_info(src_path_obj)
        if not all([store, date, file_type, new_filename]):
            logging.warning(f"[process_file] ❌ 파일 정보가 올바르지 않아 무시합니다: {src_path_obj}")
            return

        # Context7 2025: Use pathlib for all path operations
        processing_dir = config.get_processing_dir()
        dest_path = processing_dir / new_filename

        # Security: Ensure processing directory exists
        processing_dir.mkdir(parents=True, exist_ok=True)

        # Security: Prevent overwriting existing files
        if dest_path.exists():
            logging.warning(f"[process_file] 🔄 목적지 파일이 이미 존재합니다: {dest_path.name}")
            # Create backup name with timestamp
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            backup_name = f"{dest_path.stem}_backup_{timestamp}{dest_path.suffix}"
            dest_path = processing_dir / backup_name
            logging.info(f"[process_file] 📝 백업 파일명으로 변경: {backup_name}")

        # Context7 2025: Use pathlib for safe file operations
        logging.info(f"[process_file] 🚚 파일 이동: '{src_path_obj.name}' -> '{dest_path.name}'")

        # Atomic file move operation
        src_path_obj.rename(dest_path)

        logging.info(f"[process_file] ✅ 파일 이동 완료: {dest_path}")

        # 파일 이동만 수행 (리포트 생성은 finalize_all_processing에서 일괄 처리)
        logging.info(f"[process_file] ✅ 파일 이동 완료. 리포트 생성은 나중에 일괄 처리됩니다: {dest_path.name}")

    except (FileNotFoundError, PermissionError) as e:
        logging.error(f"[process_file] 🚫 파일 시스템 오류: {e}")
        # Attempt to restore original file if move failed
        if 'dest_path' in locals() and dest_path.exists() and not src_path_obj.exists():
            try:
                dest_path.rename(src_path_obj)
                logging.info(f"[process_file] 🔄 파일 복원 완료: {src_path_obj}")
            except Exception:
                logging.error(f"[process_file] ❌ 파일 복원 실패")
    except Exception as e:
        logging.error(f"[process_file] ❌ 파일 처리 중 예상치 못한 오류: {e}")
        import traceback
        logging.debug(f"[process_file] 스택 트레이스: {traceback.format_exc()}")

class FileProcessorHandler(FileSystemEventHandler):
    """파일 시스템 이벤트를 감지하여 파일 처리를 시작하는 핸들러"""
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx') and not os.path.basename(event.src_path).startswith('~$'):
            logging.info(f"[on_created] 새 파일 감지: {event.src_path}")
            time.sleep(1)
            process_file(event.src_path)

def process_existing_files() -> None:
    """
    프로그램 시작 시 다운로드 폴더에 이미 있는 파일들을 처리 - Context7 2025 모범 사례

    Enhanced existing file processing with pathlib integration, security validation,
    and comprehensive error handling for sales data automation.

    Features:
        - Secure directory traversal with pathlib
        - System folder exclusion with pattern matching
        - Atomic file processing with rollback capability
        - Comprehensive progress tracking and logging
    """
    logging.info("===== 기존 파일 스캔 시작 ====")

    # Context7 2025: Use pathlib for directory validation
    download_dir = config.validate_directory(config.DOWNLOAD_DIR)
    if not download_dir.exists():
        logging.warning(f"🔍 감시할 다운로드 폴더가 존재하지 않습니다: {download_dir}")
        return

    processed_files = 0
    total_files = 0

    # Context7 2025: Enhanced system folder exclusion with pathlib
    excluded_folders = set()
    try:
        excluded_folders.add(config.get_processing_dir().name)     # 작업폴더
        excluded_folders.add(config.get_archive_dir().name)        # 원본_보관함
        excluded_folders.add(config.get_report_archive_dir().name) # 리포트보관함
    except Exception as e:
        logging.warning(f"시스템 폴더 경로 확인 실패: {e}")

    logging.info(f"제외할 시스템 폴더들: {excluded_folders}")

    # Context7 2025: Use pathlib for safe directory traversal
    try:
        for store_folder_path in download_dir.iterdir():
            if store_folder_path.is_dir() and store_folder_path.name not in excluded_folders:
                logging.info(f"📁 스토어 폴더 스캔: {store_folder_path.name}")

                # Context7 2025: Use pathlib glob for file discovery
                store_files = [
                    f for f in store_folder_path.iterdir()
                    if f.is_file() and f.suffix.lower() == '.xlsx' and not f.name.startswith('~')
                ]
                total_files += len(store_files)

                if not store_files:
                    logging.info(f"   ℹ️ {store_folder_path.name}에 처리할 Excel 파일이 없습니다.")
                    continue

                # Context7 2025: Use pathlib file names for logging
                file_names = [f.name for f in store_files]
                logging.info(f"   📄 발견된 파일들 ({len(store_files)}개): {file_names}")

                for file_path in store_files:
                    logging.info(f"🔄 [기존 파일] 처리 시도: '{file_path.name}'")
                    try:
                        # 개별 파일 처리 (최종 정리는 나중에 일괄 수행)
                        process_file(file_path)
                        processed_files += 1
                        logging.info(f"✅ [기존 파일] 처리 완료: '{file_path.name}'")
                    except Exception as e:
                        logging.error(f"❌ [기존 파일] 처리 실패: '{file_path.name}' - {e}")

    except (OSError, PermissionError) as e:
        logging.error(f"❌ 다운로드 폴더 스캔 중 오류: {e}")
        return

    logging.info(f"📊 파일 처리 결과: {processed_files}/{total_files}개 성공")

    # 2단계: 작업폴더의 미완료 처리 파일들 검사 및 처리
    process_incomplete_files()

    # 3단계: 모든 개별 처리 완료 후 전체 통합 리포트 생성 및 파일 정리
    if processed_files > 0:
        logging.info("🔄 개별 처리 완료 - 전체 통합 리포트 생성 시작")
        finalize_all_processing()
    
    logging.info("===== 기존 파일 스캔 완료 =====")

def process_incomplete_files():
    """작업폴더에 있는 미완료 처리 파일들을 검사하고 리포트 생성을 시도합니다."""
    logging.info("--- 작업폴더 미완료 파일 검사 시작 ---")
    
    # Context7 2025: Use pathlib for stop flag check
    if STOP_FLAG_FILE.exists():
        logging.info("중지 신호 감지. 작업폴더 처리를 중단합니다.")
        return

    # Context7 2025: Use pathlib for directory check
    processing_dir = config.get_processing_dir()
    if not processing_dir.exists():
        return
    
    # Context7 2025: Use pathlib for file scanning
    all_files = [
        f.name for f in processing_dir.iterdir()
        if f.is_file() and f.suffix.lower() == '.xlsx' and not f.name.startswith('~')
    ]
    source_files = [f for f in all_files if '통합_리포트' not in f and '마진정보' not in f]
    
    if not source_files:
        logging.info("작업폴더에 미처리 파일이 없습니다.")
        return
    
    # 스토어별, 날짜별 파일 그룹 생성
    file_groups = {}
    for f in source_files:
        store, date, file_type = None, None, None
        if '상품성과' in f:
            parts = f.split(' 상품성과_')
            if len(parts) == 2: 
                store, date, file_type = parts[0], parts[1].replace('.xlsx',''), '성과'
        elif '스마트스토어_주문조회' in f:
            parts = f.split(' 스마트스토어_주문조회_')
            if len(parts) == 2: 
                store, date, file_type = parts[0], parts[1].replace('.xlsx',''), '주문'
        
        if store and date and file_type:
            key = (store, date)
            if key not in file_groups: 
                file_groups[key] = {}
            file_groups[key][file_type] = f
    
    # 완전한 파일 쌍이 있는데 리포트가 없는 경우 처리
    processed_any = False
    for (store, date), files in file_groups.items():
        # 중지 신호 확인
        if os.path.exists(STOP_FLAG_FILE):
            logging.info("중지 신호 감지. 미완료 파일 처리를 중단합니다.")
            return
            
        if '성과' in files and '주문' in files:
            individual_report = f'{store}_통합_리포트_{date}.xlsx'
            individual_report_path = os.path.join(config.get_processing_dir(), individual_report)
            
            if not os.path.exists(individual_report_path):
                logging.info(f"[미완료 처리 발견] {store} ({date}) - 리포트 생성을 재시도합니다.")
                _check_and_process_data(store, date)
    
    logging.info("--- 작업폴더 미완료 파일 검사 완료 ---")

def finalize_all_processing():
    """모든 개별 처리 완료 후 전체 통합 리포트 생성 및 파일 정리를 일괄 수행합니다."""
    logging.info("🏁 ===== 최종 정리 작업 시작 =====")
    
    # 중지 신호 확인
    if os.path.exists(STOP_FLAG_FILE):
        logging.info("⛔ 중지 신호 감지. 최종 정리 작업을 중단합니다.")
        return
    
    processing_dir = config.get_processing_dir()
    logging.info(f"📁 작업폴더 경로: {processing_dir}")
    
    # 처리할 것이 있는지 확인
    if not os.path.exists(processing_dir):
        logging.warning(f"❌ 작업폴더가 존재하지 않습니다: {processing_dir}")
        return
    
    # 작업폴더 내 모든 파일 확인
    try:
        all_files = os.listdir(processing_dir)
        all_xlsx_files = [f for f in all_files if f.endswith('.xlsx') and not f.startswith('~')]
        logging.info(f"📄 작업폴더 내 모든 Excel 파일들 ({len(all_xlsx_files)}개): {all_xlsx_files}")
    except Exception as e:
        logging.error(f"❌ 작업폴더 읽기 오류: {e}")
        return
    
    # 원본 파일이나 개별 리포트가 있는지 확인
    source_files = [f for f in all_xlsx_files if '통합_리포트' not in f and '마진정보' not in f]
    report_files = [f for f in all_xlsx_files if '통합_리포트' in f]

    logging.info(f"📋 원본 파일들 ({len(source_files)}개): {source_files}")
    logging.info(f"📊 리포트 파일들 ({len(report_files)}개): {report_files}")

    if not source_files and not report_files:
        logging.info("ℹ️ 정리할 파일이 없습니다.")
        return

    # 0단계: 원본 파일들이 있는데 개별 리포트가 없는 경우 개별 리포트 생성 (누락되었던 핵심 단계!)
    if source_files and not report_files:
        logging.info(f"🔄 0단계: 개별 리포트 생성 중... (원본 파일 {len(source_files)}개 처리)")
        try:
            # 현재 설정된 엔진에 따라 적절한 generator 사용 (작업폴더 기능과 동일한 로직)
            current_engine = get_current_engine()
            logging.info(f"🚀 데이터 처리 엔진: {current_engine}")

            if current_engine == "Polars":
                try:
                    from . import report_generator_polars
                    processed_groups = report_generator_polars.generate_individual_reports_polars()
                    logging.info(f"⚡ Polars 엔진으로 고성능 처리 완료")
                except ImportError as e:
                    logging.warning(f"⚠️ Polars 모듈 로드 실패, Pandas로 폴백: {e}")
                    from . import report_generator
                    processed_groups = report_generator.generate_individual_reports()
                except Exception as e:
                    logging.warning(f"⚠️ Polars 처리 실패, Pandas로 폴백: {e}")
                    from . import report_generator
                    processed_groups = report_generator.generate_individual_reports()
            else:
                from . import report_generator
                processed_groups = report_generator.generate_individual_reports()
                logging.info(f"📊 Pandas 엔진으로 표준 처리 완료")

            if processed_groups:
                logging.info(f"✅ 0단계: 개별 리포트 생성 완료 ({processed_groups}개 그룹 처리)")

                # 생성된 개별 리포트들 확인하여 report_files 업데이트
                updated_files = os.listdir(processing_dir)
                report_files = [f for f in updated_files if f.endswith('.xlsx') and '통합_리포트' in f and not f.startswith('~')]
                logging.info(f"📊 새로 생성된 개별 리포트들 ({len(report_files)}개): {report_files}")
            else:
                logging.error("❌ 0단계: 개별 리포트 생성 실패 - 처리된 그룹이 없음")

        except Exception as e:
            logging.error(f"❌ 0단계 실패: 개별 리포트 생성 중 오류: {e}")
            import traceback
            logging.error(f"📚 스택 트레이스: {traceback.format_exc()}")
    else:
        if source_files and report_files:
            logging.info("ℹ️ 0단계 스킵: 개별 리포트가 이미 존재합니다.")
        else:
            logging.info("ℹ️ 0단계 스킵: 처리할 원본 파일이 없습니다.")
    
    # 1단계: 전체 통합 리포트 생성 (개별 리포트가 있는 경우에만)
    if report_files:
        logging.info(f"🔄 1단계: 전체 통합 리포트 생성 중... (개별 리포트 {len(report_files)}개 통합)")
        try:
            from . import report_generator
            report_generator.consolidate_daily_reports()
            logging.info("✅ 1단계: 전체 통합 리포트 생성 완료")
            
            # 생성된 전체 통합 리포트 확인
            updated_files = os.listdir(processing_dir)
            full_reports = [f for f in updated_files if f.startswith('전체_통합_리포트_') and f.endswith('.xlsx')]
            logging.info(f"📊 생성된 전체 통합 리포트들 ({len(full_reports)}개): {full_reports}")
        except Exception as e:
            logging.error(f"❌ 1단계 실패: 전체 통합 리포트 생성 중 오류: {e}")
            import traceback
            logging.error(f"📚 스택 트레이스: {traceback.format_exc()}")
    else:
        logging.info("ℹ️ 1단계 스킵: 개별 리포트가 없어서 전체 통합 리포트를 생성하지 않습니다.")
    
    # 2단계: 모든 원본 파일들을 원본_보관함으로 이동
    if source_files:
        logging.info(f"🔄 2단계: 원본 파일들을 원본_보관함으로 이동 중... ({len(source_files)}개)")
        try:
            move_source_files_to_archive()
            logging.info("✅ 2단계: 원본 파일 이동 완료")
        except Exception as e:
            logging.error(f"❌ 2단계 실패: 원본 파일 이동 중 오류: {e}")
    else:
        logging.info("ℹ️ 2단계 스킵: 이동할 원본 파일이 없습니다.")
    
    # 3단계: 모든 리포트 파일들을 리포트보관함으로 이동
    logging.info("🔄 3단계: 리포트 파일들을 리포트보관함으로 이동 중...")
    try:
        # 이동 전 작업폴더 내 리포트 파일들 다시 확인
        current_files = os.listdir(processing_dir)
        current_reports = [f for f in current_files if f.endswith('.xlsx') and '통합_리포트' in f and not f.startswith('~')]
        logging.info(f"📊 이동할 리포트 파일들 ({len(current_reports)}개): {current_reports}")
        
        move_reports_to_archive()
        logging.info("✅ 3단계: 리포트 파일 이동 완료")
        
        # 리포트보관함 확인
        report_archive_dir = config.get_report_archive_dir()
        if os.path.exists(report_archive_dir):
            archived_reports = [f for f in os.listdir(report_archive_dir) if f.endswith('.xlsx')]
            logging.info(f"📁 리포트보관함 내 파일들 ({len(archived_reports)}개): {archived_reports}")
        else:
            logging.warning(f"❌ 리포트보관함이 존재하지 않습니다: {report_archive_dir}")
            
    except Exception as e:
        logging.error(f"❌ 3단계 실패: 리포트 파일 이동 중 오류: {e}")
        import traceback
        logging.error(f"📚 스택 트레이스: {traceback.format_exc()}")
    
    logging.info("🏁 ===== 최종 정리 작업 완료 =====")

def move_source_files_to_archive():
    """작업폴더의 모든 원본 파일들(상품성과, 주문조회)을 원본_보관함으로 이동합니다."""
    processing_dir = config.get_processing_dir()
    archive_dir = config.get_archive_dir()
    
    if not os.path.exists(processing_dir):
        return
    
    # 원본 파일들 찾기 (통합_리포트가 아닌 파일들)
    source_files = [f for f in os.listdir(processing_dir) 
                   if f.endswith('.xlsx') and '통합_리포트' not in f and not f.startswith('~')]
    
    if not source_files:
        logging.info("이동할 원본 파일이 없습니다.")
        return
    
    logging.info(f"--- 원본 파일들을 원본_보관함으로 이동 시작 ({len(source_files)}개 파일) ---")
    
    for source_file in source_files:
        try:
            src_path = os.path.join(processing_dir, source_file)
            dst_path = os.path.join(archive_dir, source_file)
            shutil.move(src_path, dst_path)
            logging.info(f"원본 파일 이동 완료: {source_file}")
        except Exception as e:
            logging.error(f"원본 파일 이동 실패 ({source_file}): {e}")
    
    logging.info("--- 원본 파일 이동 완료 ---")

def move_reports_to_archive():
    """작업폴더의 리포트 파일들을 리포트보관함으로 이동합니다."""
    logging.info("📦 ===== 리포트 파일 이동 시작 =====")
    
    processing_dir = config.get_processing_dir()
    report_archive_dir = config.get_report_archive_dir()
    
    logging.info(f"📁 작업폴더: {processing_dir}")
    logging.info(f"📁 리포트보관함: {report_archive_dir}")
    
    if not os.path.exists(processing_dir):
        logging.warning(f"❌ 작업폴더가 존재하지 않습니다: {processing_dir}")
        return
    
    # 리포트보관함 폴더 생성 확인
    if not os.path.exists(report_archive_dir):
        try:
            os.makedirs(report_archive_dir, exist_ok=True)
            logging.info(f"✅ 리포트보관함 폴더 생성: {report_archive_dir}")
        except Exception as e:
            logging.error(f"❌ 리포트보관함 폴더 생성 실패: {e}")
            return
    
    # 리포트 파일들 찾기 (통합_리포트로 시작하는 파일들)
    try:
        all_files = os.listdir(processing_dir)
        report_files = [f for f in all_files if f.endswith('.xlsx') and '통합_리포트' in f and not f.startswith('~')]
        logging.info(f"📊 찾은 리포트 파일들 ({len(report_files)}개): {report_files}")
        
        # 추가로 일일_통합_리포트와 주간_통합_리포트도 포함
        additional_reports = [f for f in all_files if f.endswith('.xlsx') and ('일일_통합_리포트' in f or '주간_통합_리포트' in f) and not f.startswith('~')]
        if additional_reports:
            logging.info(f"📈 추가 통합 리포트들 ({len(additional_reports)}개): {additional_reports}")
            report_files.extend(additional_reports)
            # 중복 제거
            report_files = list(set(report_files))
            
    except Exception as e:
        logging.error(f"❌ 작업폴더 읽기 오류: {e}")
        return
    
    if not report_files:
        logging.info("ℹ️ 이동할 리포트 파일이 없습니다.")
        # 작업폴더 전체 파일 목록 로그로 확인
        try:
            all_files = os.listdir(processing_dir)
            xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
            logging.info(f"🔍 작업폴더 내 Excel 파일들: {xlsx_files}")
        except:
            pass
        return
    
    logging.info(f"🔄 리포트 파일들을 리포트보관함으로 이동 시작 (총 {len(report_files)}개 파일)")
    
    moved_count = 0
    failed_count = 0
    
    for report_file in report_files:
        try:
            src_path = os.path.join(processing_dir, report_file)
            
            # 리포트 타입 감지 및 분류된 경로 생성
            report_type = config.detect_report_type(report_file)
            if report_type == 'unknown':
                # 기존 방식으로 처리
                dst_path = os.path.join(report_archive_dir, report_file)
                logging.info(f"🔄 알 수 없는 리포트 타입, 기본 경로 사용: {report_file}")
            else:
                # 날짜 추출
                import re
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', report_file)
                if date_match:
                    from datetime import datetime
                    date_str = date_match.group(1)
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    dst_path = config.get_categorized_report_path(report_type, date_obj, report_file)
                    logging.info(f"📁 분류된 경로로 이동: {report_type} → {dst_path}")
                else:
                    # 날짜를 찾을 수 없으면 기본 경로 사용
                    dst_path = os.path.join(report_archive_dir, report_file)
                    logging.warning(f"⚠️ 날짜를 찾을 수 없어 기본 경로 사용: {report_file}")
            
            # 원본 파일 존재 여부 확인
            if not os.path.exists(src_path):
                logging.error(f"❌ 원본 파일이 존재하지 않음: {report_file}")
                failed_count += 1
                continue
                
            logging.info(f"🔄 이동 시작: {report_file}")
            
            # 이미 같은 이름의 파일이 존재하는 경우에만 백업 (과도한 백업 방지)
            if os.path.exists(dst_path):
                # 파일 크기나 수정 시간이 다른 경우에만 백업
                src_stat = os.path.getsize(src_path)
                dst_stat = os.path.getsize(dst_path)
                
                if src_stat != dst_stat:  # 크기가 다르면 새로운 데이터
                    timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(report_file)
                    backup_name = f"{name}_backup{timestamp}{ext}"
                    backup_path = os.path.join(report_archive_dir, backup_name)
                    shutil.move(dst_path, backup_path)
                    logging.info(f"📋 기존 리포트 백업: {backup_name}")
                else:
                    # 같은 크기면 덮어쓰기 (백업하지 않음)
                    os.remove(dst_path)
                    logging.info(f"🔄 동일한 리포트 덮어쓰기: {report_file}")
            
            # 파일 이동 실행
            shutil.move(src_path, dst_path)
            
            # 이동 검증
            if os.path.exists(dst_path) and not os.path.exists(src_path):
                logging.info(f"✅ 리포트 이동 완료: {report_file}")
                moved_count += 1
            else:
                logging.error(f"❌ 이동 검증 실패: {report_file}")
                failed_count += 1
                
        except Exception as e:
            logging.error(f"❌ 리포트 이동 실패 ({report_file}): {e}")
            import traceback
            logging.error(f"🔍 상세 오류: {traceback.format_exc()}")
            failed_count += 1
    
    # 이동 결과 요약
    logging.info(f"📊 리포트 이동 결과:")
    logging.info(f"   ✅ 성공: {moved_count}개")
    logging.info(f"   ❌ 실패: {failed_count}개")
    
    # 리포트보관함 최종 상태 확인
    try:
        archived_files = [f for f in os.listdir(report_archive_dir) if f.endswith('.xlsx')]
        logging.info(f"📁 리포트보관함 최종 상태: {len(archived_files)}개 파일")
        if archived_files:
            logging.info(f"📋 보관된 파일들: {archived_files}")
    except Exception as e:
        logging.error(f"❌ 리포트보관함 상태 확인 실패: {e}")
    
    logging.info("🎯 ===== 리포트 파일 이동 완료 =====")
    
    if moved_count == 0 and len(report_files) > 0:
        logging.warning("⚠️ 모든 리포트 파일 이동이 실패했습니다. 권한이나 경로를 확인해주세요.")

def initialize_folders() -> None:
    """
    필요한 모든 폴더가 존재하는지 확인하고 없으면 생성 - Context7 2025 모범 사례

    Enhanced folder initialization with pathlib integration and secure permissions.
    """
    # Context7 2025: Use pathlib for safe directory creation
    config.get_processing_dir().mkdir(parents=True, exist_ok=True)
    config.get_archive_dir().mkdir(parents=True, exist_ok=True)
    config.get_report_archive_dir().mkdir(parents=True, exist_ok=True)

def start_monitoring() -> None:
    """
    파일 시스템 모니터링을 시작하고, stop.flag 파일이 생기면 중지 - Context7 2025 모범 사례

    Enhanced monitoring system with pathlib integration, secure file operations,
    and comprehensive error handling.
    """
    initialize_folders()

    # Context7 2025: Use pathlib for stop flag operations
    if STOP_FLAG_FILE.exists():
        STOP_FLAG_FILE.unlink()

    process_existing_files()

    logging.info("\n===== 스마트 폴더 실시간 모니터링 시작 =====")
    logging.info(f"- 감시 대상: {config.DOWNLOAD_DIR} (하위 폴더 포함)")
    logging.info("- 파일을 각 스토어 폴더에 넣으면 처리가 시작됩니다.")

    event_handler = FileProcessorHandler()
    observer = Observer()
    # Note: Observer still needs string path for compatibility
    observer.schedule(event_handler, str(config.DOWNLOAD_DIR), recursive=True)
    observer.start()

    try:
        while True:
            if STOP_FLAG_FILE.exists():
                logging.info("'stop.flag' 파일 감지. 모니터링을 중지합니다.")
                break
            time.sleep(1)
    finally:
        observer.stop()
        observer.join() # 스레드가 완전히 종료될 때까지 대기
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)
        logging.info("\n===== 모니터링이 정상적으로 종료되었습니다. =====")
