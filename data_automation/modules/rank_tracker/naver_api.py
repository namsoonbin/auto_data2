"""
네이버 쇼핑 검색 API 클라이언트
Context7 모범 사례를 적용한 안전하고 효율적인 API 호출 시스템
"""

import os
import time
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlencode

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Context7 모범 사례: 커스텀 예외 클래스
class APIError(Exception):
    """API 호출 관련 기본 예외"""
    pass

class RateLimitError(APIError):
    """Rate Limit 초과 예외"""
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")

class AuthenticationError(APIError):
    """인증 실패 예외"""
    pass

class QuotaExceededError(APIError):
    """일일 할당량 초과 예외"""
    pass


class SortOrder(Enum):
    """검색 정렬 옵션"""
    ACCURACY = "sim"        # 정확도순 (기본값)
    DATE = "date"          # 날짜순
    PRICE_ASC = "asc"      # 가격 오름차순
    PRICE_DESC = "dsc"     # 가격 내림차순


@dataclass
class SearchParams:
    """네이버 쇼핑 검색 파라미터"""
    query: str
    start: int = 1
    display: int = 100
    sort: SortOrder = SortOrder.ACCURACY

    def __post_init__(self):
        # Context7 모범 사례: 입력값 검증
        if not self.query.strip():
            raise ValueError("검색어는 비어있을 수 없습니다")

        if not (1 <= self.start <= 1000):
            raise ValueError("start는 1-1000 범위여야 합니다")

        if not (1 <= self.display <= 100):
            raise ValueError("display는 1-100 범위여야 합니다")


@dataclass
class ProductItem:
    """네이버 쇼핑 상품 정보"""
    product_id: str
    title: str
    link: str
    image: str
    l_price: str
    h_price: str
    mall_name: str
    product_type: str
    brand: str
    maker: str
    category1: str
    category2: str
    category3: str
    category4: str

    @classmethod
    def from_api_response(cls, item_data: Dict[str, Any]) -> "ProductItem":
        """API 응답 데이터에서 ProductItem 생성"""
        return cls(
            product_id=str(item_data.get("productId", "")),
            title=item_data.get("title", "").replace("<b>", "").replace("</b>", ""),
            link=item_data.get("link", ""),
            image=item_data.get("image", ""),
            l_price=item_data.get("lprice", ""),
            h_price=item_data.get("hprice", ""),
            mall_name=item_data.get("mallName", ""),
            product_type=item_data.get("productType", ""),
            brand=item_data.get("brand", ""),
            maker=item_data.get("maker", ""),
            category1=item_data.get("category1", ""),
            category2=item_data.get("category2", ""),
            category3=item_data.get("category3", ""),
            category4=item_data.get("category4", "")
        )


@dataclass
class SearchResponse:
    """네이버 쇼핑 검색 응답"""
    total: int
    start: int
    display: int
    items: List[ProductItem]
    last_build_date: str

    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any]) -> "SearchResponse":
        """API 응답에서 SearchResponse 생성"""
        items = [
            ProductItem.from_api_response(item)
            for item in response_data.get("items", [])
        ]

        return cls(
            total=response_data.get("total", 0),
            start=response_data.get("start", 1),
            display=response_data.get("display", 0),
            items=items,
            last_build_date=response_data.get("lastBuildDate", "")
        )


