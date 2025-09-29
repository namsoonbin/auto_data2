
# 네이버 쇼핑 **키워드 순위 추적** 로직 총정리 (카탈로그/스마트스토어 정규화 · API 파라미터 · 코드)

> 목적: **특정 키워드**에서 **내 상품의 유기(Organic) 순위**를 빠르고 정확하게 구한다.  
> 핵심: 화면에 노출되는 **엔티티(productId)** 를 먼저 **자동 정규화**한 뒤, **검색 API**로 상위 *최대 1000위*까지 순회하여 **랭크**를 계산한다.  
> (최신 문서 기준: 검색 API 쇼핑은 비로그인 방식, `shop.json` 사용, `display≤100`, `start≤1000`, `sort=sim|date|asc|dsc`, `filter`, `exclude` 지원) citeturn1view0

---

## 1) 먼저 개념 정리 — **내가 맞춰야 하는 ID는 `productId`**

- 네이버 쇼핑 검색 API 응답에는 개별 결과가 `items[]`로 오고, 그 안에 **`productId`(네이버 쇼핑의 상품 ID)** 가 있다. 같은 응답에 `title`, `link`, `mallName`, `brand`, `category1..4` 도 포함. citeturn1view0  
- **중요:** 화면 노출이 **카탈로그(가격비교)** 인지 **스마트스토어 개별상품**인지에 따라, 결과의 `link`가  
  - `…/catalog/{{id}}` **또는** `…/main/products/{{id}}` 형태로 온다. 이 중 `{{id}}`를 추적해야 한다. (카탈로그/채널 전시 개념은 공식 도움말/커머스 API 문서로 확인 가능) citeturn2search5turn2search13

> 결론: **URL 끝 숫자**만 맹신하지 말고, **현재 그 키워드에서 실제로 노출되는 엔티티의 ID(=productId)** 를 기준으로 순위를 계산해야 한다.

---

## 2) 검색 API 사용 조건(요약)

- **엔드포인트**: `GET https://openapi.naver.com/v1/search/shop.json` (HTTPS, 비로그인 방식 — 헤더에 Client ID/Secret) citeturn1view0  
- **파라미터**:  
  - `query`(필수), `display` ≤ 100, `start` ≤ 1000, `sort` ∈ {`sim`,`date`,`asc`,`dsc`} citeturn1view0  
  - **포함/제외**: `filter=naverpay`, `exclude=used:rental:cbshop` 조합 가능 (UI 조건 맞추기용) citeturn1view0  
- **호출한도**: **25,000회/일** (Client ID 기준 합산) citeturn1view0

---

## 3) 전체 로직 흐름 (요약 다이어그램)

1. **입력**: `keyword`, `user_input`(스마트스토어/카탈로그 URL 또는 숫자), 선택 옵션(`sort`, `filter`, `exclude`).  
2. **정규화**: `user_input`에서 ID를 추출하거나(가능하면 즉시),  
   같은 키워드의 **상위 1~2페이지**를 조회해 **실제 노출 엔티티의 ID**(catalog or products)를 **자동 매핑**.  
3. **랭킹 스캔**: `start=1, display=100`부터 최대 **1000위**까지 페이지네이션, `items[i].productId == target_id`를 찾으면  
   **rank = 누적스캔개수 + i + 1** 로 반환(1-based).  
4. **조기종료**: 찾으면 즉시 종료, or 더 이상 결과 없으면 종료.

---

## 4) 코드 (드롭인 유틸)
아래 3개 블록을 모듈로 추가하면, **URL→productId 정규화 + 랭킹 계산**을 바로 붙일 수 있다.
- `api.py` : 검색 API 클라이언트
- `id_utils.py` : URL/힌트 기반으로 **실노출 ID** 자동 정규화
- `rank.py` : 정규화된 `productId`로 **랭킹 계산**

> `requests`와 `urllib3` 재시도 어댑터로 **429/5xx**를 안전하게 처리한다(`Retry-After` 존중).

