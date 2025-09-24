"""
순위 계산 로직
Context7 모범 사례를 적용한 네이버 쇼핑 검색 결과 순위 분석
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum

from .naver_api import NaverShopAPI, SearchParams, SortOrder, ProductItem, APIError


class RankStatus(Enum):
    """순위 상태"""
    FOUND = "found"                    # 순위 발견
    NOT_FOUND = "not_found"           # 순위 미발견 (1000위 밖)
    API_ERROR = "api_error"           # API 오류
    INVALID_PRODUCT = "invalid"       # 유효하지 않은 상품 ID


class RankTrend(Enum):
    """순위 변동 트렌드"""
    UP = "up"                # 순위 상승
    DOWN = "down"            # 순위 하락
    SAME = "same"            # 순위 유지
    NEW_ENTRY = "new_entry"  # 신규 진입
    DROPPED = "dropped"      # 순위권 밖으로 이탈


@dataclass
class RankResult:
    """순위 계산 결과"""
    product_id: str
    keyword: str
    rank: Optional[int]                    # None이면 순위권 밖
    status: RankStatus
    total_scanned: int                     # 스캔한 총 상품 수
    checked_at: datetime
    error_message: Optional[str] = None
    product_info: Optional[ProductItem] = None  # 상품 세부 정보

    @property
    def rank_display(self) -> str:
        """순위 표시용 문자열"""
        if self.rank is None:
            return f"{self.total_scanned}위권 밖"
        return f"{self.rank}위"

    @property
    def is_ranked(self) -> bool:
        """순위권 내 여부"""
        return self.status == RankStatus.FOUND and self.rank is not None


@dataclass
class RankComparison:
    """순위 비교 결과"""
    product_id: str
    keyword: str
    previous_rank: Optional[int]
    current_rank: Optional[int]
    trend: RankTrend
    rank_change: int = 0                   # 양수: 상승, 음수: 하락

    def __post_init__(self):
        """순위 변동 계산"""
        if self.previous_rank is None and self.current_rank is not None:
            self.trend = RankTrend.NEW_ENTRY
            self.rank_change = 0

        elif self.previous_rank is not None and self.current_rank is None:
            self.trend = RankTrend.DROPPED
            self.rank_change = 0

        elif self.previous_rank is None and self.current_rank is None:
            self.trend = RankTrend.SAME
            self.rank_change = 0

        elif self.previous_rank == self.current_rank:
            self.trend = RankTrend.SAME
            self.rank_change = 0

        elif self.current_rank < self.previous_rank:  # 순위는 낮은 수가 좋음
            self.trend = RankTrend.UP
            self.rank_change = self.previous_rank - self.current_rank

        else:
            self.trend = RankTrend.DOWN
            self.rank_change = self.previous_rank - self.current_rank  # 음수


@dataclass
class BatchRankResult:
    """배치 순위 계산 결과"""
    keyword: str
    results: List[RankResult]
    success_count: int = field(init=False)
    error_count: int = field(init=False)
    found_count: int = field(init=False)
    total_time_seconds: float = 0.0

    def __post_init__(self):
        """통계 계산"""
        self.success_count = len([r for r in self.results if r.status != RankStatus.API_ERROR])
        self.error_count = len([r for r in self.results if r.status == RankStatus.API_ERROR])
        self.found_count = len([r for r in self.results if r.status == RankStatus.FOUND])

    @property
    def success_rate(self) -> float:
        """성공률 (0.0 ~ 1.0)"""
        if not self.results:
            return 0.0
        return self.success_count / len(self.results)

    @property
    def found_rate(self) -> float:
        """발견율 (0.0 ~ 1.0)"""
        if not self.results:
            return 0.0
        return self.found_count / len(self.results)


class RankCalculator:
    """
    순위 계산기
    Context7 모범 사례를 적용한 효율적이고 안전한 순위 분석 시스템
    """

    def __init__(
        self,
        api_client: NaverShopAPI,
        max_scan_depth: int = 1000,
        chunk_size: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        순위 계산기 초기화

        Args:
            api_client: 네이버 쇼핑 API 클라이언트
            max_scan_depth: 최대 스캔 깊이 (1-1000)
            chunk_size: 페이지당 검색 수 (1-100)
            logger: 로거 인스턴스
        """
        self.api_client = api_client
        self.max_scan_depth = min(max_scan_depth, 1000)  # 네이버 API 제한
        self.chunk_size = min(chunk_size, 100)           # 네이버 API 제한
        self.logger = logger or logging.getLogger(__name__)

        # Context7 모범 사례: 입력값 검증
        if not (1 <= self.max_scan_depth <= 1000):
            raise ValueError("max_scan_depth는 1-1000 범위여야 합니다")
        if not (1 <= self.chunk_size <= 100):
            raise ValueError("chunk_size는 1-100 범위여야 합니다")

        self.logger.info(f"순위 계산기 초기화: 최대깊이={max_scan_depth}, 청크크기={chunk_size}")

    def calculate_single_rank(
        self,
        keyword: str,
        product_id: str,
        sort_order: SortOrder = SortOrder.ACCURACY
    ) -> RankResult:
        """
        단일 상품 순위 계산

        Args:
            keyword: 검색 키워드
            product_id: 상품 ID
            sort_order: 정렬 방식

        Returns:
            RankResult: 순위 계산 결과
        """
        self.logger.info(f"단일 순위 계산 시작: '{keyword}' - 상품ID {product_id}")

        checked_at = datetime.now(timezone(timedelta(hours=9)))  # KST
        total_scanned = 0

        # Context7 모범 사례: 입력값 정규화
        normalized_product_id = str(product_id).strip()
        if not normalized_product_id:
            return RankResult(
                product_id=product_id,
                keyword=keyword,
                rank=None,
                status=RankStatus.INVALID_PRODUCT,
                total_scanned=0,
                checked_at=checked_at,
                error_message="빈 상품 ID"
            )

        try:
            # 페이지별로 순차 검색
            for start in range(1, self.max_scan_depth + 1, self.chunk_size):
                # 남은 스캔 범위 계산
                remaining = self.max_scan_depth - start + 1
                current_display = min(self.chunk_size, remaining)

                params = SearchParams(
                    query=keyword,
                    start=start,
                    display=current_display,
                    sort=sort_order
                )

                try:
                    response = self.api_client.search_products(params)

                    if not response.items:
                        self.logger.debug(f"페이지 {start}부터 검색 결과 없음")
                        break

                    # 현재 페이지에서 상품 검색
                    for idx, item in enumerate(response.items):
                        current_rank = total_scanned + idx + 1

                        if item.product_id == normalized_product_id:
                            self.logger.info(f"순위 발견: {current_rank}위")
                            return RankResult(
                                product_id=product_id,
                                keyword=keyword,
                                rank=current_rank,
                                status=RankStatus.FOUND,
                                total_scanned=total_scanned + len(response.items),
                                checked_at=checked_at,
                                product_info=item
                            )

                    total_scanned += len(response.items)

                    # 전체 결과 수보다 많이 검색한 경우 중단
                    if response.total <= total_scanned:
                        break

                except APIError as e:
                    self.logger.error(f"API 호출 중 오류: {e}")
                    return RankResult(
                        product_id=product_id,
                        keyword=keyword,
                        rank=None,
                        status=RankStatus.API_ERROR,
                        total_scanned=total_scanned,
                        checked_at=checked_at,
                        error_message=str(e)
                    )

            # 순위권 밖
            self.logger.info(f"순위권 밖: {total_scanned}개 중 미발견")
            return RankResult(
                product_id=product_id,
                keyword=keyword,
                rank=None,
                status=RankStatus.NOT_FOUND,
                total_scanned=total_scanned,
                checked_at=checked_at
            )

        except Exception as e:
            self.logger.error(f"순위 계산 중 예외 발생: {e}")
            return RankResult(
                product_id=product_id,
                keyword=keyword,
                rank=None,
                status=RankStatus.API_ERROR,
                total_scanned=total_scanned,
                checked_at=checked_at,
                error_message=f"계산 오류: {str(e)}"
            )

    def calculate_batch_ranks(
        self,
        keyword: str,
        product_ids: List[str],
        sort_order: SortOrder = SortOrder.ACCURACY,
        early_stop: bool = True
    ) -> BatchRankResult:
        """
        여러 상품 순위 일괄 계산 (최적화된 버전)

        Args:
            keyword: 검색 키워드
            product_ids: 상품 ID 목록
            sort_order: 정렬 방식
            early_stop: 모든 상품 발견 시 조기 종료 여부

        Returns:
            BatchRankResult: 배치 계산 결과
        """
        import time

        start_time = time.time()
        self.logger.info(f"배치 순위 계산 시작: '{keyword}' - {len(product_ids)}개 상품")

        # Context7 모범 사례: 입력값 정규화 및 검증
        normalized_ids = set(str(pid).strip() for pid in product_ids if str(pid).strip())

        if not normalized_ids:
            return BatchRankResult(
                keyword=keyword,
                results=[],
                total_time_seconds=time.time() - start_time
            )

        checked_at = datetime.now(timezone(timedelta(hours=9)))  # KST
        results: Dict[str, RankResult] = {}
        total_scanned = 0
        found_count = 0

        try:
            # 페이지별로 순차 검색 (최적화: 한 번의 검색으로 모든 상품 확인)
            for start in range(1, self.max_scan_depth + 1, self.chunk_size):
                remaining = self.max_scan_depth - start + 1
                current_display = min(self.chunk_size, remaining)

                params = SearchParams(
                    query=keyword,
                    start=start,
                    display=current_display,
                    sort=sort_order
                )

                try:
                    response = self.api_client.search_products(params)

                    if not response.items:
                        self.logger.debug(f"페이지 {start}부터 검색 결과 없음")
                        break

                    # 현재 페이지에서 모든 타겟 상품 확인
                    for idx, item in enumerate(response.items):
                        current_rank = total_scanned + idx + 1

                        if item.product_id in normalized_ids and item.product_id not in results:
                            self.logger.info(f"순위 발견: 상품 {item.product_id} - {current_rank}위")
                            results[item.product_id] = RankResult(
                                product_id=item.product_id,
                                keyword=keyword,
                                rank=current_rank,
                                status=RankStatus.FOUND,
                                total_scanned=0,  # 배치에서는 나중에 일괄 설정
                                checked_at=checked_at,
                                product_info=item
                            )
                            found_count += 1

                    total_scanned += len(response.items)

                    # Context7 모범 사례: 조기 종료 최적화
                    if early_stop and found_count == len(normalized_ids):
                        self.logger.info(f"모든 상품 발견으로 조기 종료: {total_scanned}개 스캔")
                        break

                    # 전체 결과 수보다 많이 검색한 경우 중단
                    if response.total <= total_scanned:
                        break

                except APIError as e:
                    self.logger.error(f"배치 계산 중 API 오류: {e}")
                    # 부분 실패: 이미 찾은 결과는 유지하고 나머지는 에러로 처리
                    break

        except Exception as e:
            self.logger.error(f"배치 계산 중 예외 발생: {e}")

        # 미발견 상품들에 대한 결과 생성
        final_results = []
        for product_id in product_ids:
            normalized_id = str(product_id).strip()

            if normalized_id in results:
                # 발견된 상품: total_scanned 업데이트
                result = results[normalized_id]
                result.total_scanned = total_scanned
                final_results.append(result)
            else:
                # 미발견 상품
                final_results.append(RankResult(
                    product_id=product_id,
                    keyword=keyword,
                    rank=None,
                    status=RankStatus.NOT_FOUND,
                    total_scanned=total_scanned,
                    checked_at=checked_at
                ))

        batch_result = BatchRankResult(
            keyword=keyword,
            results=final_results,
            total_time_seconds=time.time() - start_time
        )

        self.logger.info(
            f"배치 계산 완료: 성공률 {batch_result.success_rate:.1%}, "
            f"발견율 {batch_result.found_rate:.1%}, 소요시간 {batch_result.total_time_seconds:.1f}초"
        )

        return batch_result

    def compare_ranks(
        self,
        previous_results: List[RankResult],
        current_results: List[RankResult]
    ) -> List[RankComparison]:
        """
        순위 비교 분석

        Args:
            previous_results: 이전 순위 결과
            current_results: 현재 순위 결과

        Returns:
            List[RankComparison]: 순위 비교 결과
        """
        self.logger.info("순위 비교 분석 시작")

        # Context7 모범 사례: 효율적인 데이터 구조 사용
        previous_map = {
            (result.keyword, result.product_id): result.rank
            for result in previous_results
        }

        current_map = {
            (result.keyword, result.product_id): result.rank
            for result in current_results
        }

        # 모든 키워드-상품 조합 수집
        all_keys = set(previous_map.keys()) | set(current_map.keys())

        comparisons = []
        for keyword, product_id in all_keys:
            previous_rank = previous_map.get((keyword, product_id))
            current_rank = current_map.get((keyword, product_id))

            comparison = RankComparison(
                product_id=product_id,
                keyword=keyword,
                previous_rank=previous_rank,
                current_rank=current_rank,
                trend=RankTrend.SAME  # __post_init__에서 재계산됨
            )

            comparisons.append(comparison)

        self.logger.info(f"순위 비교 완료: {len(comparisons)}개 항목")
        return comparisons

    def get_rank_insights(self, results: List[RankResult]) -> Dict[str, any]:
        """
        순위 결과 인사이트 생성

        Args:
            results: 순위 결과 목록

        Returns:
            Dict: 인사이트 데이터
        """
        if not results:
            return {"error": "결과가 없습니다"}

        # Context7 모범 사례: 통계 계산
        total_count = len(results)
        found_count = len([r for r in results if r.status == RankStatus.FOUND])
        error_count = len([r for r in results if r.status == RankStatus.API_ERROR])

        ranked_results = [r for r in results if r.rank is not None]
        ranks = [r.rank for r in ranked_results]

        insights = {
            "총_상품수": total_count,
            "순위권_진입수": found_count,
            "에러수": error_count,
            "진입률": round(found_count / total_count * 100, 1) if total_count > 0 else 0,
            "성공률": round((total_count - error_count) / total_count * 100, 1) if total_count > 0 else 0
        }

        if ranks:
            insights.update({
                "최고순위": min(ranks),
                "최저순위": max(ranks),
                "평균순위": round(sum(ranks) / len(ranks), 1),
                "상위10위_개수": len([r for r in ranks if r <= 10]),
                "상위50위_개수": len([r for r in ranks if r <= 50])
            })

        return insights