"""
통합 순위 엔진
naver-rank-logic.md 기반 완전 재구축된 단일 API 호출 순위 추적 시스템
"""

import re
import logging
import time
import random
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

# 기존 API 클라이언트 재사용
try:
    from ..enhanced_api import NaverShopAPI, SearchParams
except ImportError:
    from ..naver_api import NaverShopAPI
    SearchParams = None


@dataclass
class ProductInfo:
    """완전한 상품 정보"""
    product_id: str
    title: str
    store_name: str
    image_url: str
    link: str
    price_low: str
    price_high: str
    brand: str
    category: str
    product_type: str


@dataclass
class RankSearchResult:
    """통합 순위 검색 결과"""
    success: bool
    rank: Optional[int]
    product_info: Optional[ProductInfo]
    total_scanned: int
    search_keyword: str
    input_url: str
    effective_product_id: str
    search_time: datetime
    error_message: Optional[str] = None


class UnifiedRankEngine:
    """
    통합 순위 엔진 - 단일 API 호출로 모든 정보 획득
    naver-rank-logic.md의 모범 사례를 완전 구현
    """

    # URL 패턴 (naver-rank-logic.md 기준)
    URL_PATTERNS = [
        r"https?://search\.shopping\.naver\.com/catalog/(\d+)",
        r"https?://smartstore\.naver\.com/(?:[^/]+/)?products/(\d+)",
        r"https?://brand\.naver\.com/(?:[^/]+/)?products/(\d+)",
    ]

    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 min_delay: float = 0.3,
                 max_delay: float = 0.9,
                 max_scan_depth: int = 1000):
        """
        통합 순위 엔진 초기화

        Args:
            client_id: 네이버 클라이언트 ID
            client_secret: 네이버 클라이언트 시크릿
            min_delay: 최소 지연 시간 (초)
            max_delay: 최대 지연 시간 (초)
            max_scan_depth: 최대 스캔 깊이 (1~1000)
        """
        self.logger = logging.getLogger(__name__)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_scan_depth = min(max_scan_depth, 1000)

        # API 클라이언트 초기화
        try:
            self.api = NaverShopAPI(
                client_id=client_id,
                client_secret=client_secret
            )
            self.logger.info("통합 순위 엔진 초기화 완료")
        except Exception as e:
            self.logger.error(f"API 클라이언트 초기화 실패: {e}")
            raise

    def extract_product_id(self, url_or_id: str) -> Optional[str]:
        """
        URL 또는 ID에서 상품 ID 추출
        naver-rank-logic.md의 extract_product_id 함수 구현
        """
        if not url_or_id:
            return None

        s = url_or_id.strip()

        # 숫자만 있으면 그대로 반환
        if s.isdigit():
            return s

        # URL 패턴 매칭
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, s)
            if match:
                return match.group(1)

        # 쿼리스트링에서 추출 시도
        try:
            parsed = urlparse(s)
            if parsed.query:
                query_params = dict(
                    kv.split("=", 1) for kv in parsed.query.split("&")
                    if "=" in kv
                )
                for key in ("productId", "nv_mid", "nvMid"):
                    if key in query_params and query_params[key].isdigit():
                        return query_params[key]
        except Exception:
            pass

        return None

    def _jitter_delay(self):
        """API 호출 간 지연 (jitter 적용)"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def search_instant_rank(self, keyword: str, url_or_id: str,
                          sort: str = "sim", include_filter: Optional[str] = None,
                          exclude_types: Optional[List[str]] = None) -> RankSearchResult:
        """
        즉시 순위 검색 - Enhanced_rank.py 로직 통합
        지능적 ID 정규화 + 고급 검색 파라미터 지원

        Args:
            keyword: 검색 키워드
            url_or_id: 상품 URL 또는 ID
            sort: 정렬 방식 (sim, date, asc, dsc)
            include_filter: 포함 필터 ("naverpay")
            exclude_types: 제외 타입 (["used", "rental", "cbshop"])

        Returns:
            RankSearchResult: Enhanced 로직 기반 검색 결과
        """
        search_start_time = datetime.now(timezone(timedelta(hours=9)))

        self.logger.info(f"🔍 Enhanced 순위 검색 시작: '{keyword}' - {url_or_id}")

        try:
            # Enhanced_rank.py의 calculate_rank_with_id_resolution 사용
            from ..enhanced_rank import calculate_rank_with_id_resolution

            enhanced_result = calculate_rank_with_id_resolution(
                api=self.api,
                keyword=keyword,
                user_input=url_or_id,
                sort=sort,
                include_filter=include_filter,
                exclude_types=exclude_types,
                max_depth=self.max_scan_depth
            )

            # Enhanced 결과를 RankSearchResult로 변환
            return self._convert_enhanced_result(enhanced_result, search_start_time)

        except ImportError as e:
            self.logger.warning(f"Enhanced_rank 모듈 로드 실패, 기본 로직 사용: {e}")
            # Enhanced 모듈이 없는 경우 기본 로직으로 폴백
            return self._fallback_search(keyword, url_or_id, sort, search_start_time)
        except Exception as e:
            self.logger.error(f"Enhanced 검색 실패: {e}")
            return RankSearchResult(
                success=False,
                rank=None,
                product_info=None,
                total_scanned=0,
                search_keyword=keyword,
                input_url=url_or_id,
                effective_product_id="",
                search_time=search_start_time,
                error_message=f"검색 중 오류 발생: {str(e)}"
            )

    def _unified_search(self, keyword: str, raw_product_id: str, url_or_id: str,
                       sort: str, search_start_time: datetime) -> RankSearchResult:
        """
        통합 검색 처리 - ID 정규화와 순위 계산을 단일 루프에서 수행
        naver-rank-logic.md의 통합 방식 구현
        """
        effective_product_id = None
        target_rank = None
        matched_product = None
        total_scanned = 0

        # 첫 페이지에서 발견된 ID들 (디버깅용)
        found_product_ids = []

        # 페이지별 검색
        for start in range(1, self.max_scan_depth + 1, 100):
            display = min(100, self.max_scan_depth - start + 1)

            try:
                # API 호출
                self._jitter_delay()

                if SearchParams:  # enhanced_api 사용
                    params = SearchParams(
                        query=keyword,
                        start=start,
                        display=display,
                        sort=sort
                    )
                    response = self.api.search(params)
                else:  # 기존 API 사용
                    response = self.api.get_page(
                        query=keyword,
                        start=start,
                        display=display,
                        sort=sort
                    )

                items = response.get("items", [])
                if not items:
                    break

                self.logger.info(f"  📄 페이지 {start//100 + 1}: {len(items)}개 상품 스캔")

                # 첫 페이지에서 ID 정규화 수행
                if start == 1:
                    effective_product_id = self._resolve_effective_id(
                        items, raw_product_id, found_product_ids
                    )

                    if not effective_product_id:
                        # 해당 상품이 검색 결과에 없음
                        return RankSearchResult(
                            success=False,
                            rank=None,
                            product_info=None,
                            total_scanned=len(items),
                            search_keyword=keyword,
                            input_url=url_or_id,
                            effective_product_id=raw_product_id,
                            search_time=search_start_time,
                            error_message=f"상품이 '{keyword}' 검색 결과에 없습니다. 상위 ID들: {found_product_ids[:5]}"
                        )

                    self.logger.info(f"✅ 정규화된 effective ID: {effective_product_id}")

                # 순위 계산 - effective_id로 매칭
                if effective_product_id:
                    for idx, item in enumerate(items):
                        current_product_id = str(item.get("productId", ""))
                        if current_product_id == effective_product_id:
                            target_rank = total_scanned + idx + 1
                            matched_product = item
                            self.logger.info(f"🎯 순위 발견: {target_rank}위")
                            break

                total_scanned += len(items)

                # 순위를 찾았으면 조기 종료
                if target_rank:
                    break

                # 전체 결과를 다 스캔했으면 종료
                if total_scanned >= response.get("total", 0):
                    break

            except Exception as e:
                self.logger.error(f"API 호출 실패 (start={start}): {e}")
                break

        # 결과 구성
        if target_rank and matched_product:
            product_info = self._extract_product_info(matched_product, effective_product_id)
            return RankSearchResult(
                success=True,
                rank=target_rank,
                product_info=product_info,
                total_scanned=total_scanned,
                search_keyword=keyword,
                input_url=url_or_id,
                effective_product_id=effective_product_id,
                search_time=search_start_time
            )
        else:
            return RankSearchResult(
                success=True,  # 검색은 성공했지만 순위권 밖
                rank=None,
                product_info=None,
                total_scanned=total_scanned,
                search_keyword=keyword,
                input_url=url_or_id,
                effective_product_id=effective_product_id or raw_product_id,
                search_time=search_start_time,
                error_message=f"{total_scanned}위권 밖"
            )

    def _resolve_effective_id(self, items: List[Dict], raw_product_id: str,
                            found_product_ids: List[str]) -> Optional[str]:
        """
        실제 노출되는 effective product ID 결정
        naver-rank-logic.md의 resolve_effective_product_id 로직
        """
        for idx, item in enumerate(items):
            link = item.get("link", "")
            product_id = str(item.get("productId", ""))

            if product_id:
                found_product_ids.append(product_id)

            # 상위 5개 로깅
            if idx < 5:
                link_type = "catalog" if "/catalog/" in link else "products"
                self.logger.info(f"    {idx+1}위: {product_id} ({link_type})")

            # raw ID와 직접 매칭
            if product_id == raw_product_id:
                self.logger.info(f"✅ Raw ID 직접 매칭: {raw_product_id}")
                return product_id

        # 직접 매칭 실패 - 해당 상품이 검색 결과에 없음
        self.logger.warning(f"❌ Raw ID '{raw_product_id}' 미발견")
        return None

    def _convert_enhanced_result(self, enhanced_result: Dict, search_time: datetime) -> RankSearchResult:
        """Enhanced_rank.py 결과를 RankSearchResult로 변환"""

        if not enhanced_result.get("success", False):
            return RankSearchResult(
                success=False,
                rank=None,
                product_info=None,
                total_scanned=enhanced_result.get("scanned", 0),
                search_keyword=enhanced_result.get("keyword", ""),
                input_url=enhanced_result.get("user_input", ""),
                effective_product_id=enhanced_result.get("effective_product_id", ""),
                search_time=search_time,
                error_message=enhanced_result.get("error", "알 수 없는 오류")
            )

        rank = enhanced_result.get("rank")
        found = enhanced_result.get("found", False)

        # 상품 정보 추출
        product_info = None
        if found and enhanced_result.get("matched_item"):
            matched_item = enhanced_result["matched_item"]
            product_info = self._extract_product_info(
                matched_item,
                enhanced_result.get("effective_product_id", "")
            )

        # 순위권 밖인 경우 메시지 설정
        error_message = None
        if not found and rank is None:
            scanned = enhanced_result.get("scanned", 0)
            error_message = f"{scanned}위권 밖"

        return RankSearchResult(
            success=True,
            rank=rank,
            product_info=product_info,
            total_scanned=enhanced_result.get("scanned", 0),
            search_keyword=enhanced_result.get("keyword", ""),
            input_url=enhanced_result.get("user_input", ""),
            effective_product_id=enhanced_result.get("effective_product_id", ""),
            search_time=search_time,
            error_message=error_message
        )

    def _fallback_search(self, keyword: str, url_or_id: str, sort: str,
                        search_start_time: datetime) -> RankSearchResult:
        """Enhanced 로직 실패 시 기본 로직으로 폴백"""

        self.logger.info("기본 검색 로직으로 폴백")

        # URL에서 raw product ID 추출
        raw_product_id = self.extract_product_id(url_or_id)
        if not raw_product_id:
            return RankSearchResult(
                success=False,
                rank=None,
                product_info=None,
                total_scanned=0,
                search_keyword=keyword,
                input_url=url_or_id,
                effective_product_id="",
                search_time=search_start_time,
                error_message="URL에서 상품 ID를 추출할 수 없습니다"
            )

        # 기본 통합 검색 실행
        return self._unified_search(
            keyword=keyword,
            raw_product_id=raw_product_id,
            url_or_id=url_or_id,
            sort=sort,
            search_start_time=search_start_time
        )

    def _extract_product_info(self, item: Dict[str, Any], product_id: str) -> ProductInfo:
        """API 응답에서 완전한 상품 정보 추출"""
        # HTML 태그 제거
        title = item.get("title", "")
        title = re.sub(r"<[^>]+>", "", title)

        return ProductInfo(
            product_id=product_id,
            title=title,
            store_name=item.get("mallName", ""),
            image_url=item.get("image", ""),
            link=item.get("link", ""),
            price_low=str(item.get("lprice", "")),
            price_high=str(item.get("hprice", "")),
            brand=item.get("brand", ""),
            category=item.get("category1", ""),
            product_type=str(item.get("productType", ""))
        )

    def search_batch_ranks(self, keyword: str, url_list: List[str]) -> List[RankSearchResult]:
        """
        배치 순위 검색 - 여러 상품을 한번에 검색
        그룹 관리에서 사용
        """
        results = []
        self.logger.info(f"📦 배치 순위 검색 시작: '{keyword}' - {len(url_list)}개 상품")

        for idx, url_or_id in enumerate(url_list):
            self.logger.info(f"  ({idx+1}/{len(url_list)}) 검색 중: {url_or_id}")
            result = self.search_instant_rank(keyword, url_or_id)
            results.append(result)

            # 배치 처리간 지연
            if idx < len(url_list) - 1:
                self._jitter_delay()

        success_count = len([r for r in results if r.success])
        found_count = len([r for r in results if r.rank is not None])

        self.logger.info(f"📦 배치 검색 완료: {success_count}/{len(url_list)} 성공, {found_count}개 순위 발견")
        return results