
# 네이버 쇼핑 **순위 추적** 문제 원인 & 해결 가이드 (URL 입력 → 정규화 → 순위·상품명·스토어명)
_Updated: 2025-09-25 06:38:18

> 이 문서는 현재 코드에서 **순위가 안 나오거나 상품명/스토어명이 비는 문제**를 한 번에 해결하도록,
> **원인 분석 → 패치 코드 → 테스트 방법 → 배치 확장**까지 모두 담은 실전 가이드입니다.

---

## 0) TL;DR (핵심 요약)
- **원인**:  
  1) 키워드 결과가 **카탈로그(가격비교) 엔티티**로 노출되면 API의 `productId`가 **카탈로그 ID**인데, 코드가 **스마트스토어 상품번호**로만 비교 → **불일치**.  
  2) Enhanced 경로가 **순위만** 반환하고 **매칭된 아이템 JSON을 버림** → UI에서 **상품명/스토어명 표시 불가**.  
  3) 빠른 조회에서 **검색 깊이(예: 50)** 가 얕아 상위 51+위인 경우 **미발견**처럼 보일 수 있음.

- **해결**:  
  A) `id_utils.resolve_effective_product_id()`로 **URL→실노출 ID(카탈로그/스토어)** 를 자동 정규화.  
  B) `enhanced_rank`가 **순위 + 매칭 아이템 + 실제 스캔 수**를 **함께 반환**하도록 수정.  
  C) `rank_calculator`가 **ProductItem(title/mall_name)** 을 **채워서** UI로 전달하고, **스캔 수**도 정확히 반영.  
  D) (선택) 빠른 조회 깊이를 200~300으로 일시 상향해 현황 점검.

---

## 1) 동작 흐름 (권장 아키텍처)

입력(URL) → URL/숫자 파싱 → 키워드 Top N 검색 → raw ID가 보이면 raw 유지, 안 보이면 catalog로 폴백  
정규화된 productId → 유기(Organic) 검색 페이지네이션 스캔(≤1000위) → 매칭되면 rank(1-based)와 item(title/mallName/link...) 캡처 → UI로 전달

- **왜 정규화가 필요?**  
  키워드에 따라 동일 제품이 **카탈로그(가격비교)** 카드로 노출되면, 응답의 `productId`가 **카탈로그 ID**입니다. URL 끝 숫자(스토어 상품번호)만 비교하면 **불일치**가 납니다.
- **응답 필드(요약)**: `productId`, `title`, `mallName`, `link`, `image`, `lprice`, `hprice`, `productType`, `brand`, `maker`, `category1..4` 등.

---

## 2) 패치 ① — `id_utils.py` : URL 패턴 보강 + “raw 우선, 카탈로그 폴백”

```python
# id_utils.py
import re
from urllib.parse import urlparse
from typing import Optional
from .enhanced_api import NaverShopAPI, SearchParams

_PATTERNS = [
    r"https?://search\.shopping\.naver\.com/catalog/(\d+)",
    r"https?://smartstore\.naver\.com/(?:[^/]+/)?products/(\d+)",  # {store}/products/{id}, main/products/{id}
    r"https?://brand\.naver\.com/(?:[^/]+/)?products/(\d+)",       # 브랜드 스토어
]

def extract_product_id(token: str) -> Optional[str]:
    s = (token or "").strip()
    if s.isdigit():
        return s
    for pat in _PATTERNS:
        m = re.search(pat, s)
        if m:
            return m.group(1)
    # 쿼리스트링 보조 (nv_mid, productId 등)
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
    """해당 키워드 검색 화면에 실제 노출되는 엔티티(카탈로그/개별상품)의 ID 결정.
    정책: raw ID가 Top N(pages×100)에서 보이면 raw 유지, 없으면 catalog로 폴백.
    """
    raw_id = extract_product_id(user_input)

    # 1) raw ID가 있으면: 상위 영역에서 실제 노출 여부 확인
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
                if raw_id == eff:                 # raw가 실제 노출이면 그대로 사용
                    return eff
                if kind == "catalog":             # 카탈로그가 Top에 보이면 후보로 저장
                    seen_catalog_candidate = eff
        return seen_catalog_candidate or raw_id

    # 2) URL/숫자 추출 실패 시: 상위 결과의 첫 노출 ID 채택
    for p in range(pages):
        resp = api.search(SearchParams(query=keyword, start=1 + p*100, display=100, sort=sort))
        for it in resp.get("items", []):
            m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
            if m:
                return m.group(2)
    return None
```