class NaverShopAPI:
    """
    네이버 쇼핑 검색 API 클라이언트
    Context7 모범 사례 적용:
    - Rate limiting with jitter
    - Exponential backoff retry
    - Connection pooling
    - Comprehensive error handling
    """

    BASE_URL = "https://openapi.naver.com/v1/search/shop.json"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        min_delay: float = 0.3,
        max_delay: float = 0.9,
        timeout: Tuple[float, float] = (3.05, 10.0),
        max_retries: int = 3,
        backoff_factor: float = 0.3
    ):
        """
        네이버 쇼핑 API 클라이언트 초기화

        Args:
            client_id: 네이버 클라이언트 ID (환경변수에서 자동 로드)
            client_secret: 네이버 클라이언트 Secret (환경변수에서 자동 로드)
            min_delay: 최소 요청 간격 (초)
            max_delay: 최대 요청 간격 (초)
            timeout: (연결 타임아웃, 읽기 타임아웃)
            max_retries: 최대 재시도 횟수
            backoff_factor: 지수 백오프 계수
        """
        # Context7 모범 사례: 환경변수에서 인증정보 로드
        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "네이버 API 인증정보가 필요합니다. "
                "환경변수 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정하거나 "
                "생성자에서 직접 전달하세요."
            )

        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # Context7 모범 사례: requests Session with retry strategy
        self.session = requests.Session()

        # 재시도 전략 설정
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET"},
            raise_on_status=False,
            respect_retry_after_header=True
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 헤더 설정
        self.session.headers.update({
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "User-Agent": "NaverShopRankTracker/1.0",
            "Accept": "application/json"
        })

        self.logger.info("네이버 쇼핑 API 클라이언트 초기화 완료")

    def _apply_rate_limit(self) -> None:
        """Context7 모범 사례: Jitter를 포함한 Rate Limiting"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        self.logger.debug(f"Rate limit 대기: {delay:.2f}초")

    def _handle_response_errors(self, response: requests.Response) -> None:
        """Context7 모범 사례: HTTP 응답 에러 처리"""
        if response.status_code == 401:
            raise AuthenticationError("API 인증에 실패했습니다. 클라이언트 ID/Secret을 확인하세요.")

        elif response.status_code == 429:
            # Rate limit 헤더에서 재시도 시간 추출
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else 60
            raise RateLimitError(retry_after_int)

        elif response.status_code == 403:
            content = response.text.lower()
            if "quota" in content or "limit" in content:
                raise QuotaExceededError("일일 API 호출 한도를 초과했습니다.")
            else:
                raise APIError(f"접근 거부: {response.text}")

        elif response.status_code >= 400:
            raise APIError(f"API 오류 (HTTP {response.status_code}): {response.text}")

    def search_products(self, params: SearchParams) -> SearchResponse:
        """
        상품 검색 실행

        Args:
            params: 검색 파라미터

        Returns:
            SearchResponse: 검색 결과

        Raises:
            APIError: API 호출 실패
            RateLimitError: Rate limit 초과
            AuthenticationError: 인증 실패
            QuotaExceededError: 할당량 초과
        """
        self.logger.info(f"상품 검색 시작: '{params.query}' (start={params.start}, display={params.display})")

        # Context7 모범 사례: Rate limiting 적용
        self._apply_rate_limit()

        # 쿼리 파라미터 구성
        query_params = {
            "query": params.query,
            "start": params.start,
            "display": params.display,
            "sort": params.sort.value
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=query_params,
                timeout=self.timeout
            )

            # 에러 응답 처리
            self._handle_response_errors(response)

            # JSON 파싱
            try:
                response_data = response.json()
            except ValueError as e:
                raise APIError(f"응답 JSON 파싱 실패: {e}")

            # SearchResponse 객체 생성
            search_response = SearchResponse.from_api_response(response_data)

            self.logger.info(
                f"검색 완료: {search_response.total}개 결과 중 {len(search_response.items)}개 조회"
            )

            return search_response

        except requests.exceptions.Timeout:
            raise APIError(f"요청 타임아웃 ({self.timeout}초)")

        except requests.exceptions.ConnectionError:
            raise APIError("네트워크 연결 오류")

        except requests.exceptions.RequestException as e:
            raise APIError(f"HTTP 요청 실패: {e}")

    def search_all_pages(
        self,
        query: str,
        max_results: int = 1000,
        sort: SortOrder = SortOrder.ACCURACY
    ) -> List[ProductItem]:
        """
        모든 페이지를 순회하며 검색 (최대 1000개 제한)

        Args:
            query: 검색어
            max_results: 최대 결과 수 (1-1000)
            sort: 정렬 방식

        Returns:
            List[ProductItem]: 모든 상품 목록
        """
        if not (1 <= max_results <= 1000):
            raise ValueError("max_results는 1-1000 범위여야 합니다")

        all_items = []
        start = 1
        display = 100  # 페이지당 최대 100개

        self.logger.info(f"전체 페이지 검색 시작: '{query}' (최대 {max_results}개)")

        while len(all_items) < max_results and start <= 1000:
            # 남은 개수 계산
            remaining = max_results - len(all_items)
            current_display = min(display, remaining)

            params = SearchParams(
                query=query,
                start=start,
                display=current_display,
                sort=sort
            )

            try:
                response = self.search_products(params)

                if not response.items:
                    self.logger.info("더 이상 검색 결과가 없습니다")
                    break

                all_items.extend(response.items)

                # 전체 결과 수보다 많이 가져온 경우 중단
                if response.total <= len(all_items):
                    break

                start += current_display

            except RateLimitError as e:
                self.logger.warning(f"Rate limit 도달, {e.retry_after}초 대기")
                time.sleep(e.retry_after)
                continue

            except APIError as e:
                self.logger.error(f"검색 중 오류 발생: {e}")
                break

        self.logger.info(f"전체 페이지 검색 완료: {len(all_items)}개 결과")
        return all_items

    def close(self) -> None:
        """Context7 모범 사례: 리소스 정리"""
        if self.session:
            self.session.close()
            self.logger.info("API 클라이언트 세션 종료")

    def __enter__(self):
        """Context Manager 지원"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 지원"""
        self.close()