"""
순위 자동 표시 워커 - 그룹 선택 시 모든 아이템의 순위를 자동으로 검색하고 업데이트
"""

import logging
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, QThread
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class RankDisplayWorker(QObject):
    """그룹 선택 시 자동 순위 표시를 위한 워커"""

    # 시그널 정의
    progress = Signal(int, str)  # percentage, message
    item_updated = Signal(str, dict)  # item_id, rank_result
    finished = Signal()
    error = Signal(str)  # error_message

    def __init__(self, group_id: str, items: Dict, engine=None):
        super().__init__()
        self.group_id = group_id
        self.items = items  # {item_id: GroupItem}
        self.engine = engine
        self.should_stop = False

    def set_engine(self, engine):
        """순위 엔진 설정"""
        self.engine = engine

    def stop(self):
        """작업 중지"""
        self.should_stop = True

    def run(self):
        """자동 순위 표시 실행 - 상품명도 함께 업데이트"""
        if not self.engine:
            self.error.emit("순위 엔진이 설정되지 않았습니다")
            return

        if not self.items:
            self.finished.emit()
            return

        total_items = len(self.items)
        processed = 0

        try:
            logger.info(f"그룹 '{self.group_id}' 자동 순위 표시 시작: {total_items}개 아이템")

            for item_id, item in self.items.items():
                if self.should_stop:
                    break

                try:
                    # 진행률 업데이트
                    progress_percent = int((processed / total_items) * 100)
                    self.progress.emit(
                        progress_percent,
                        f"{item.title} 순위 확인 중... ({item.keyword})"
                    )

                    # 순위 검색
                    result = self.engine.search_instant_rank(item.keyword, item.url)

                    # 결과를 딕셔너리로 변환
                    if result:
                        # ✅ 상품명 업데이트: "상품 {ID}" 형태인 경우만 업데이트
                        updated_title = None
                        if result.success and result.product_info and result.product_info.title:
                            # 현재 title이 "상품 {숫자}" 형태이거나 짧은 경우만 업데이트
                            if item.title.startswith("상품 ") or len(item.title) < 10:
                                old_title = item.title
                                item.title = result.product_info.title
                                updated_title = result.product_info.title
                                logger.info(f"✅ 상품명 자동 업데이트: {item_id} | {old_title} → {updated_title}")

                        rank_data = {
                            'success': result.success,
                            'rank': result.rank,
                            'error_message': result.error_message,
                            'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                            'updated_title': updated_title  # 업데이트된 상품명 포함
                        }
                    else:
                        rank_data = {
                            'success': False,
                            'rank': None,
                            'error_message': '검색 결과 없음',
                            'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                            'updated_title': None
                        }

                    # 결과 전송
                    self.item_updated.emit(item_id, rank_data)

                except Exception as e:
                    logger.error(f"아이템 {item.title} 순위 검색 실패: {e}")
                    error_data = {
                        'success': False,
                        'rank': None,
                        'error_message': str(e),
                        'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                        'updated_title': None
                    }
                    self.item_updated.emit(item_id, error_data)

                processed += 1

            # 완료
            self.progress.emit(100, "모든 순위 확인 완료!")
            logger.info(f"그룹 '{self.group_id}' 자동 순위 표시 완료: {processed}/{total_items}")

        except Exception as e:
            logger.error(f"자동 순위 표시 실패: {e}")
            self.error.emit(f"자동 순위 표시 실패: {str(e)}")
        finally:
            self.finished.emit()