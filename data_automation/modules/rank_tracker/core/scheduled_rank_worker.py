"""
스케줄된 순위 추적 워커 - URL+키워드 기반 구조 지원
Context7 2025: asyncio 통합으로 성능 향상 + DB 연동
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from PySide6.QtCore import QObject, Signal, QThread
from dataclasses import asdict

try:
    from .rank_history_db import RankHistoryDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("RankHistoryDB not available - history will not be saved")

logger = logging.getLogger(__name__)


class ScheduledRankWorker(QObject):
    """스케줄된 순위 추적을 위한 워커 - 새로운 URL+키워드 구조 지원"""

    # 시그널 정의
    progress = Signal(int, str, str)  # percentage, message, group_name
    group_completed = Signal(str, dict)  # group_id, results
    all_completed = Signal(dict)  # {group_id: results}
    error = Signal(str, str)  # group_id, error_message
    status = Signal(str)  # status_message

    def __init__(self, group_manager, engine, selected_groups: List[str], use_async: bool = False, db_path: Optional[str] = None):
        super().__init__()
        self.group_manager = group_manager
        self.engine = engine
        self.selected_groups = selected_groups
        self.should_stop = False
        self.all_results = {}
        self.use_async = use_async and hasattr(engine, 'search_instant_rank_async')

        # DB 초기화
        self.db = None
        if DB_AVAILABLE:
            try:
                self.db = RankHistoryDB(db_path) if db_path else RankHistoryDB()
                logger.info("RankHistoryDB initialized for scheduled tracking")
            except Exception as e:
                logger.error(f"Failed to initialize RankHistoryDB: {e}")
                self.db = None

    def stop(self):
        """작업 중지"""
        self.should_stop = True

    def run(self):
        """스케줄된 순위 추적 실행"""
        if not self.group_manager or not self.engine:
            self.error.emit("", "GroupManager 또는 Engine이 설정되지 않았습니다")
            return

        if not self.selected_groups:
            self.all_completed.emit({})
            return

        total_groups = len(self.selected_groups)
        logger.info(f"스케줄된 순위 추적 시작: {total_groups}개 그룹")

        try:
            for group_index, group_id in enumerate(self.selected_groups):
                if self.should_stop:
                    break

                group = self.group_manager.get_group(group_id)
                if not group:
                    logger.warning(f"그룹을 찾을 수 없음: {group_id}")
                    continue

                # 그룹 진행률 업데이트
                group_progress = int((group_index / total_groups) * 100)
                self.status.emit(f"그룹 '{group.name}' 처리 중... ({group_index + 1}/{total_groups})")

                # 그룹 내 모든 아이템 처리
                group_results = self.process_group(group, group_progress, total_groups)
                self.all_results[group_id] = group_results

                # 그룹 완료 시그널
                self.group_completed.emit(group_id, group_results)

                # 그룹 간 간격 (API 부하 분산)
                if group_index < total_groups - 1 and not self.should_stop:
                    QThread.msleep(2000)  # 2초 = 2000ms (QThread에서 안전)

            # 전체 완료
            self.progress.emit(100, "모든 그룹 처리 완료!", "")
            self.all_completed.emit(self.all_results)
            logger.info("스케줄된 순위 추적 완료")

        except Exception as e:
            logger.error(f"스케줄된 순위 추적 실패: {e}")
            self.error.emit("", f"스케줄된 순위 추적 실패: {str(e)}")

    def process_group(self, group, base_progress: int, total_groups: int) -> Dict:
        """
        개별 그룹의 모든 아이템 처리

        비동기 모드가 활성화되어 있고 아이템이 많을 경우 병렬 처리
        """
        group_results = {}

        if not group.items:
            logger.info(f"그룹 '{group.name}'에 아이템이 없음")
            return group_results

        total_items = len(group.items)
        logger.info(f"그룹 '{group.name}' 처리: {total_items}개 아이템")

        # Context7 최적화: 병렬 처리로 성능 향상 (비동기 모드 + 3개 이상 아이템)
        if self.use_async and total_items >= 3:
            try:
                logger.info(f"  🚀 병렬 처리 모드로 {total_items}개 아이템 처리")
                return self._process_group_parallel(group, base_progress, total_groups)
            except Exception as e:
                logger.warning(f"  ⚠️ 병렬 처리 실패, 순차 처리로 폴백: {e}")
                # 폴백: 순차 처리

        # 기본: 순차 처리
        return self._process_group_sequential(group, base_progress, total_groups)

    def _process_group_sequential(self, group, base_progress: int, total_groups: int) -> Dict:
        """순차 처리 (기존 로직)"""
        group_results = {}
        total_items = len(group.items)

        for item_index, (item_id, item) in enumerate(group.items.items()):
            if self.should_stop:
                break

            # 아이템별 진행률 계산
            item_progress_within_group = int((item_index / total_items) * 100)
            overall_progress = base_progress + int(item_progress_within_group / total_groups)

            self.progress.emit(
                overall_progress,
                f"{item.title} 순위 확인 중... (키워드: {item.keyword})",
                group.name
            )

            try:
                # 순위 검색 실행 (async/sync 자동 선택)
                logger.info(f"  🔍 '{item.title}' 순위 검색 시작 (키워드: '{item.keyword}', URL: {item.url})")

                if self.use_async:
                    # Context7 권장: asyncio.run()으로 QThread에서 async 함수 실행
                    try:
                        result = asyncio.run(
                            self.engine.search_instant_rank_async(item.keyword, item.url)
                        )
                        logger.info(f"  ✅ '{item.title}' 비동기 순위 검색 완료: success={result.success if result else None}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 비동기 검색 실패, 동기 모드로 폴백: {e}")
                        result = self.engine.search_instant_rank(item.keyword, item.url)
                        logger.info(f"  ✅ '{item.title}' 동기 순위 검색 완료: success={result.success if result else None}")
                else:
                    result = self.engine.search_instant_rank(item.keyword, item.url)
                    logger.info(f"  ✅ '{item.title}' 순위 검색 완료: success={result.success if result else None}")

                if result:
                    # 성공적인 결과 처리
                    rank_data = {
                        'success': result.success,
                        'rank': result.rank,
                        'error_message': result.error_message,
                        'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                        'keyword': item.keyword,
                        'url': item.url,
                        'title': item.title,
                        'image_url': result.product_info.image_url if result.product_info else None
                    }

                    # DB에 순위 저장
                    if self.db:
                        try:
                            self.db.save_rank(
                                item_id=item_id,
                                group_id=group.group_id,
                                product_id=item.product_id,
                                keyword=item.keyword,
                                url=item.url,
                                title=item.title,
                                rank=result.rank if result.success else None,
                                success=result.success,
                                error_message=result.error_message,
                                checked_at=rank_data['search_time']
                            )

                            # 전일 대비 순위 변화 계산
                            rank_change = self.db.get_rank_change(item_id)
                            if rank_change:
                                rank_data['rank_change'] = rank_change['change']
                                rank_data['previous_rank'] = rank_change['previous_rank']
                                logger.info(f"  📊 '{item.title}' 순위 변화: {rank_change['previous_rank']} → {rank_change['current_rank']} (전일 대비 {rank_change['change']:+d})")
                            else:
                                rank_data['rank_change'] = None
                                rank_data['previous_rank'] = None

                        except Exception as db_error:
                            logger.error(f"Failed to save rank to DB: {db_error}")
                            rank_data['rank_change'] = None
                            rank_data['previous_rank'] = None
                    else:
                        rank_data['rank_change'] = None
                        rank_data['previous_rank'] = None

                    # 그룹 내 아이템 업데이트
                    if result.success and result.rank is not None:
                        item.last_rank = result.rank
                        item.last_error = None
                    else:
                        item.last_rank = None
                        item.last_error = result.error_message

                    item.last_checked = rank_data['search_time']

                else:
                    # 결과가 없는 경우
                    rank_data = {
                        'success': False,
                        'rank': None,
                        'error_message': '검색 결과 없음',
                        'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                        'keyword': item.keyword,
                        'url': item.url,
                        'title': item.title,
                        'rank_change': None,
                        'previous_rank': None
                    }

                    # DB에 실패 기록 저장
                    if self.db:
                        try:
                            self.db.save_rank(
                                item_id=item_id,
                                group_id=group.group_id,
                                product_id=item.product_id,
                                keyword=item.keyword,
                                url=item.url,
                                title=item.title,
                                rank=None,
                                success=False,
                                error_message='검색 결과 없음',
                                checked_at=rank_data['search_time']
                            )
                        except Exception as db_error:
                            logger.error(f"Failed to save error to DB: {db_error}")

                    item.last_rank = None
                    item.last_error = '검색 결과 없음'
                    item.last_checked = rank_data['search_time']

                group_results[item_id] = rank_data
                logger.debug(f"아이템 '{item.title}' 순위: {item.last_rank}")

            except Exception as e:
                logger.error(f"아이템 '{item.title}' 순위 검색 실패: {e}")

                error_data = {
                    'success': False,
                    'rank': None,
                    'error_message': str(e),
                    'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                    'keyword': item.keyword,
                    'url': item.url,
                    'title': item.title,
                    'rank_change': None,
                    'previous_rank': None
                }

                # DB에 예외 기록 저장
                if self.db:
                    try:
                        self.db.save_rank(
                            item_id=item_id,
                            group_id=group.group_id,
                            product_id=item.product_id,
                            keyword=item.keyword,
                            url=item.url,
                            title=item.title,
                            rank=None,
                            success=False,
                            error_message=str(e),
                            checked_at=error_data['search_time']
                        )
                    except Exception as db_error:
                        logger.error(f"Failed to save error to DB: {db_error}")

                item.last_rank = None
                item.last_error = str(e)
                item.last_checked = error_data['search_time']

                group_results[item_id] = error_data

            # 아이템 간 간격 (API 부하 분산)
            if item_index < total_items - 1 and not self.should_stop:
                QThread.msleep(1000)  # 1초 = 1000ms (QThread에서 안전)

        # 그룹 처리 완료 시 데이터 저장
        group.last_checked = datetime.now(timezone(timedelta(hours=9))).isoformat()
        if self.group_manager:
            self.group_manager.save_groups()

        logger.info(f"그룹 '{group.name}' 처리 완료: {len(group_results)}개 아이템")
        return group_results

    def _process_group_parallel(self, group, base_progress: int, total_groups: int) -> Dict:
        """
        병렬 처리 (Context7 2025: asyncio.run() + gather)

        QThread에서 asyncio.run()을 사용하여 여러 상품을 병렬로 검색
        """
        group_results = {}
        total_items = len(group.items)

        async def process_all_items():
            """모든 아이템을 병렬로 처리하는 async 함수"""
            tasks = []
            items_list = list(group.items.items())

            for item_index, (item_id, item) in enumerate(items_list):
                if self.should_stop:
                    break

                # 각 아이템에 대한 async task 생성
                task = self._process_single_item_async(
                    item_id, item, item_index, total_items,
                    base_progress, total_groups, group.name
                )
                tasks.append((item_id, item, task))

            # Context7 권장: asyncio.gather()로 병렬 실행
            results = await asyncio.gather(*[t[2] for t in tasks], return_exceptions=True)

            # 결과 처리 및 DB 저장
            for i, ((item_id, item, _), result) in enumerate(zip(tasks, results)):
                if isinstance(result, Exception):
                    logger.error(f"아이템 '{item.title}' 병렬 처리 실패: {result}")
                    result = {
                        'success': False,
                        'rank': None,
                        'error_message': str(result),
                        'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                        'keyword': item.keyword,
                        'url': item.url,
                        'title': item.title,
                        'rank_change': None,
                        'previous_rank': None
                    }

                # DB에 저장 (병렬 처리 결과)
                if self.db:
                    try:
                        self.db.save_rank(
                            item_id=item_id,
                            group_id=group.group_id,
                            product_id=item.product_id,
                            keyword=result.get('keyword', item.keyword),
                            url=result.get('url', item.url),
                            title=result.get('title', item.title),
                            rank=result.get('rank'),
                            success=result.get('success', False),
                            error_message=result.get('error_message'),
                            checked_at=result['search_time']
                        )

                        # 전일 대비 순위 변화 계산
                        if result.get('success') and result.get('rank') is not None:
                            rank_change = self.db.get_rank_change(item_id)
                            if rank_change:
                                result['rank_change'] = rank_change['change']
                                result['previous_rank'] = rank_change['previous_rank']
                            else:
                                result['rank_change'] = None
                                result['previous_rank'] = None

                    except Exception as db_error:
                        logger.error(f"Failed to save rank to DB (parallel): {db_error}")
                        result['rank_change'] = None
                        result['previous_rank'] = None

                group_results[item_id] = result

                # 아이템 업데이트
                if result.get('success') and result.get('rank') is not None:
                    item.last_rank = result['rank']
                    item.last_error = None
                else:
                    item.last_rank = None
                    item.last_error = result.get('error_message')

                item.last_checked = result['search_time']

            return group_results

        # asyncio.run()으로 QThread에서 async 함수 실행
        try:
            group_results = asyncio.run(process_all_items())
        except Exception as e:
            logger.error(f"병렬 처리 중 오류: {e}")
            raise

        # 그룹 처리 완료 시 데이터 저장
        group.last_checked = datetime.now(timezone(timedelta(hours=9))).isoformat()
        if self.group_manager:
            self.group_manager.save_groups()

        logger.info(f"그룹 '{group.name}' 병렬 처리 완료: {len(group_results)}개 아이템")
        return group_results

    async def _process_single_item_async(
        self, item_id: str, item, item_index: int, total_items: int,
        base_progress: int, total_groups: int, group_name: str
    ) -> dict:
        """단일 아이템 비동기 처리"""
        # 진행률 업데이트
        item_progress_within_group = int((item_index / total_items) * 100)
        overall_progress = base_progress + int(item_progress_within_group / total_groups)

        self.progress.emit(
            overall_progress,
            f"{item.title} 순위 확인 중... (키워드: {item.keyword})",
            group_name
        )

        try:
            logger.info(f"  🔍 '{item.title}' 비동기 순위 검색 시작 (키워드: '{item.keyword}', URL: {item.url})")

            # 비동기 검색 실행
            result = await self.engine.search_instant_rank_async(item.keyword, item.url)

            logger.info(f"  ✅ '{item.title}' 비동기 순위 검색 완료: success={result.success if result else None}")

            if result:
                # 성공적인 결과 처리
                rank_data = {
                    'success': result.success,
                    'rank': result.rank,
                    'error_message': result.error_message,
                    'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                    'keyword': item.keyword,
                    'url': item.url,
                    'title': item.title,
                    'image_url': result.product_info.image_url if result.product_info else None
                }
            else:
                # 결과가 없는 경우
                rank_data = {
                    'success': False,
                    'rank': None,
                    'error_message': '검색 결과 없음',
                    'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                    'keyword': item.keyword,
                    'url': item.url,
                    'title': item.title
                }

            return rank_data

        except Exception as e:
            logger.error(f"아이템 '{item.title}' 비동기 순위 검색 실패: {e}")

            return {
                'success': False,
                'rank': None,
                'error_message': str(e),
                'search_time': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                'keyword': item.keyword,
                'url': item.url,
                'title': item.title
            }


class ScheduleManager:
    """스케줄 관리자 - 새로운 구조 지원"""

    def __init__(self, group_manager, engine):
        self.group_manager = group_manager
        self.engine = engine
        self.worker = None
        self.worker_thread = None

    def start_scheduled_tracking(self, selected_groups: List[str]) -> bool:
        """스케줄된 순위 추적 시작"""
        if self.is_running():
            logger.warning("이미 스케줄된 작업이 실행 중입니다")
            return False

        if not selected_groups:
            logger.warning("선택된 그룹이 없습니다")
            return False

        try:
            # 새로운 워커 생성
            self.worker = ScheduledRankWorker(
                self.group_manager,
                self.engine,
                selected_groups
            )

            self.worker_thread = QThread()
            self.worker.moveToThread(self.worker_thread)

            # 시그널 연결은 외부에서 처리
            self.worker_thread.started.connect(self.worker.run)

            # 워커 시작
            self.worker_thread.start()

            logger.info(f"스케줄된 순위 추적 시작: {len(selected_groups)}개 그룹")
            return True

        except Exception as e:
            logger.error(f"스케줄된 순위 추적 시작 실패: {e}")
            return False

    def stop_scheduled_tracking(self):
        """스케줄된 순위 추적 중지"""
        if self.worker:
            self.worker.stop()

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(5000)  # 5초 대기

        self.cleanup()

    def is_running(self) -> bool:
        """스케줄된 작업 실행 중 여부"""
        return (self.worker_thread is not None and
                self.worker_thread.isRunning())

    def cleanup(self):
        """리소스 정리"""
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None

        if self.worker:
            self.worker.deleteLater()
            self.worker = None

        logger.info("스케줄 관리자 리소스 정리 완료")