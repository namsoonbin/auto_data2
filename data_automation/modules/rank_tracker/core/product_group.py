"""
Product Group 클래스 - URL+키워드 기반 관리 시스템
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class GroupItem:
    """그룹 내 개별 상품+키워드 아이템"""
    url: str                    # 상품 URL
    keyword: str               # 검색 키워드
    title: str                 # 상품명
    product_id: str           # 정규화된 상품 ID
    added_at: str             # 추가 일시
    last_rank: Optional[int] = None      # 최근 순위
    last_checked: Optional[str] = None   # 최근 체크 일시
    last_error: Optional[str] = None     # 최근 오류

    def __post_init__(self):
        """초기화 후 처리"""
        if not self.added_at:
            self.added_at = datetime.now(timezone(timedelta(hours=9))).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupItem':
        """딕셔너리에서 생성"""
        return cls(**data)


class ProductGroup:
    """상품 그룹 클래스 - URL+키워드 기반"""

    def __init__(self, group_id: str, name: str, description: str = ""):
        self.group_id = group_id
        self.name = name
        self.description = description
        self.items: Dict[str, GroupItem] = {}  # item_id -> GroupItem
        self.created_at = datetime.now(timezone(timedelta(hours=9))).isoformat()
        self.last_checked: Optional[str] = None

    def add_item(self, url: str, keyword: str, title: str = "", product_id: str = "") -> str:
        """새 아이템 추가"""
        # 고유 아이템 ID 생성 (URL+키워드 기반)
        item_id = f"{hash(url + keyword):x}"[-8:]

        # 기본값 설정
        if not title:
            title = f"상품 {item_id}"
        if not product_id:
            from ..id_utils import extract_product_id
            product_id = extract_product_id(url) or ""

        item = GroupItem(
            url=url,
            keyword=keyword,
            title=title,
            product_id=product_id,
            added_at=datetime.now(timezone(timedelta(hours=9))).isoformat()
        )

        self.items[item_id] = item
        logger.info(f"그룹 '{self.name}'에 아이템 추가: {title} (키워드: {keyword})")
        return item_id

    def remove_item(self, item_id: str) -> bool:
        """아이템 제거"""
        if item_id in self.items:
            item = self.items.pop(item_id)
            logger.info(f"그룹 '{self.name}'에서 아이템 제거: {item.title}")
            return True
        return False

    def update_item_rank(self, item_id: str, rank: Optional[int], error: Optional[str] = None):
        """아이템 순위 업데이트"""
        if item_id in self.items:
            item = self.items[item_id]
            item.last_rank = rank
            item.last_checked = datetime.now(timezone(timedelta(hours=9))).isoformat()
            item.last_error = error
            logger.debug(f"아이템 {item.title} 순위 업데이트: {rank}")

    def get_items_for_keyword(self, keyword: str) -> List[GroupItem]:
        """특정 키워드의 아이템들 반환"""
        return [item for item in self.items.values() if item.keyword == keyword]

    def get_all_keywords(self) -> List[str]:
        """그룹의 모든 키워드 반환"""
        return list(set(item.keyword for item in self.items.values()))

    def get_item_count(self) -> int:
        """총 아이템 수"""
        return len(self.items)

    def get_keyword_count(self) -> int:
        """총 키워드 수"""
        return len(self.get_all_keywords())

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 저장용)"""
        return {
            "group_id": self.group_id,
            "name": self.name,
            "description": self.description,
            "items": {item_id: item.to_dict() for item_id, item in self.items.items()},
            "created_at": self.created_at,
            "last_checked": self.last_checked
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductGroup':
        """딕셔너리에서 생성 (JSON 로드용)"""
        group = cls(
            group_id=data["group_id"],
            name=data["name"],
            description=data.get("description", "")
        )
        group.created_at = data.get("created_at", group.created_at)
        group.last_checked = data.get("last_checked")

        # 아이템들 로드
        items_data = data.get("items", {})
        for item_id, item_data in items_data.items():
            try:
                group.items[item_id] = GroupItem.from_dict(item_data)
            except Exception as e:
                logger.warning(f"아이템 로드 실패 (ID: {item_id}): {e}")

        return group

    @classmethod
    def from_legacy_format(cls, data: Dict[str, Any]) -> 'ProductGroup':
        """기존 형식에서 변환"""
        group = cls(
            group_id=data.get("group_id", ""),
            name=data.get("name", ""),
            description=data.get("description", "")
        )

        # 기존 products 배열을 items로 변환
        products = data.get("products", [])
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    url = product.get("url", "")
                    title = product.get("title", "")
                    # 기존 형식에는 키워드가 없으므로 기본값 설정
                    group.add_item(url=url, keyword="기본키워드", title=title)

        return group


class ProductGroupManager:
    """상품 그룹 관리자"""

    def __init__(self, data_file: str = None):
        # ✅ 경로 통일: config.BASE_DIR 기준으로 절대 경로 사용
        if data_file is None:
            try:
                # config.py에서 BASE_DIR 가져오기 (exe/개발 환경 자동 감지)
                import sys
                from pathlib import Path

                # config 모듈 import
                config_path = Path(__file__).parent.parent.parent
                sys.path.insert(0, str(config_path))
                from config import BASE_DIR

                self.data_file = str(BASE_DIR / "product_groups.json")
                logger.info(f"✅ 그룹 데이터 파일 경로: {self.data_file}")
            except Exception as e:
                # Fallback: 상대 경로
                logger.warning(f"⚠️ config.BASE_DIR 로드 실패, 상대 경로 사용: {e}")
                self.data_file = "product_groups.json"
        else:
            self.data_file = data_file

        self.groups: Dict[str, ProductGroup] = {}
        self.load_groups()

    def load_groups(self) -> bool:
        """그룹 데이터 로드"""
        try:
            if not os.path.exists(self.data_file):
                logger.info("그룹 데이터 파일이 없습니다. 새로 생성합니다.")
                return True

            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 기존 데이터 초기화 (재로드 시 중복 방지)
            self.groups.clear()

            # 새 형식 로드
            groups_loaded = 0
            for key, value in data.items():
                if isinstance(value, dict) and 'name' in value:
                    try:
                        if 'items' in value:  # 새 형식
                            group = ProductGroup.from_dict(value)
                        else:  # 기존 형식
                            group = ProductGroup.from_legacy_format(value)

                        self.groups[group.group_id] = group
                        groups_loaded += 1
                    except Exception as e:
                        logger.error(f"그룹 로드 실패 (키: {key}): {e}")

            logger.info(f"그룹 {groups_loaded}개 로드 완료")
            return True

        except Exception as e:
            logger.error(f"그룹 데이터 로드 실패: {e}")
            return False

    def save_groups(self) -> bool:
        """그룹 데이터 저장"""
        try:
            # 백업 생성
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                import shutil
                shutil.copy2(self.data_file, backup_file)

            # 새 형식으로 저장
            data = {}
            for group_id, group in self.groups.items():
                data[group_id] = group.to_dict()

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"그룹 {len(self.groups)}개 저장 완료")
            return True

        except Exception as e:
            logger.error(f"그룹 데이터 저장 실패: {e}")
            return False

    def create_group(self, name: str, description: str = "") -> str:
        """새 그룹 생성"""
        # 고유 ID 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        group_id = f"group_{timestamp}"

        group = ProductGroup(group_id=group_id, name=name, description=description)
        self.groups[group_id] = group

        logger.info(f"새 그룹 생성: '{name}' (ID: {group_id})")
        return group_id

    def delete_group(self, group_id: str) -> bool:
        """그룹 삭제"""
        if group_id in self.groups:
            group_name = self.groups[group_id].name
            del self.groups[group_id]
            logger.info(f"그룹 삭제: '{group_name}' (ID: {group_id})")
            return True
        return False

    def get_group(self, group_id: str) -> Optional[ProductGroup]:
        """그룹 조회"""
        return self.groups.get(group_id)

    def get_all_groups(self) -> List[ProductGroup]:
        """모든 그룹 반환"""
        return list(self.groups.values())

    def search_groups(self, query: str) -> List[ProductGroup]:
        """그룹 검색 (이름, 설명으로)"""
        query = query.lower()
        results = []

        for group in self.groups.values():
            if (query in group.name.lower() or
                query in group.description.lower()):
                results.append(group)

        return results

    def get_groups_by_keyword(self, keyword: str) -> List[ProductGroup]:
        """특정 키워드가 포함된 그룹들 반환"""
        results = []

        for group in self.groups.values():
            if keyword in group.get_all_keywords():
                results.append(group)

        return results

    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        데이터 정합성 검증 - Context7 2025

        모든 그룹과 아이템의 데이터 무결성을 검증하고
        발견된 문제점과 통계를 반환합니다.

        Returns:
            {
                'valid': bool,           # 전체 데이터 유효 여부
                'issues': List[str],     # 발견된 문제점 목록
                'stats': Dict            # 통계 정보
            }
        """
        issues = []
        stats = {
            'total_groups': len(self.groups),
            'total_items': 0,
            'items_without_product_id': 0,
            'items_without_keyword': 0,
            'items_without_title': 0,
            'groups_without_items': 0,
            'duplicate_item_ids': 0
        }

        # 중복 item_id 검증용 집합
        all_item_ids = set()
        duplicate_ids = set()

        for group_id, group in self.groups.items():
            item_count = group.get_item_count()
            stats['total_items'] += item_count

            # 빈 그룹 검증
            if item_count == 0:
                issues.append(f"그룹 '{group.name}' (ID: {group_id})에 아이템이 없음")
                stats['groups_without_items'] += 1

            # 각 아이템 검증
            for item_id, item in group.items.items():
                # 중복 item_id 검증
                if item_id in all_item_ids:
                    duplicate_ids.add(item_id)
                    stats['duplicate_item_ids'] += 1
                else:
                    all_item_ids.add(item_id)

                # product_id 검증
                if not item.product_id:
                    issues.append(
                        f"아이템 {item_id} (그룹: {group.name})에 product_id 없음"
                    )
                    stats['items_without_product_id'] += 1

                # keyword 검증
                if not item.keyword or item.keyword.strip() == "":
                    issues.append(
                        f"아이템 {item_id} (그룹: {group.name})에 keyword 없음"
                    )
                    stats['items_without_keyword'] += 1

                # title 검증
                if not item.title or item.title.strip() == "":
                    issues.append(
                        f"아이템 {item_id} (그룹: {group.name})에 title 없음"
                    )
                    stats['items_without_title'] += 1

        # 중복 ID 상세 정보 추가
        if duplicate_ids:
            issues.append(f"중복된 item_id 발견: {', '.join(duplicate_ids)}")

        # 전체 유효성 판단
        valid = len(issues) == 0

        logger.info(
            f"데이터 정합성 검증 완료: "
            f"valid={valid}, issues={len(issues)}, "
            f"groups={stats['total_groups']}, items={stats['total_items']}"
        )

        return {
            'valid': valid,
            'issues': issues,
            'stats': stats
        }