
# 네이버 쇼핑 **개별상품 vs 카탈로그(가격비교)** 순위 추적 — 실무 구현서
_Updated: 2025-09-26 04:27:39

> 목표: **상품 URL을 입력**하면 키워드 검색 결과에서 실제 노출되는 엔티티(개별상품 _products/{id}_ 또는 카탈로그 _catalog/{id}_)로 **자동 정규화**하고, **유기(광고 제외) 순위 + 상품명 + 스토어명**을 정확히 산출해 UI에 표기한다.

---

## 1) 개념 정리 (왜 로직이 갈리나?)

- **카탈로그(가격비교) 카드**는 하나의 **제품 엔티티**이며, 키워드 결과에서 이 카드 **1개가 1위/2위…로 집계**됩니다.  
  → 따라서 **카탈로그 카드의 순위**를 추적할 때는 **카탈로그 `productId`**로 매칭해야 합니다.

- **개별 스마트스토어 상품 카드**(가격비교 비매칭 등)는 그 **상품 자체가 1개 결과**입니다.  
  → 따라서 **개별 상품의 순위**는 **그 상품의 `productId`**로 매칭하면 됩니다.

- 반면, **카탈로그 카드 내부에서 내 스토어가 몇 번째 판매처인지**(오퍼 순서)는 **오픈 검색 API로는 알 수 없음**. (API 응답엔 판매처 리스트가 없음)

> 구현의 핵심은 “**URL → 실제 노출 ID로 정규화**” 입니다. 같은 키워드라도 노출 형태에 따라 ID가 **`products/{id}` (개별)** 또는 **`catalog/{id}` (카탈로그)**로 달라지므로, **정규화 없이 스토어 상품번호만 비교하면 미스매칭**이 납니다.

---

## 2) 구현 스펙(요약)

- **API**: `GET https://openapi.naver.com/v1/search/shop.json`  
  - `display ≤ 100`, `start ≤ 1000`, `sort ∈ {sim,date,asc,dsc}`  
  - `filter`(예: `naverpay`), `exclude`(예: `used:cbshop:rental`) 지원  
  - 응답 `items[]` 주요 필드: `productId`, `title`(굵게 태그 포함), `mallName`, `link`, `image`, `lprice`, `hprice`, `productType`, `brand`, `maker`, `category1..4`  
- **계산 기준**: 오픈API **유기(광고 제외)** 결과만 대상으로 **1~1000위**까지 페이지네이션 스캔.  
- **UI 데이터**: 순위가 매칭된 `item`에서 `title`과 `mallName`을 바로 사용(제목은 `<b>` 제거).

---

## 3) 코드 ① — `id_utils.py` (URL 패턴 + 정규화)

```python
# id_utils.py
import re
from urllib.parse import urlparse
from typing import Optional, Tuple
from .enhanced_api import NaverShopAPI, SearchParams

_PATTERNS = [
    r"https?://search\.shopping\.naver\.com/catalog/(\d+)",
    r"https?://smartstore\.naver\.com/(?:[^/]+/)?products/(\d+)",
    r"https?://brand\.naver\.com/(?:[^/]+/)?products/(\d+)",
]

def extract_product_id(token: str) -> Optional[str]:
    s = (token or "").strip()
    if s.isdigit():
        return s
    for pat in _PATTERNS:
        m = re.search(pat, s)
        if m:
            return m.group(1)
    # 쿼리스트링 보조 (productId, nv_mid 등)
    try:
        qs = dict(kv.split("=",1) for kv in urlparse(s).query.split("&") if "=" in kv)
        for k in ("productId","nv_mid","nvMid"):
            if k in qs and qs[k].isdigit():
                return qs[k]
    except Exception:
        pass
    return None

def resolve_effective_product_id(api: NaverShopAPI, keyword: str, user_input: str,
                                 pages: int = 2, sort: str = "sim") -> Optional[str]:
    """키워드 검색 상위 N(pages×100)에서 **실제 노출되는 엔티티**의 ID를 결정.
    정책: raw ID가 Top 영역에서 보이면 raw 유지, 안 보이면 catalog로 폴백.
    """
    raw_id = extract_product_id(user_input)
    if raw_id:
        seen_catalog_candidate = None
        for p in range(pages):
            resp = api.search(SearchParams(query=keyword, start=1 + p*100, display=100, sort=sort))
            for it in resp.get("items", []):
                m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
                if not m:
                    continue
                eff = m.group(2)
                kind = m.group(1)
                if raw_id == eff:         # raw가 실제 노출이면 그대로 사용
                    return eff
                if kind == "catalog":     # 카탈로그가 Top에서 보이면 후보
                    seen_catalog_candidate = eff
        return seen_catalog_candidate or raw_id

    # URL/숫자로 못 뽑혔으면 상위 결과의 첫 노출 ID 채택
    for p in range(pages):
        resp = api.search(SearchParams(query=keyword, start=1 + p*100, display=100, sort=sort))
        for it in resp.get("items", []):
            m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
            if m:
                return m.group(2)
    return None
```