**포인트**
- `brand.naver.com/.../products/{{id}}` 패턴을 추가하여 **추출 실패**를 줄입니다.
- `pages`를 2로 두면 Top 200까지 확인. 필요시 1~3 사이에서 조정.

---

## 3) 패치 ② — `enhanced_rank.py` : **순위 + 매칭 아이템 + 실제 스캔 수** 반환

```python
# enhanced_rank.py
from typing import Optional, Dict, Any
from .enhanced_api import NaverShopAPI, SearchParams

def get_rank_for_product(api: NaverShopAPI, keyword: str, product_id: str,
                         sort: str = "sim",
                         include_filter: Optional[str] = None,
                         exclude_types: Optional[list[str]] = None,
                         max_depth: int = 1000,
                         page_size: int = 100) -> tuple[Optional[int], Optional[dict], int]:
    """순위, 매칭 아이템(JSON), 실제 스캔 수를 함께 반환."""
    scanned = 0
    for start in range(1, min(max_depth, 1000) + 1, page_size):
        display = min(page_size, max_depth - start + 1)
        params = SearchParams(query=keyword, start=start, display=display, sort=sort,
                              filter=include_filter, exclude=exclude_types)
        resp = api.search(params)
        items = resp.get("items", [])
        for i, it in enumerate(items):
            if str(it.get("productId")) == str(product_id):
                return scanned + i + 1, it, scanned + len(items)
        scanned += len(items)
        if scanned >= resp.get("total", 0):
            break
    return None, None, scanned

def calculate_rank_with_id_resolution(api: NaverShopAPI, keyword: str, user_input: str,
                                      sort: str = "sim",
                                      include_filter: Optional[str] = None,
                                      exclude_types: Optional[list[str]] = None,
                                      max_depth: int = 1000) -> dict:
    from .id_utils import resolve_effective_product_id
    effective_id = resolve_effective_product_id(api, keyword, user_input, pages=2, sort=sort)
    if not effective_id:
        return {"success": False, "error": "ID normalization failed"}

    rank, matched_item, scanned = get_rank_for_product(
        api, keyword, effective_id, sort=sort,
        include_filter=include_filter, exclude_types=exclude_types,
        max_depth=max_depth
    )
    return {
        "success": True,
        "user_input": user_input,
        "effective_product_id": effective_id,
        "keyword": keyword,
        "rank": rank,
        "matched_item": matched_item,   # ★ 추가
        "scanned": scanned,             # ★ 추가
        "sort": sort,
        "filter": include_filter,
        "exclude": exclude_types,
        "max_depth": max_depth,
        "found": rank is not None
    }
```

---

## 4) 패치 ③ — `rank_calculator.py` : **ProductItem 채우기 + 스캔 수 반영**

```python
# rank_calculator.py (Enhanced 경로 성공 분기 예시)
result = calculate_rank_with_id_resolution(...)

if result.get("found") and result.get("rank") is not None:
    matched = result.get("matched_item")
    prod = None
    if matched:
        # ProductItem.from_api_response()가 있다면 사용
        if hasattr(ProductItem, "from_api_response"):
            prod = ProductItem.from_api_response(matched)
        else:
            # 최소 필드 매핑 (정의에 맞춰 필드명 조정)
            prod = ProductItem(
                product_id=str(matched.get("productId")),
                title=(matched.get("title") or ""),
                link=(matched.get("link") or ""),
                mall_name=(matched.get("mallName") or None),
            )

    return RankResult(
        product_id=str(result.get("effective_product_id")),
        keyword=keyword,
        rank=result["rank"],
        status=RankStatus.FOUND,
        total_scanned=int(result.get("scanned") or 0),   # ★ 실제 스캔 수
        checked_at=checked_at,
        product_info=prod                                 # ★ 상품명/스토어명 포함
    )
```

