
# 네이버 쇼핑 **키워드 순위 추적** _URL 입력 → (카탈로그/스토어 자동 정규화) → 순위 + 상품명 + 스토어명_

> 당신이 원하는 동작에 맞춰, **상품 URL만 넣어도** 실제 검색 화면에서 노출되는 **엔티티의 `productId`**(카탈로그 or 개별상품)로 자동 정규화하고, **유기(광고 제외) 순위 + 상품명 + 스토어명**을 반환하도록 최소 수정 예시를 정리했습니다.  
> 아래 2가지만 적용하면 됩니다: **① `id_utils.py` 보강**, **② `rank_calculator.py`에 `calculate_single_rank_by_url()` 추가**.  
> (파라미터/응답 스키마/제한은 네이버 공식 문서 기준: `shop.json`, `display≤100`, `start≤1000`, `sort=sim|date|asc|dsc`, `filter`, `exclude`, 응답 필드 `productId/title/link/image/lprice/hprice/mallName/productType/brand/maker/category1..4` 등.) citeturn1view0

---

## 왜 이 변경이 필요한가? (요약)
- 쇼핑 검색 API는 키워드 결과에서 **실제 노출 엔티티**의 `productId`를 반환합니다. 키워드에 따라 **카탈로그(가격비교)** 로 노출되면 `catalog/{{id}}`의 ID가, **개별 스마트스토어 상품**으로 노출되면 `products/{{id}}`의 ID가 결과에 담깁니다.  
- 따라서 **URL 끝 숫자(스토어 상품번호)를 그대로 비교**하면 카탈로그 노출 키워드에서 **불일치(미발견)** 이 납니다.  
- 해결: **URL → (상위 N결과 기준) 실노출 ID로 정규화** → 그 ID로 순위 매칭. 그러면 **카탈로그/비카탈로그 모두** 정상 매칭됩니다.  
  (정렬/페이징/필터 제약은 공식 문서에 명시되어 있습니다.) citeturn1view0

---

# ① `id_utils.py` (드롭인 교체)
- **브랜드 스토어 URL 패턴** 추가 (`brand.naver.com/.../products/{{id}}`)  
- **정규화 정책 강화**:  
  1) **raw ID 우선** — 상위 N(=pages×100)에서 **raw가 실제로 보이면 그대로 유지**  
  2) **카탈로그 폴백** — raw가 안 보이고 카탈로그만 보이면 그 **catalog ID로 교체**  
  3) URL/숫자에서 못 뽑혔으면 상위 N의 첫 결과 ID 채택

```python
# id_utils.py
import re
from urllib.parse import urlparse
from typing import Optional
from .enhanced_api import NaverShopAPI, SearchParams

_PATTERNS = [
    r"https?://search\.shopping\.naver\.com/catalog/(\d+)",
    r"https?://smartstore\.naver\.com/(?:[^/]+/)?products/(\d+)",  # {{store}}/products/{{id}}, main/products/{{id}}
    r"https?://brand\.naver\.com/(?:[^/]+/)?products/(\d+)",       # 브랜드 스토어 보강
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
    """실제 '검색 화면'에 노출되는 엔티티의 ID(카탈로그/스마트스토어)를 결정.
    정책: raw ID가 Top N(=pages*100)에서 보이면 raw 유지, 없으면 catalog로 폴백.
    """
    raw_id = extract_product_id(user_input)

    # 1) raw ID가 있다면: 우선 Top 영역에서 실제로 보이는지 확인
    if raw_id:
        seen_catalog_candidate = None
        for p in range(pages):
            resp = api.search(SearchParams(query=keyword, start=1 + p*100, display=100, sort=sort))
            for it in resp.get("items", []):
                m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
                if not m:
                    continue
                eff = m.group(2)
                if raw_id == eff:                 # raw가 실제 노출이면 그대로 사용
                    return eff
                if "catalog" in m.group(1):       # 카탈로그가 Top에 보이면 후보로 기억
                    seen_catalog_candidate = eff
        # Top에서 raw가 안 보였고 카탈로그가 보였으면 그 ID로 폴백
        return seen_catalog_candidate or raw_id

    # 2) URL/숫자로 못 뽑혔으면 상위 n페이지에서 첫 노출 항목의 ID 채택
    for p in range(pages):
        resp = api.search(SearchParams(query=keyword, start=1 + p*100, display=100, sort=sort))
        for it in resp.get("items", []):
            m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
            if m:
                return m.group(2)
    return None
```

---

# ② `rank_calculator.py`에 **URL 버전** 추가
- 기존 `calculate_single_rank()`는 **상품 ID**를 입력으로 받습니다.  
- 여기에 **URL을 받아서 → (정규화) → 기존 메서드 호출**하는 **`calculate_single_rank_by_url()`** 을 추가합니다.  
- 이 메서드는 **정규화에 `enhanced_api.NaverShopAPI`** 를 사용하므로, **환경변수**(`X-Naver-Client-Id/Secret`에 해당하는 `NAVER_CLIENT_ID/SECRET`)가 설정되어 있어야 합니다. citeturn1view0

