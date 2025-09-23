# -*- coding: utf-8 -*-
"""
Structlog 기반 구조화된 로깅 시스템
Context7 2025 모범 사례: 구조화된 로그, 다중 출력, 성능 최적화
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    print("Structlog를 설치하세요: pip install structlog")

# 로그 레벨 매핑
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


class ColorFormatter(logging.Formatter):
    """컬러 포맷터 (콘솔 출력용)"""

    COLORS = {
        'DEBUG': '\033[36m',    # 청록색
        'INFO': '\033[32m',     # 녹색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',    # 빨간색
        'CRITICAL': '\033[35m', # 자홍색
        'RESET': '\033[0m'      # 리셋
    }

    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_structured: bool = True
) -> None:
    """로깅 시스템 초기화"""

    # 기본 로그 파일 설정
    if log_file is None:
        log_file = Path("sales_automation.log")

    # 로그 디렉토리 생성
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 기본 로거 설정
    logging.basicConfig(
        level=LOG_LEVELS.get(log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]
    )

    # 루트 로거 가져오기
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # 파일 핸들러 설정 (회전 로그)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Structlog 설정 (사용 가능한 경우) - Context7 모범 사례
    if STRUCTLOG_AVAILABLE and enable_structured:
        setup_structlog(log_level)

        # ProcessorFormatter를 사용한 콘솔 핸들러 (Structlog 통합)
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            processor_formatter = structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=True),
            )
            console_handler.setFormatter(processor_formatter)
            root_logger.addHandler(console_handler)
    else:
        # Structlog 없을 때 기본 콘솔 핸들러
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            color_formatter = ColorFormatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(color_formatter)
            root_logger.addHandler(console_handler)


def setup_structlog(log_level: str = "INFO") -> None:
    """Structlog 구조화된 로깅 설정"""
    if not STRUCTLOG_AVAILABLE:
        return

    # Context7 모범 사례: 표준 라이브러리 통합을 위한 프로세서 체인
    processors = [
        # 로그 레벨로 필터링 (성능 향상)
        structlog.stdlib.filter_by_level,

        # 로거 이름과 로그 레벨 추가
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,

        # 타임스탬프 추가
        structlog.processors.TimeStamper(fmt="iso"),

        # 위치 인수 포맷팅
        structlog.stdlib.PositionalArgumentsFormatter(),

        # 스택 정보 및 예외 정보
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,

        # 유니코드 디코딩
        structlog.processors.UnicodeDecoder(),

        # 표준 라이브러리 통합용 래퍼 (Context7 권장)
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Structlog 구성
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class SalesAutomationLogger:
    """판매 자동화 전용 로거"""

    def __init__(self, name: str = "SalesAutomation"):
        self.name = name
        if STRUCTLOG_AVAILABLE:
            self.logger = structlog.get_logger(name)
        else:
            self.logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        if STRUCTLOG_AVAILABLE:
            self.logger.debug(message, **kwargs)
        else:
            self.logger.debug(f"{message} - {kwargs}" if kwargs else message)

    def info(self, message: str, **kwargs):
        """정보 로그"""
        if STRUCTLOG_AVAILABLE:
            self.logger.info(message, **kwargs)
        else:
            self.logger.info(f"{message} - {kwargs}" if kwargs else message)

    def warning(self, message: str, **kwargs):
        """경고 로그"""
        if STRUCTLOG_AVAILABLE:
            self.logger.warning(message, **kwargs)
        else:
            self.logger.warning(f"{message} - {kwargs}" if kwargs else message)

    def error(self, message: str, **kwargs):
        """에러 로그"""
        if STRUCTLOG_AVAILABLE:
            self.logger.error(message, **kwargs)
        else:
            self.logger.error(f"{message} - {kwargs}" if kwargs else message)

    def critical(self, message: str, **kwargs):
        """치명적 에러 로그"""
        if STRUCTLOG_AVAILABLE:
            self.logger.critical(message, **kwargs)
        else:
            self.logger.critical(f"{message} - {kwargs}" if kwargs else message)

    def bind(self, **kwargs):
        """컨텍스트 바인딩"""
        if STRUCTLOG_AVAILABLE:
            return self.logger.bind(**kwargs)
        else:
            # Fallback: 기본 로거에서는 kwargs를 무시
            return self

    def with_context(self, **context):
        """컨텍스트와 함께 새 로거 인스턴스 반환"""
        if STRUCTLOG_AVAILABLE:
            new_logger = SalesAutomationLogger(self.name)
            new_logger.logger = self.logger.bind(**context)
            return new_logger
        else:
            return self


def get_logger(name: str = "SalesAutomation") -> SalesAutomationLogger:
    """로거 인스턴스 반환"""
    return SalesAutomationLogger(name)


def log_performance(func):
    """성능 측정 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("Performance")
        start_time = datetime.now()

        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(
                "함수 실행 완료",
                function=func.__name__,
                duration_seconds=duration,
                args_count=len(args),
                kwargs_count=len(kwargs)
            )

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(
                "함수 실행 실패",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=duration
            )
            raise

    return wrapper


def log_file_operation(operation: str, file_path: Path, **extra_context):
    """파일 작업 로그"""
    logger = get_logger("FileOperation")
    logger.info(
        "파일 작업",
        operation=operation,
        file_path=str(file_path),
        file_exists=file_path.exists(),
        file_size=file_path.stat().st_size if file_path.exists() else 0,
        **extra_context
    )


def log_data_processing(operation: str, row_count: int, **extra_context):
    """데이터 처리 로그"""
    logger = get_logger("DataProcessing")
    logger.info(
        "데이터 처리",
        operation=operation,
        row_count=row_count,
        **extra_context
    )


def log_error_with_context(error: Exception, context: Dict[str, Any]):
    """컨텍스트와 함께 에러 로그"""
    logger = get_logger("Error")
    logger.error(
        "에러 발생",
        error_message=str(error),
        error_type=type(error).__name__,
        **context
    )


# 사전 정의된 로거들
file_logger = get_logger("FileHandler")
report_logger = get_logger("ReportGenerator")
ui_logger = get_logger("UI")
ai_logger = get_logger("AI")
api_logger = get_logger("API")


# 편의 함수들
def setup_app_logging():
    """애플리케이션 로깅 초기화"""
    setup_logging(
        log_level="INFO",
        log_file=Path("sales_automation.log"),
        enable_console=True,
        enable_structured=True
    )

    logger = get_logger("System")
    logger.info("로깅 시스템 초기화 완료", structlog_available=STRUCTLOG_AVAILABLE)


def get_log_stats() -> Dict[str, Any]:
    """로그 통계 반환"""
    log_file = Path("sales_automation.log")

    stats = {
        "log_file_exists": log_file.exists(),
        "log_file_size": log_file.stat().st_size if log_file.exists() else 0,
        "structlog_enabled": STRUCTLOG_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

    return stats