# id_utils.py
import re
from urllib.parse import urlparse
from typing import Optional
# enhanced_api는 함수 내부에서 import (순환 참조 방지)

_PATTERNS = [
    r"https?://search\.shopping\.naver\.com/catalog/(\d+)",
    r"https?://smartstore\.naver\.com/(?:[^/]+/)?products/(\d+)",  # {store}/products/{id} 또는 main/products/{id}
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

def resolve_effective_product_id(api, keyword: str, user_input: str,
                                 pages:int=2, sort:str="sim") -> Optional[str]:
    """실제 '검색 화면'에 노출되는 엔티티의 ID(카탈로그/스마트스토어)를 결정.
    정책: raw ID가 Top N(=pages*100)에서 보이면 raw 유지, 없으면 catalog로 폴백.
    """
    # 지연 import로 순환 참조 방지
    from .enhanced_api import SearchParams as EnhancedSearchParams
    import logging
    logger = logging.getLogger(__name__)

    raw_id = extract_product_id(user_input)
    logger.info(f"🔍 ID 정규화 시작: input='{user_input}' → raw_id='{raw_id}'")

    # 1) raw ID가 있다면: 우선 Top 영역에서 실제로 보이는지 확인
    if raw_id:
        first_catalog_candidate = None
        found_raw = False
        all_found_ids = []

        for p in range(pages):
            start_pos = 1 + p * 100
            resp = api.search(EnhancedSearchParams(query=keyword, start=start_pos, display=100, sort=sort))
            items = resp.get("items", [])
            logger.info(f"  📄 페이지 {p+1} ({start_pos}~{start_pos+len(items)-1}): {len(items)}개 아이템 검색")

            for idx, it in enumerate(items):
                link = it.get("link", "")
                m = re.search(r"/(catalog|products)/(\d+)", link)
                if not m:
                    continue

                eff_id = m.group(2)
                is_catalog = "catalog" in m.group(1)
                all_found_ids.append(eff_id)

                # 상위 5개 아이템만 로깅 (첫 페이지)
                if p == 0 and idx < 5:
                    item_type = "catalog" if is_catalog else "products"
                    logger.info(f"    {idx+1}위: {eff_id} ({item_type})")

                # raw ID와 정확히 일치하는 경우
                if raw_id == eff_id:
                    logger.info(f"✅ Raw ID 직접 매칭 발견: {raw_id}")
                    found_raw = True
                    return eff_id

                # 첫 번째 카탈로그 ID 기억 (폴백용)
                if is_catalog and first_catalog_candidate is None:
                    first_catalog_candidate = eff_id
                    logger.info(f"📝 첫 번째 카탈로그 ID 후보: {first_catalog_candidate}")

        # Raw ID를 찾지 못한 경우 처리
        if not found_raw:
            logger.info(f"❌ Raw ID '{raw_id}' 미발견. 검색된 상위 ID들: {all_found_ids[:10]}")
            logger.warning(f"⚠️ 해당 상품이 검색 결과에 없습니다. 다른 상품으로 대체하지 않습니다.")
            return None  # 해당 상품을 찾을 수 없으면 None 반환

    # 2) URL/숫자로 못 뽑혔으면 상위 페이지에서 첫 노출 항목의 ID 채택
    logger.info("🔍 URL/숫자 추출 실패, 검색 결과에서 첫 번째 ID 사용")
    for p in range(pages):
        resp = api.search(EnhancedSearchParams(query=keyword, start=1 + p*100, display=100, sort=sort))
        for it in resp.get("items", []):
            m = re.search(r"/(catalog|products)/(\d+)", it.get("link",""))
            if m:
                logger.info(f"🎯 검색 결과 첫 번째 ID 선택: {m.group(2)}")
                return m.group(2)

    logger.error("❌ 모든 방법으로 Product ID를 결정할 수 없음")
    return None