```python
# rank_calculator.py (발췌: 클래스 내부에 아래 메서드 추가)
from .id_utils import resolve_effective_product_id
from .enhanced_api import NaverShopAPI as EnhancedAPI

def calculate_single_rank_by_url(
        self,
        keyword: str,
        product_url: str,
        sort_order: SortOrder = SortOrder.ACCURACY
    ) -> "RankResult":
    """상품 **URL**을 넣어서 유기 순위를 계산 (상품명/스토어명 포함).
    내부에서 URL→실노출 productId로 정규화한 뒤 기존 calculate_single_rank()를 호출합니다.
    """
    # 정렬 매핑: enum → 문자열 (enhanced_api용)
    sort_map = {
        SortOrder.ACCURACY: "sim",
        SortOrder.DATE: "date",
        SortOrder.PRICE_ASC: "asc",
        SortOrder.PRICE_DESC: "dsc",
    }

    # 1) 정규화용 임시 API 클라이언트 (비로그인 헤더 방식)
    eapi = EnhancedAPI()  # ENV: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 필요

    effective_id = resolve_effective_product_id(
        api=eapi,
        keyword=keyword,
        user_input=product_url,
        pages=2,
        sort=sort_map.get(sort_order, "sim")
    )

    if not effective_id:
        # 정규화 실패: 그대로 NOT_FOUND 처리
        checked_at = datetime.now(timezone(timedelta(hours=9)))  # KST
        return RankResult(
            product_id=product_url,
            keyword=keyword,
            rank=None,
            status=RankStatus.INVALID_PRODUCT,
            total_scanned=0,
            checked_at=checked_at,
            error_message="URL에서 productId를 결정할 수 없습니다."
        )

    # 2) 정규화된 ID로 기존 로직 사용 (상품명/스토어명은 기존 메서드가 ProductItem로 반환)
    return self.calculate_single_rank(keyword=keyword, product_id=str(effective_id), sort_order=sort_order)
```

> 이렇게 하면 **URL만 입력해도**:  
> (a) 상위 결과에서 **raw ID가 보이는지 우선 확인** → (b) 안 보이면 **카탈로그 ID로 폴백** → (c) **유기 순위 매칭 + `ProductItem(title, mall_name)`** 이 UI에 전달됩니다.  
> 응답 필드(`productId`, `title`, `mallName`, …), 정렬 옵션, 페이징/필터/제외 규칙은 네이버 공식 문서와 일치합니다. citeturn1view0

---

## 사용 예시

```python
# 예시: URL로 순위 + 상품명/스토어명 얻기
calc = RankCalculator(api_client=naver_api_client)  # 기존대로 생성
res = calc.calculate_single_rank_by_url(
    keyword="무선 청소기",
    product_url="https://smartstore.naver.com/main/products/7058693395"
)

if res.is_ranked:
    print(f"[{res.rank}위] {res.product_info.title} · {res.product_info.mall_name}")
else:
    print(f"미발견 (스캔: {res.total_scanned}) - {res.error_message or ''}")
```

> 참고: 쇼핑 검색 API는 **유기 결과만** 반환합니다(광고 슬롯 미포함). 응답 스키마에 `productId`, `title`, `mallName` 등 필드가 정의돼 있으며, `display≤100`, `start≤1000`, `sort=sim|date|asc|dsc`, `filter`/`exclude`를 지원합니다. 하루 호출 한도는 **25,000회**입니다. citeturn1view0

---

## 디버깅 체크리스트
- [ ] 같은 키워드로 **Top 100**의 `productId/title/mallName`을 임시로 로그에 찍어보면, 카탈로그/개별상품 노출 형태를 바로 확인 가능합니다. (`productType` 표는 문서에 제공) citeturn1view0  
- [ ] **정규화 실패**가 반복되면, URL 패턴(`smartstore`, `brand`, `catalog`)이 맞는지 확인하세요.  
- [ ] `403`은 **애플리케이션 API 권한 미설정**일 수 있습니다(문서의 주의사항 참조). citeturn1view0  
- [ ] `SE02/SE03` 오류면 `display(1~100)`·`start(1~1000)` 범위를 벗어나지 않았는지 확인. citeturn1view0

---

## 출처 (공식)
- **네이버 개발자 센터 — 검색 > 쇼핑**: 요청 URL(`shop.json`), 파라미터(`display/start/sort/filter/exclude`), 응답 필드(`productId/title/link/image/lprice/hprice/mallName/productType/...`), 하루 한도 **25,000회**, 비로그인 헤더 인증, 오류코드/주의사항. citeturn1view0

— Generated 2025-09-25 02:52:31