### 4.1 `api.py` — Naver 쇼핑 검색 API 클라이언트
```python
# api.py
from dataclasses import dataclass
from typing import Optional, List
import os, time, random, requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

BASE = "https://openapi.naver.com/v1/search/shop.json"

@dataclass
class SearchParams:
    query: str
    start: int = 1
    display: int = 100
    sort: str = "sim"                 # sim|date|asc|dsc
    filter: Optional[str] = None      # 'naverpay'만 허용
    exclude: Optional[List[str]] = None  # ['used','rental','cbshop'] 조합

    def validate(self):
        if not self.query or not self.query.strip():
            raise ValueError("query is required")
        if not (1 <= self.start <= 1000):
            raise ValueError("start must be 1..1000")
        if not (1 <= self.display <= 100):
            raise ValueError("display must be 1..100")
        if self.sort not in ("sim","date","asc","dsc"):
            raise ValueError("sort must be one of sim|date|asc|dsc")
        if self.filter not in (None, "naverpay"):
            raise ValueError("filter must be None or 'naverpay'")
        if self.exclude:
            allowed = {"used","rental","cbshop"}
            bad = set(self.exclude) - allowed
            if bad:
                raise ValueError(f"exclude supports only {allowed}: {bad}")

class NaverShopAPI:
    def __init__(self, min_delay=0.2, max_delay=0.8, timeout=10, max_retries=5, backoff_factor=0.3):
        if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
            raise RuntimeError("Set NAVER_CLIENT_ID / NAVER_CLIENT_SECRET in env")
        self.s = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429,500,502,503,504],
            allowed_methods=frozenset(["GET"]),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retry))
        self.headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            "Accept": "application/json",
            "User-Agent": "RankWatch/1.0",
        }
        self.min_delay, self.max_delay, self.timeout = min_delay, max_delay, timeout

    def _jitter(self):
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def search(self, p: SearchParams) -> dict:
        p.validate()
        q = {
            "query": p.query,
            "start": p.start,
            "display": p.display,
            "sort": p.sort,
        }
        if p.filter:
            q["filter"] = p.filter
        if p.exclude:
            q["exclude"] = ":".join(p.exclude)
        self._jitter()
        r = self.s.get(BASE, headers=self.headers, params=q, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
```

### 4.2 `id_utils.py` — URL/힌트로 **실노출 ID** 정규화
```python
# id_utils.py
import re
from urllib.parse import urlparse
from typing import Optional
from api import NaverShopAPI, SearchParams

_PATTERNS = [
    r"https?://search\.shopping\.naver\.com/catalog/(\d+)",
    r"https?://smartstore\.naver\.com/(?:[^/]+/)?products/(\d+)",  # {store}/products/{id} 또는 main/products/{id}
]

def extract_product_id(token: str) -> Optional[str]:
    """URL 또는 숫자 문자열에서 productId 후보를 뽑는다 (빠른 경로)."""
    s = token.strip()
    if s.isdigit():
        return s
    for pat in _PATTERNS:
        m = re.search(pat, s)
        if m:
            return m.group(1)
    # 쿼리스트링 보조 파싱 (nv_mid, productId 등)
    try:
        qs = dict(kv.split("=",1) for kv in urlparse(s).query.split("&") if "=" in kv)
        for k in ("productId","nv_mid","nvMid"):
            if k in qs and qs[k].isdigit():
                return qs[k]
    except Exception:
        pass
    return None

def resolve_effective_product_id(api: NaverShopAPI, keyword: str, user_input: str,
                                 pages:int=2, sort:str="sim") -> Optional[str]:
    """키워드 상에서 실제 노출되는 엔티티의 ID(카탈로그/스마트스토어)를 자동 선택.
    - 1) URL/숫자에서 곧장 추출되면 그대로 반환
    - 2) 상위 n페이지(기본 2)에서 'catalog/####'가 먼저 보이면 그 카탈로그ID를 채택
       (Top 영역이 카탈로그 노출이면 그 ID로 추적해야 순위가 정확)
    """
    raw_id = extract_product_id(user_input)
    # 1) 빠른 경로: 이미 숫자면 OK
    if raw_id:
        # 그래도 실노출이 카탈로그라면 카탈로그 ID로 교체
        for p in range(pages):
            resp = api.search(SearchParams(query=keyword, start=1+p*100, display=100, sort=sort))
            for it in resp.get("items", []):
                m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
                if not m: 
                    continue
                eff = m.group(2)
                if raw_id == eff:
                    return eff
                if "catalog" in it.get("link",""):
                    return eff
        return raw_id

    # 2) URL/숫자로 못 뽑았으면 상위 n페이지에서 링크로 결정
    for p in range(pages):
        resp = api.search(SearchParams(query=keyword, start=1+p*100, display=100, sort=sort))
        for it in resp.get("items", []):
            m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
            if m:
                return m.group(2)
    return None
```

