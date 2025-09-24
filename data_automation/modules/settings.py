# -*- coding: utf-8 -*-
"""
Pydantic Settings 기반 설정 관리 시스템
Context7 2025 모범 사례 적용: 타입 안전성, 자동 검증, 환경 변수 지원
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """데이터베이스 관련 설정"""
    engine: str = Field(default="pandas", description="데이터 처리 엔진 (pandas/polars)")
    use_polars: bool = Field(default=False, description="Polars 엔진 사용 여부")

    @field_validator('engine')
    @classmethod
    def validate_engine(cls, v):
        allowed_engines = ["pandas", "polars"]
        if v not in allowed_engines:
            raise ValueError(f"엔진은 {allowed_engines} 중 하나여야 합니다")
        return v

    model_config = SettingsConfigDict(env_prefix="DB_")


class FileProcessingSettings(BaseSettings):
    """파일 처리 관련 설정"""
    order_file_password: str = Field(default="1234", description="주문조회 파일 암호")
    max_file_size_mb: int = Field(default=100, description="최대 파일 크기 (MB)")
    supported_extensions: List[str] = Field(
        default=[".xlsx", ".xls"],
        description="지원되는 파일 확장자"
    )
    backup_enabled: bool = Field(default=True, description="백업 기능 활성화")

    @field_validator('max_file_size_mb')
    @classmethod
    def validate_file_size(cls, v):
        if v <= 0 or v > 500:
            raise ValueError("파일 크기는 1MB~500MB 사이여야 합니다")
        return v

    model_config = SettingsConfigDict(env_prefix="FILE_")


class PathSettings(BaseSettings):
    """경로 관련 설정"""
    download_dir: Optional[Path] = Field(default=None, description="다운로드 폴더 경로")
    base_dir: Optional[Path] = Field(default=None, description="기본 작업 디렉토리")
    reports_dir: Optional[Path] = Field(default=None, description="리포트 저장 디렉토리")

    @field_validator('download_dir', 'base_dir', 'reports_dir', mode='before')
    @classmethod
    def validate_path(cls, v):
        if v is None:
            return v
        path_obj = Path(v) if isinstance(v, str) else v
        if not path_obj.exists():
            logger.warning(f"경로가 존재하지 않습니다: {path_obj}")
        return path_obj

    model_config = SettingsConfigDict(env_prefix="PATH_")


class UISettings(BaseSettings):
    """UI 관련 설정"""
    theme: str = Field(default="light", description="UI 테마")
    language: str = Field(default="ko", description="언어 설정")
    window_width: int = Field(default=1200, description="창 너비")
    window_height: int = Field(default=800, description="창 높이")
    enable_animations: bool = Field(default=True, description="애니메이션 활성화")

    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v):
        allowed_themes = ["light", "dark"]
        if v not in allowed_themes:
            raise ValueError(f"테마는 {allowed_themes} 중 하나여야 합니다")
        return v

    @field_validator('window_width', 'window_height')
    @classmethod
    def validate_dimensions(cls, v):
        if v < 400 or v > 4000:
            raise ValueError("창 크기는 400~4000 픽셀 사이여야 합니다")
        return v

    model_config = SettingsConfigDict(env_prefix="UI_")


class AISettings(BaseSettings):
    """AI 기능 관련 설정"""
    enable_ai_features: bool = Field(default=True, description="AI 기능 활성화")
    prediction_model: str = Field(default="linear", description="예측 모델 타입")
    confidence_threshold: float = Field(default=0.8, description="신뢰도 임계값")
    max_predictions: int = Field(default=100, description="최대 예측 수")

    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError("신뢰도는 0.0~1.0 사이여야 합니다")
        return v

    @field_validator('prediction_model')
    @classmethod
    def validate_model(cls, v):
        allowed_models = ["linear", "polynomial", "neural"]
        if v not in allowed_models:
            raise ValueError(f"모델은 {allowed_models} 중 하나여야 합니다")
        return v

    model_config = SettingsConfigDict(env_prefix="AI_")


class RankTrackingSettings(BaseSettings):
    """순위 추적 관련 설정"""
    naver_client_id: Optional[str] = Field(default=None, description="네이버 API 클라이언트 ID")
    naver_client_secret: Optional[str] = Field(default=None, description="네이버 API 클라이언트 Secret")
    api_rate_limit_min: float = Field(default=0.3, description="API 호출 최소 간격 (초)")
    api_rate_limit_max: float = Field(default=0.9, description="API 호출 최대 간격 (초)")
    api_timeout: float = Field(default=10.0, description="API 타임아웃 (초)")
    max_scan_depth: int = Field(default=1000, description="최대 순위 스캔 깊이")
    retry_attempts: int = Field(default=3, description="API 재시도 횟수")

    # 스케줄러 설정
    schedule_interval_minutes: int = Field(default=10, description="순위 확인 간격 (분)")
    max_concurrent_jobs: int = Field(default=3, description="최대 동시 작업 수")
    error_threshold: int = Field(default=5, description="연속 오류 임계값")

    # 데이터베이스 설정
    db_file_name: str = Field(default="rankwatch.db", description="순위 데이터베이스 파일명")
    data_retention_days: int = Field(default=90, description="데이터 보관 기간 (일)")

    @field_validator('api_rate_limit_min', 'api_rate_limit_max')
    @classmethod
    def validate_rate_limits(cls, v):
        if v <= 0 or v > 60:
            raise ValueError("API 제한은 0~60초 사이여야 합니다")
        return v

    @field_validator('max_scan_depth')
    @classmethod
    def validate_scan_depth(cls, v):
        if not (1 <= v <= 1000):
            raise ValueError("스캔 깊이는 1~1000 범위여야 합니다")
        return v

    @field_validator('schedule_interval_minutes')
    @classmethod
    def validate_schedule_interval(cls, v):
        if not (1 <= v <= 1440):  # 1분 ~ 24시간
            raise ValueError("스케줄 간격은 1~1440분 사이여야 합니다")
        return v

    @field_validator('max_concurrent_jobs')
    @classmethod
    def validate_concurrent_jobs(cls, v):
        if not (1 <= v <= 10):
            raise ValueError("동시 작업 수는 1~10개 사이여야 합니다")
        return v

    @field_validator('data_retention_days')
    @classmethod
    def validate_retention_days(cls, v):
        if not (7 <= v <= 365):
            raise ValueError("데이터 보관 기간은 7~365일 사이여야 합니다")
        return v

    model_config = SettingsConfigDict(env_prefix="RANK_")


class ApplicationSettings(BaseSettings):
    """애플리케이션 전체 설정"""

    # 하위 설정 클래스들 (Context7 모범 사례)
    database: DatabaseSettings = DatabaseSettings()
    file_processing: FileProcessingSettings = FileProcessingSettings()
    paths: PathSettings = PathSettings()
    ui: UISettings = UISettings()
    ai: AISettings = AISettings()
    rank_tracking: RankTrackingSettings = RankTrackingSettings()

    # 일반 설정
    debug_mode: bool = Field(default=False, description="디버그 모드")
    log_level: str = Field(default="INFO", description="로그 레벨")
    auto_save: bool = Field(default=True, description="자동 저장")
    check_updates: bool = Field(default=True, description="업데이트 확인")

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"로그 레벨은 {allowed_levels} 중 하나여야 합니다")
        return v.upper()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        nested_model_default_partial_update=True
    )

    def save_to_file(self, file_path: Path):
        """설정을 JSON 파일로 저장"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.model_dump_json(indent=2))
            logger.info(f"설정이 저장되었습니다: {file_path}")
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            raise

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'ApplicationSettings':
        """JSON 파일에서 설정 로드"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                    settings = cls.model_validate_json(data)
                    logger.info(f"설정이 로드되었습니다: {file_path}")
                    return settings
            else:
                logger.info("설정 파일이 없어 기본 설정을 사용합니다")
                return cls()
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            logger.info("기본 설정을 사용합니다")
            return cls()


# 전역 설정 인스턴스
_global_settings: Optional[ApplicationSettings] = None


def get_settings() -> ApplicationSettings:
    """전역 설정 인스턴스 반환 (싱글톤 패턴)"""
    global _global_settings
    if _global_settings is None:
        settings_file = Path("settings.json")
        _global_settings = ApplicationSettings.load_from_file(settings_file)
    return _global_settings


def update_settings(**kwargs) -> ApplicationSettings:
    """설정 업데이트"""
    global _global_settings
    settings = get_settings()

    # 설정 업데이트
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    # 파일에 저장
    settings_file = Path("settings.json")
    settings.save_to_file(settings_file)

    return settings


def reset_settings() -> ApplicationSettings:
    """설정을 기본값으로 리셋"""
    global _global_settings
    _global_settings = ApplicationSettings()
    settings_file = Path("settings.json")
    _global_settings.save_to_file(settings_file)
    return _global_settings


# 편의 함수들
def get_download_dir() -> Optional[Path]:
    """다운로드 디렉토리 반환"""
    return get_settings().paths.download_dir


def set_download_dir(path: Path) -> None:
    """다운로드 디렉토리 설정"""
    settings = get_settings()
    settings.paths.download_dir = path
    settings.save_to_file(Path("settings.json"))


def is_polars_enabled() -> bool:
    """Polars 엔진 사용 여부 반환"""
    return get_settings().database.use_polars


def set_polars_enabled(enabled: bool) -> None:
    """Polars 엔진 사용 설정"""
    settings = get_settings()
    settings.database.use_polars = enabled
    settings.database.engine = "polars" if enabled else "pandas"
    settings.save_to_file(Path("settings.json"))


def get_order_file_password() -> str:
    """주문조회 파일 암호 반환"""
    return get_settings().file_processing.order_file_password


def set_order_file_password(password: str) -> None:
    """주문조회 파일 암호 설정"""
    settings = get_settings()
    settings.file_processing.order_file_password = password
    settings.save_to_file(Path("settings.json"))