# enhanced_rank.py
from typing import Optional
from .enhanced_api import NaverShopAPI, SearchParams as EnhancedSearchParams

def get_rank_for_product(api: NaverShopAPI, keyword: str, product_id: str,
                         sort: str = "sim",
                         include_filter: Optional[str] = None,
                         exclude_types: Optional[list[str]] = None,
                         max_depth: int = 1000,
                         page_size: int = 100) -> tuple[Optional[int], Optional[dict], int]:
    """순위, 매칭 아이템(JSON), 실제 스캔 수를 함께 반환."""
    import logging
    logger = logging.getLogger(__name__)

    scanned = 0
    found_ids = []  # 발견된 ID들 추적

    for start in range(1, min(max_depth, 1000) + 1, page_size):
        display = min(page_size, max_depth - start + 1)
        params = EnhancedSearchParams(query=keyword, start=start, display=display, sort=sort,
                              filter=include_filter, exclude=exclude_types)
        resp = api.search(params)
        items = resp.get("items", [])

        # 첫 번째 페이지에서 발견된 ID들 로깅
        if start <= 100:
            page_ids = [str(it.get("productId")) for it in items[:5]]  # 상위 5개만
            found_ids.extend(page_ids)
            logger.info(f"페이지 {start}-{start+len(items)-1} 상위 5개 Product ID: {page_ids}")

        for i, it in enumerate(items):
            current_product_id = str(it.get("productId"))
            if current_product_id == str(product_id):
                logger.info(f"✅ 매칭 성공! 순위 {scanned + i + 1}위에서 발견: {current_product_id}")
                return scanned + i + 1, it, scanned + len(items)
        scanned += len(items)
        if scanned >= resp.get("total", 0):
            break

    # 매칭 실패 시 상세 정보
    logger.warning(f"❌ 매칭 실패 - 찾는 ID: '{product_id}', 발견된 상위 ID들: {found_ids[:10]}")
    return None, None, scanned

def calculate_rank_with_id_resolution(api: NaverShopAPI, keyword: str, user_input: str,
                                      sort:str="sim", include_filter:Optional[str]=None,
                                      exclude_types:Optional[list[str]]=None,
                                      max_depth:int=1000) -> dict:
    """사용자 입력을 받아서 ID를 정규화하고 순위를 계산하는 통합 함수 (단일 API 호출)"""
    import logging
    import re
    logger = logging.getLogger(__name__)

    from .id_utils import extract_product_id

    # 1) URL에서 raw ID 추출
    raw_id = extract_product_id(user_input)
    logger.info(f"🔍 통합 검색 시작: input='{user_input}' → raw_id='{raw_id}'")

    if not raw_id:
        return {
            "success": False,
            "error": f"URL 또는 상품 ID를 인식할 수 없습니다: {user_input}",
            "user_input": user_input,
            "keyword": keyword,
            "rank": None,
            "found": False
        }

    # 2) 단일 API 호출로 검색 결과 획득 및 ID 정규화 + 순위 계산 통합 처리
    scanned = 0
    effective_id = None
    target_rank = None
    matched_item = None
    found_ids = []  # 디버깅용
    first_catalog_id = None

    for start in range(1, min(max_depth, 1000) + 1, 100):
        display = min(100, max_depth - start + 1)
        params = EnhancedSearchParams(query=keyword, start=start, display=display, sort=sort,
                              filter=include_filter, exclude=exclude_types)
        resp = api.search(params)
        items = resp.get("items", [])

        # 첫 페이지에서 ID 정규화 수행
        if start == 1:
            logger.info(f"  📄 첫 페이지 ({start}~{start+len(items)-1}): {len(items)}개 아이템 검색")

            for idx, it in enumerate(items):
                link = it.get("link", "")
                m = re.search(r"/(catalog|products)/(\d+)", link)
                if not m:
                    continue

                eff_id = m.group(2)
                is_catalog = "catalog" in m.group(1)
                found_ids.append(eff_id)

                # 디버깅용 상위 5개 로깅
                if idx < 5:
                    item_type = "catalog" if is_catalog else "products"
                    logger.info(f"    {idx+1}위: {eff_id} ({item_type})")

                # raw ID와 직접 매칭되면 그것을 사용
                if raw_id == eff_id:
                    effective_id = eff_id
                    logger.info(f"✅ Raw ID 직접 매칭: {raw_id}")
                    break

                # 첫 번째 카탈로그 ID 기억 (폴백용)
                if is_catalog and first_catalog_id is None:
                    first_catalog_id = eff_id
                    logger.info(f"📝 첫 번째 카탈로그 ID 후보: {first_catalog_id}")

            # Raw ID를 찾지 못한 경우 처리
            if effective_id is None:
                logger.info(f"❌ Raw ID '{raw_id}' 미발견. 검색된 상위 ID들: {found_ids[:10]}")
                logger.warning(f"⚠️ 해당 상품이 '{keyword}' 검색 결과에 없습니다.")
                return {
                    "success": False,
                    "error": f"해당 상품이 '{keyword}' 검색 결과에 없습니다. 상품이 검색에 노출되지 않거나 다른 키워드로 검색되고 있을 수 있습니다.",
                    "user_input": user_input,
                    "keyword": keyword,
                    "rank": None,
                    "found": False,
                    "scanned": len(items)
                }

        # 순위 계산 - effective_id가 결정된 후 검색
        if effective_id:
            for i, it in enumerate(items):
                current_product_id = str(it.get("productId"))
                if current_product_id == str(effective_id):
                    target_rank = scanned + i + 1
                    matched_item = it
                    logger.info(f"✅ 순위 매칭 성공! {target_rank}위에서 발견: {effective_id}")
                    break

        scanned += len(items)

        # 순위를 찾았으면 조기 종료
        if target_rank:
            break

        if scanned >= resp.get("total", 0):
            break

    # 결과 반환
    if target_rank:
        return {
            "success": True,
            "user_input": user_input,
            "effective_product_id": effective_id,
            "keyword": keyword,
            "rank": target_rank,
            "matched_item": matched_item,
            "scanned": scanned,
            "sort": sort,
            "filter": include_filter,
            "exclude": exclude_types,
            "max_depth": max_depth,
            "found": True
        }
    else:
        logger.warning(f"❌ 순위 미발견 - effective_id: '{effective_id}', scanned: {scanned}")
        return {
            "success": True,
            "user_input": user_input,
            "effective_product_id": effective_id,
            "keyword": keyword,
            "rank": None,
            "matched_item": None,
            "scanned": scanned,
            "sort": sort,
            "filter": include_filter,
            "exclude": exclude_types,
            "max_depth": max_depth,
            "found": False
        }