---

## 5) URL 입력 편의 — `calculate_single_rank_by_url()` (있으면 유지)

```python
# rank_calculator.py (클래스 메서드 예시)
from .enhanced_api import NaverShopAPI as EnhancedAPI
from .id_utils import resolve_effective_product_id

def calculate_single_rank_by_url(self, keyword: str, product_url: str,
                                 sort_order: SortOrder = SortOrder.ACCURACY) -> "RankResult":
    sort_map = {SortOrder.ACCURACY:"sim", SortOrder.DATE:"date",
                SortOrder.PRICE_ASC:"asc", SortOrder.PRICE_DESC:"dsc"}
    eapi = EnhancedAPI()  # ENV 필요: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET
    eff = resolve_effective_product_id(eapi, keyword, product_url, pages=2, sort=sort_map.get(sort_order,"sim"))
    if not eff:
        return RankResult(..., status=RankStatus.INVALID_PRODUCT, error_message="URL에서 productId를 결정할 수 없습니다.")
    return self.calculate_single_rank(keyword=keyword, product_id=str(eff), sort_order=sort_order)
```

---

## 6) 배치(여러 URL/키워드) 확장 팁
- **키워드 단위로 묶어** 페이지 스캔을 **공유**하면 API 호출 수를 줄일 수 있음.
- 절차: URL들에서 raw 추출 → 키워드 Top 200 역색인 → raw 매칭/폴백 → 본 스캔(≤1000위) → item 보존.

---

## 7) 테스트 체크리스트
- 같은 키워드로 **Top 100**의 `productId/title/mallName/productType` 로그를 켜서 **카탈로그/개별상품** 노출 여부 확인.  
- URL(스마트스토어/브랜드/카탈로그) 각각 넣어 **정규화 결과** 확인.  
- 빠른 조회(예: 50)와 심층 조회(예: 300)의 결과 차이를 비교.  
- 오류코드(400/403): 파라미터 범위와 API 권한/쿼터 확인.

---

## 8) 한계/주의
- 오픈API 응답에는 **광고 슬롯 없음** → **유기(Organic) 순위**만 계산.
- UI의 “인기순/리뷰순”은 오픈API 정렬(`sim|date|asc|dsc`)과 다름 → **정확도(sim)** 기준이 기본.
- `start ≤ 1000` 제약으로 **1000위 밖**은 확인 불가.

---

## 9) 부록 — 제목 정리 헬퍼

```python
import re, html
def clean_title(s: str) -> str:
    return html.unescape(re.sub(r"</?b>", "", s or "", flags=re.I))
```

**1) 카탈로그(가격비교)로 묶이는 경우**

네이버는 동일 제품을 카탈로그(가격비교) 페이지로 묶어 한 카드에 여러 판매처를 모아 보여줍니다(브랜드/모델 단위 제품 정보, 판매처 영역은 판매자가 임의 편집 불가). 키워드 검색에서 이 카탈로그 카드 하나가 1개 결과로 잡혀요. 
네이버 광고주센터
+1

이때 검색 API의 각 아이템은 카탈로그 자체를 가리키며, productType이 가격비교 계열(1,4,7,10)로 표기됩니다. 추적 가능한 건 카탈로그 카드의 전체 순위뿐입니다. 카탈로그 내부의 ‘내 스토어’ 위치 정보는 응답에 없음. 
NAVER Developers

2) 개별 스마트스토어 상품(카탈로그 비매칭)으로 노출되는 경우