### 4.3 `rank.py` — 정규화된 ID로 **랭크 계산**
```python
# rank.py
from typing import Optional
from api import NaverShopAPI, SearchParams

def get_rank_for_product(api: NaverShopAPI, keyword: str, product_id: str,
                         sort:str="sim", include_filter:Optional[str]=None,
                         exclude_types:Optional[list[str]]=None,
                         max_depth:int=1000, page_size:int=100) -> Optional[int]:
    """정확도순(sim) 등 지정 기준으로 최대 1000위까지 스캔하여 랭크 반환 (1위=1).
       못 찾으면 None. 광고는 응답에 포함되지 않으므로 유기(Organic) 순위만 계산됨.
    """
    scanned = 0
    for start in range(1, min(max_depth,1000)+1, page_size):
        display = min(page_size, max_depth - start + 1)
        params = SearchParams(query=keyword, start=start, display=display, sort=sort,
                              filter=include_filter, exclude=exclude_types)
        resp = api.search(params)
        items = resp.get("items", [])
        for i, it in enumerate(items):
            if str(it.get("productId")) == str(product_id):
                return scanned + i + 1
        scanned += len(items)
        total = resp.get("total", 0)
        if scanned >= total:
            break
    return None
```

---

## 5) 사용 예시

```python
from api import NaverShopAPI
from id_utils import resolve_effective_product_id, extract_product_id
from rank import get_rank_for_product

api = NaverShopAPI()

keyword = "무선 청소기"

# 사용자가 입력한 값 (스마트스토어 URL / 카탈로그 URL / 숫자 모두 허용)
user_input = "https://smartstore.naver.com/main/products/7058693395"

# 1) 실제 노출되는 엔티티 ID(카탈로그 or 스마트스토어)로 정규화
pid = resolve_effective_product_id(api, keyword, user_input, pages=2, sort="sim")
if not pid:
    raise RuntimeError("추적 대상 productId를 결정할 수 없습니다. (키워드/입력값 확인)")

# 2) 유기 순위 계산 (정확도순, 네이버페이만, 중고/직구 제외 예시)
rank = get_rank_for_product(
    api, keyword, pid,
    sort="sim",
    include_filter="naverpay",
    exclude_types=["used","cbshop"]
)
print("순위:", rank)   # 예: 7 → 7위
```

---

## 6) 자주 묻는 질문 (FAQ)

**Q. 왜 *스마트스토어 URL 끝 숫자*로는 못 잡을 때가 있나요?**  
A. 그 키워드에서 **카탈로그(가격비교)로 노출**되면, 검색 API가 반환하는 엔티티는 **카탈로그 ID** 입니다. 이때는 스마트스토어 채널상품번호 대신 **카탈로그 ID**로 추적해야 순위가 맞습니다. 위의 `resolve_effective_product_id()`가 이 상황을 자동 보정해 줍니다. (카탈로그 개념/연동은 공식 도움말·커머스 API 문서를 참고) citeturn2search5turn2search13

**Q. 화면 순서와 API 순서가 다른데요?**  
A. API는 `sort=sim|date|asc|dsc`만 지원합니다. UI의 “인기순/리뷰순”은 API 옵션에 없습니다. 따라서 **`sim(정확도)`** 기준 순위가 기본이며, 필요 시 `date/asc/dsc`로 테스트하세요. citeturn1view0

**Q. 상위 1000위 밖은 어떻게 하나요?**  
A. 검색 API 제약(`start≤1000`) 때문에 **1000위 밖은 확인할 수 없습니다**. 이 한계는 문서에 명시되어 있습니다. citeturn1view0

**Q. 광고 슬롯은 포함되나요?**  
A. **아니요.** 검색 오픈API 응답은 광고 필드가 없고, **유기 결과(items)**만 반환합니다. 따라서 이 스크립트는 **유기 순위**만 계산합니다. citeturn1view0

---

## 7) 체크리스트 (실전)

- [ ] **키/권한**: 개발자센터 앱 등록 + 검색 API 권한 On, 헤더에 ID/Secret 포함 (비로그인 오픈API) citeturn1view0  
- [ ] **정렬/필터/제외**: `sort`, `filter=naverpay`, `exclude=used:cbshop:rental` 필요 시 적용 citeturn1view0  
- [ ] **정규화**: URL → 숫자 추출이 안 되거나, 카탈로그 노출 이슈가 있으면 `resolve_effective_product_id()`로 자동 보정  
- [ ] **호출한도**: **25,000회/일** — 스케줄 시 지터·캐시·중복 억제 필수 citeturn1view0

---

## 8) 참고(공식 문서)

- **검색 > 쇼핑 API** (요청 URL/파라미터/응답 스키마/제한/에러) citeturn1view0  
- **네이버쇼핑 ‘제품 카탈로그’ 개념** (도움말) citeturn2search5  
- **커머스 API 토론 — 카탈로그 연결 개념** citeturn2search13

— Generated 2025-09-25 01:47:58
