# -*- coding: utf-8 -*-
"""
성능 모니터링 유틸리티
"""
import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def monitor_performance(threshold_ms: float = 500):
    """
    API 엔드포인트 성능 모니터링 데코레이터

    Args:
        threshold_ms: 경고를 발생시킬 임계값 (밀리초)
                     이 시간을 초과하면 WARNING 레벨로 로깅

    Usage:
        @router.get("/metrics")
        @monitor_performance(threshold_ms=1000)
        async def get_metrics(...):
            ...

    Logs:
        - INFO: 모든 요청의 실행 시간
        - WARNING: threshold를 초과한 느린 쿼리
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                # 파라미터에서 주요 필터 정보 추출
                filter_info = []
                if 'start_date' in kwargs and kwargs['start_date']:
                    filter_info.append(f"start_date={kwargs['start_date']}")
                if 'end_date' in kwargs and kwargs['end_date']:
                    filter_info.append(f"end_date={kwargs['end_date']}")
                if 'product' in kwargs and kwargs['product']:
                    filter_info.append(f"product={kwargs['product']}")
                if 'limit' in kwargs and kwargs['limit']:
                    filter_info.append(f"limit={kwargs['limit']}")

                filter_str = f" [{', '.join(filter_info)}]" if filter_info else ""

                if elapsed_ms > threshold_ms:
                    logger.warning(
                        f"⚠️  SLOW QUERY: {func.__name__} took {elapsed_ms:.2f}ms{filter_str}"
                    )
                else:
                    logger.info(
                        f"✓ {func.__name__} completed in {elapsed_ms:.2f}ms{filter_str}"
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if elapsed_ms > threshold_ms:
                    logger.warning(
                        f"⚠️  SLOW QUERY: {func.__name__} took {elapsed_ms:.2f}ms"
                    )
                else:
                    logger.info(
                        f"✓ {func.__name__} completed in {elapsed_ms:.2f}ms"
                    )

        # async 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_query_stats(query, description: str = "Query"):
    """
    SQLAlchemy 쿼리 통계 로깅

    Args:
        query: SQLAlchemy Query 객체
        description: 쿼리 설명

    Example:
        query = db.query(IntegratedRecord).filter(...)
        log_query_stats(query, "IntegratedRecord 조회")
        records = query.all()
    """
    try:
        # 쿼리를 문자열로 변환 (실제 SQL 확인용)
        sql_str = str(query.statement.compile(
            compile_kwargs={"literal_binds": True}
        ))

        logger.debug(f"📊 {description}:")
        logger.debug(f"   SQL: {sql_str[:200]}...")  # 처음 200자만

    except Exception as e:
        logger.debug(f"Could not log query stats: {e}")


class PerformanceTracker:
    """
    요청 내 여러 작업의 성능을 추적하는 컨텍스트 매니저

    Usage:
        tracker = PerformanceTracker()

        with tracker.track("데이터 조회"):
            records = db.query(...).all()

        with tracker.track("집계 계산"):
            result = calculate_metrics(records)

        tracker.log_summary()  # 전체 요약 로깅
    """

    def __init__(self):
        self.timings = []
        self.current_name = None
        self.current_start = None

    def track(self, name: str):
        """작업 추적 시작"""
        self.current_name = name
        return self

    def __enter__(self):
        self.current_start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.perf_counter() - self.current_start) * 1000
        self.timings.append((self.current_name, elapsed_ms))
        logger.debug(f"  ⏱️  {self.current_name}: {elapsed_ms:.2f}ms")
        return False

    def log_summary(self):
        """전체 작업 요약 로깅"""
        if not self.timings:
            return

        total_ms = sum(t[1] for t in self.timings)

        logger.info(f"📈 Performance Summary (Total: {total_ms:.2f}ms):")
        for name, ms in self.timings:
            percentage = (ms / total_ms * 100) if total_ms > 0 else 0
            logger.info(f"   • {name}: {ms:.2f}ms ({percentage:.1f}%)")

    def get_total_time(self) -> float:
        """총 실행 시간 반환 (밀리초)"""
        return sum(t[1] for t in self.timings)


# 전역 성능 설정
PERFORMANCE_LOGGING_ENABLED = True

def enable_performance_logging():
    """성능 로깅 활성화"""
    global PERFORMANCE_LOGGING_ENABLED
    PERFORMANCE_LOGGING_ENABLED = True
    logger.info("Performance logging enabled")


def disable_performance_logging():
    """성능 로깅 비활성화"""
    global PERFORMANCE_LOGGING_ENABLED
    PERFORMANCE_LOGGING_ENABLED = False
    logger.info("Performance logging disabled")