---

## 4) 코드 ② — `enhanced_rank.py` (순위 + 아이템 + 스캔수)

```python
# enhanced_rank.py
from typing import Optional, Dict, Any
from .enhanced_api import NaverShopAPI, SearchParams

def get_rank_and_item_for_product(api: NaverShopAPI, keyword: str, product_id: str,
                                  sort: str = "sim",
                                  include_filter: Optional[str] = None,
                                  exclude_types: Optional[list[str]] = None,
                                  max_depth: int = 1000,
                                  page_size: int = 100) -> Dict[str, Any]:
    """순위(1-based), 매칭 아이템(JSON), 실제 스캔 수를 함께 반환."""
    scanned = 0
    for start in range(1, min(max_depth, 1000) + 1, page_size):
        display = min(page_size, max_depth - start + 1)
        params = SearchParams(query=keyword, start=start, display=display, sort=sort,
                              filter=include_filter, exclude=exclude_types)
        resp = api.search(params)
        items = resp.get("items", [])
        for i, it in enumerate(items):
            if str(it.get("productId")) == str(product_id):
                return {"rank": scanned + i + 1, "item": it, "scanned": scanned + len(items)}
        scanned += len(items)
        if scanned >= resp.get("total", 0):
            break
    return {"rank": None, "item": None, "scanned": scanned}

def calculate_rank_with_id_resolution(api: NaverShopAPI, keyword: str, user_input: str,
                                      sort: str = "sim",
                                      include_filter: Optional[str] = None,
                                      exclude_types: Optional[list[str]] = None,
                                      max_depth: int = 1000) -> dict:
    from .id_utils import resolve_effective_product_id
    effective_id = resolve_effective_product_id(api, keyword, user_input, pages=2, sort=sort)
    if not effective_id:
        return {"success": False, "error": "ID normalization failed"}

    hit = get_rank_and_item_for_product(api, keyword, effective_id, sort=sort,
                                        include_filter=include_filter, exclude=exclude_types,
                                        max_depth=max_depth)
    return {
        "success": True,
        "user_input": user_input,
        "effective_product_id": effective_id,
        "keyword": keyword,
        "rank": hit["rank"],
        "matched_item": hit["item"],
        "scanned": hit["scanned"],
        "sort": sort,
        "filter": include_filter,
        "exclude": exclude_types,
        "max_depth": max_depth,
        "found": hit["rank"] is not None,
    }
```

---

## 5) 코드 ③ — `rank_calculator.py` (상품명/스토어명 채우기)