키워드 결과가 개별 상품 카드로 노출되면, 그 결과의 productId가 곧 해당 상품의 ID이고 productType은 “가격비교 비매칭 일반상품(2,5,8,11)” 등으로 나옵니다. 이때는 그 productId로 그대로 순위를 찾으면 끝입니다. 
NAVER Developers

참고: 검색 API 파라미터 제약 — display(최대 100), start(최대 1000), 정렬 sort ∈ {sim,date,asc,dsc}. 결국 1000위까지만 스캔 가능합니다. 
NAVER Developers

“개별 상품 순위”를 정확히 추적하려면 (실무 절차)

대상 파라미터 고정

정렬: 보통 정확도(sim) 기준을 표준으로 삼습니다(다른 정렬을 쓰면 UI/순위 기준이 달라짐).

페이지네이션: display=100으로 두고 start=1,101,201,... 식으로 최대 1000위까지 반복 조회. 
NAVER Developers

URL → 추적대상 ID 정규화

입력이 스마트스토어 상품 URL이면 숫자 ID를 추출합니다.

그 키워드의 상위 100~200개를 먼저 조회해 링크/productId가 catalog/{id}인지 products/{id}인지 확인합니다.

상위 결과에서 내 products/{id}가 실제로 보이면 → 그 **상품 productId**로 순위 검색.

안 보이고 카탈로그 카드만 보이면 → **그 카탈로그 productId**로 “카탈로그 카드” 순위를 따로 기록(= 키워드 결과에서 내 상품이 단독으로 노출되지 않는 상황).

이렇게 해야 카탈로그/개별상품 상황이 바뀌어도 오탐을 줄입니다. (검색 응답에 productId, productType, link, mallName만 있고, 카탈로그 내부 판매처 목록은 없음.) 
NAVER Developers

순위 산출

각 페이지의 items[*].productId를 내 대상 ID와 비교해 일치하는 인덱스 + 누적 스캔 수로 1-based 순위를 계산합니다.

함께 내려오는 title(굵게 태그 포함)·mallName을 정리해서 UI에 표시하세요. 
NAVER Developers

해석 가이드

카탈로그로만 노출되는 키워드는 → “키워드 유기 순위 = 카탈로그 카드 순위”입니다.

개별 상품으로 노출되는 키워드는 → “키워드 유기 순위 = 해당 상품 카드의 순위”입니다.

카탈로그 안 ‘내 스토어’가 몇 번째인지는 검색 API로 측정 불가(응답 스키마에 판매처 리스트가 없음). 그건 카탈로그 상세 페이지의 ‘판매처 정렬(최저가/인기 등)’ 영역 문제이며, 검색 결과 순위와 개념이 다릅니다. 
네이버 광고주센터
+1

자주 헷갈리는 포인트

productType 해석: 문서 표에 “가격비교 상품(1,4,7,10) / 가격비교 비매칭 일반상품(2,5,8,11) / 가격비교 매칭 일반상품(3,6,9,12)” 이 나옵니다. 실무적으로는

가격비교 상품 → 카탈로그 카드 그 자체

비매칭 일반상품 → 개별 상품 카드

매칭 일반상품 → 카탈로그와 연결된 일반상품 유형(결과 UI 동작은 케이스별 차이)
로 이해하고, 랭킹 매칭은 productId 기준으로 처리하세요. 
NAVER Developers

광고 슬롯과의 차이: 검색 결과 페이지에는 광고 모듈이 섞일 수 있으나, 오픈 검색 API 스펙은 검색 아이템 필드(productId 등) 중심이며 광고 슬롯 구조는 명시돼 있지 않습니다. 즉, UI의 광고 순서와 1:1 대응을 전제하면 안 됩니다. 
NAVER Developers

한 줄 정리

카탈로그 카드 순위를 볼 땐 카탈로그 productId,

개별 상품 순위를 볼 땐 상품 productId.

카탈로그 내부에서 내 스토어의 위치는 검색 API로는 측정 불가—그건 카탈로그 상세의 판매처 영역 문제라 다른 채널(파트너/내부 리포트/페이지 분석 등)로 봐야 합니다.