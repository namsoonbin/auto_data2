"""
순위 추적 모듈
Context7 모범 사례를 적용한 네이버 쇼핑 순위 추적 시스템

주요 구성요소:
- NaverShopAPI: 네이버 쇼핑 검색 API 클라이언트
- RankCalculator: 순위 계산 및 분석 로직
- RankDatabase: SQLite 기반 데이터 저장
- RankScheduler: 자동화된 순위 모니터링
"""

from .naver_api import NaverShopAPI, APIError, RateLimitError
from .rank_calculator import RankCalculator, RankResult, RankStatus
from .database import RankDatabase, Keyword, TrackingTarget, RankObservation
from .scheduler import RankScheduler, ScheduleConfig

__version__ = "1.0.0"
__author__ = "Context7 Team"

# Context7 모범 사례: 모듈 레벨 상수
DEFAULT_RATE_LIMIT = 0.5  # 초 단위
DEFAULT_TIMEOUT = 10      # 초 단위
DEFAULT_RETRY_COUNT = 3

__all__ = [
    # API 클라이언트
    "NaverShopAPI",
    "APIError",
    "RateLimitError",

    # 순위 계산
    "RankCalculator",
    "RankResult",
    "RankStatus",

    # 데이터베이스
    "RankDatabase",
    "Keyword",
    "TrackingTarget",
    "RankObservation",

    # 스케줄러
    "RankScheduler",
    "ScheduleConfig",

    # 상수
    "DEFAULT_RATE_LIMIT",
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRY_COUNT",
]