```python
# rank_calculator.py (핵심 분기만 예시)
from .naver_api import ProductItem, SortOrder, SearchError, RateLimitError
from .enhanced_rank import calculate_rank_with_id_resolution

def _to_sort_str(sort_order: SortOrder) -> str:
    return {
        SortOrder.ACCURACY: "sim",
        SortOrder.DATE: "date",
        SortOrder.PRICE_ASC: "asc",
        SortOrder.PRICE_DESC: "dsc",
    }.get(sort_order, "sim")

def calculate_single_rank(self, keyword: str, product_id: str,
                          sort_order: SortOrder = SortOrder.ACCURACY) -> "RankResult":
    checked_at = datetime.now(timezone(timedelta(hours=9)))  # KST
    result = calculate_rank_with_id_resolution(
        api=self._enhanced_api,
        keyword=keyword,
        user_input=product_id,      # URL 또는 숫자 모두 허용
        sort=_to_sort_str(sort_order),
        include_filter=None,
        exclude_types=None,
        max_depth=self.max_scan_depth
    )
    if result.get("found") and result.get("rank") is not None:
        prod = None
        it = result.get("matched_item")
        if it:
            if hasattr(ProductItem, "from_api_response"):
                prod = ProductItem.from_api_response(it)
            else:
                prod = ProductItem(
                    product_id=str(it.get("productId")),
                    title=(it.get("title") or ""),
                    link=(it.get("link") or ""),
                    mall_name=(it.get("mallName") or None),
                )
        return RankResult(
            product_id=str(result.get("effective_product_id") or product_id),
            keyword=keyword,
            rank=int(result["rank"]),
            status=RankStatus.FOUND,
            total_scanned=int(result.get("scanned") or 0),
            checked_at=checked_at,
            product_info=prod
        )
    else:
        return RankResult(
            product_id=product_id,
            keyword=keyword,
            rank=None,
            status=RankStatus.NOT_FOUND,
            total_scanned=int(result.get("scanned") or self.max_scan_depth),
            checked_at=checked_at,
            error_message=result.get("error")
        )

# (선택) URL 편의 함수
def calculate_single_rank_by_url(self, keyword: str, product_url: str,
                                 sort_order: SortOrder = SortOrder.ACCURACY) -> "RankResult":
    return self.calculate_single_rank(keyword=keyword, product_id=product_url, sort_order=sort_order)
```

---

## 6) 사용 예시

```python
calc = RankCalculator(api_client=naver_api_client)  # 기존 생성 방식
res = calc.calculate_single_rank_by_url(
    keyword="무선 청소기",
    product_url="https://smartstore.naver.com/main/products/7058693395"
)
if res.is_ranked:
    print(f"[{res.rank}위] {res.product_info.title} · {res.product_info.mall_name}")
else:
    print(f"미발견 (스캔: {res.total_scanned}) - {res.error_message or ''}")
```

---

## 7) 디버깅 포인트

- **Top 100 샘플 로그**: `items[*].productId / productType / mallName / link`를 잠시 찍어 **카탈로그/개별상품** 노출 여부 확인.  
- **정규화 실패**: URL 패턴(`smartstore`, `brand`, `catalog`)·쿼리스트링(`productId`, `nv_mid`) 확인.  
- **403**: 애플리케이션의 **API 권한(검색 API)** 체크.  
- **정렬/페이징**: `sort=sim`, `display=100`, `start=1..1000` 범위 준수.

---

## 8) 한계/주의

- 오픈API 응답에는 **광고 슬롯이 미포함** → **유기 순위만** 계산.  
- UI의 “인기순/리뷰순” 등은 오픈API 정렬(`sim|date|asc|dsc`)과 다릅니다.  
- **1000위 초과**는 확인 불가(`start ≤ 1000`).

---

## 9) 참고 링크

- 네이버 개발자센터 — **검색 > 쇼핑 API(Shop)**  
  https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md

- 네이버 개발자센터 — **API 공통 가이드 / 오픈API 종류**  
  https://developers.naver.com/docs/common/openapiguide/

- (개념) 네이버 통합 광고주센터 도움말 — **카탈로그/가격비교**  
  https://ads.naver.com/help/search?searchType=TAG&searchValue=%EC%B9%B4%ED%83%88%EB%A1%9C%EA%B7%B8
