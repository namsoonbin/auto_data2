# -*- coding: utf-8 -*-
"""
데이터 처리 엔진 호환성 관리
Pandas/Polars 엔진 전환 지원
"""

import logging
from typing import Literal

# 현재 엔진 상태
_current_engine: Literal["pandas", "polars"] = "pandas"

logger = logging.getLogger(__name__)


def set_engine(use_polars: bool = False) -> None:
    """데이터 처리 엔진 설정"""
    global _current_engine

    if use_polars:
        try:
            import polars as pl
            _current_engine = "polars"
            logger.info("Polars 엔진으로 전환되었습니다")
        except ImportError:
            logger.warning("Polars를 설치하세요: pip install polars")
            _current_engine = "pandas"
    else:
        _current_engine = "pandas"
        logger.info("Pandas 엔진으로 전환되었습니다")


def get_current_engine() -> str:
    """현재 사용 중인 엔진 반환"""
    return _current_engine


def is_polars_available() -> bool:
    """Polars 사용 가능 여부 확인"""
    try:
        import polars as pl
        return True
    except ImportError:
        return False


def get_engine_info() -> dict:
    """엔진 정보 반환"""
    return {
        "current": _current_engine,
        "polars_available": is_polars_available(),
        "pandas_available": True  # pandas는 항상 사용 가능
    }