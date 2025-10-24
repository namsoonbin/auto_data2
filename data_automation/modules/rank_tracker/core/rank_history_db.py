"""
순위 히스토리 데이터베이스 - SQLite 기반
Context7 2025: 시계열 데이터 저장 및 분석
"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def get_default_db_path() -> Path:
    """
    기본 데이터베이스 경로 반환 (exe 파일 위치 기준)
    config.BASE_DIR을 활용하여 일관된 경로 제공

    Context7 2025: 안전한 fallback 경로 사용
    """
    try:
        from modules import config
        return config.BASE_DIR / "rank_history.db"
    except ImportError:
        # config 모듈을 찾을 수 없는 경우 현재 작업 디렉토리 기준
        logger.warning("config.BASE_DIR을 찾을 수 없어 현재 작업 디렉토리 사용")
        return Path.cwd() / "rank_history.db"


class RankHistoryDB:
    """순위 히스토리를 관리하는 SQLite 데이터베이스"""

    def __init__(self, db_path: Optional[str] = None):
        """
        데이터베이스 초기화

        Args:
            db_path: SQLite 데이터베이스 파일 경로 (None이면 exe 기준 기본 경로 사용)
        """
        if db_path is None:
            self.db_path = get_default_db_path()
        else:
            self.db_path = Path(db_path)

        # 부모 디렉토리가 없으면 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        logger.info(f"RankHistoryDB initialized: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """데이터베이스 스키마 초기화"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 순위 히스토리 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rank_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    rank INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    checked_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스 생성 (조회 성능 향상)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_item_checked
                ON rank_history(item_id, checked_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_group_checked
                ON rank_history(group_id, checked_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keyword_checked
                ON rank_history(keyword, checked_at DESC)
            """)

            logger.info("Database schema initialized")

    def save_rank(
        self,
        item_id: str,
        group_id: str,
        product_id: str,
        keyword: str,
        url: str,
        title: str,
        rank: Optional[int],
        success: bool,
        error_message: Optional[str] = None,
        checked_at: Optional[str] = None
    ) -> bool:
        """
        순위 기록 저장

        Args:
            item_id: 아이템 ID
            group_id: 그룹 ID
            product_id: 네이버 상품 ID
            keyword: 검색 키워드
            url: 상품 URL
            title: 상품 제목
            rank: 순위 (None이면 미발견)
            success: 성공 여부
            error_message: 오류 메시지 (실패 시)
            checked_at: 검색 시간 (ISO format, None이면 현재 시간)

        Returns:
            저장 성공 여부
        """
        try:
            if checked_at is None:
                checked_at = datetime.now(timezone(timedelta(hours=9))).isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO rank_history
                    (item_id, group_id, product_id, keyword, url, title,
                     rank, success, error_message, checked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id, group_id, product_id, keyword, url, title,
                    rank, success, error_message, checked_at
                ))

                logger.debug(f"Saved rank: {title} (keyword: {keyword}, rank: {rank})")
                return True

        except Exception as e:
            logger.error(f"Failed to save rank: {e}")
            return False

    def save_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        여러 순위 기록을 일괄 저장

        Args:
            records: 순위 기록 리스트 (각 record는 save_rank의 인자와 동일)

        Returns:
            저장 성공한 레코드 수
        """
        saved_count = 0

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for record in records:
                    checked_at = record.get('checked_at')
                    if checked_at is None:
                        checked_at = datetime.now(timezone(timedelta(hours=9))).isoformat()

                    cursor.execute("""
                        INSERT INTO rank_history
                        (item_id, group_id, product_id, keyword, url, title,
                         rank, success, error_message, checked_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['item_id'],
                        record['group_id'],
                        record['product_id'],
                        record['keyword'],
                        record['url'],
                        record['title'],
                        record.get('rank'),
                        record['success'],
                        record.get('error_message'),
                        checked_at
                    ))
                    saved_count += 1

                logger.info(f"Batch saved: {saved_count} records")

        except Exception as e:
            logger.error(f"Batch save failed: {e}")

        return saved_count

    def get_history(
        self,
        item_id: str,
        days: int = 7,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        아이템의 순위 히스토리 조회

        Args:
            item_id: 아이템 ID
            days: 조회할 일수 (기본 7일)
            limit: 최대 레코드 수 (None이면 제한 없음)

        Returns:
            순위 기록 리스트 (최신순)
        """
        try:
            cutoff_date = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=days)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT * FROM rank_history
                    WHERE item_id = ? AND checked_at >= ?
                    ORDER BY checked_at DESC
                """

                if limit:
                    query += f" LIMIT {limit}"

                cursor.execute(query, (item_id, cutoff_date.isoformat()))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def get_group_history(
        self,
        group_id: str,
        days: int = 7
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        그룹 내 모든 아이템의 순위 히스토리 조회

        Args:
            group_id: 그룹 ID
            days: 조회할 일수

        Returns:
            {item_id: [순위 기록들]} 형태의 딕셔너리
        """
        try:
            cutoff_date = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=days)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM rank_history
                    WHERE group_id = ? AND checked_at >= ?
                    ORDER BY item_id, checked_at DESC
                """, (group_id, cutoff_date.isoformat()))

                rows = cursor.fetchall()

                # item_id별로 그룹화
                result = {}
                for row in rows:
                    item_id = row['item_id']
                    if item_id not in result:
                        result[item_id] = []
                    result[item_id].append(dict(row))

                return result

        except Exception as e:
            logger.error(f"Failed to get group history: {e}")
            return {}

    def get_latest_rank(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        아이템의 최신 순위 조회

        Args:
            item_id: 아이템 ID

        Returns:
            최신 순위 기록 (없으면 None)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM rank_history
                    WHERE item_id = ?
                    ORDER BY checked_at DESC
                    LIMIT 1
                """, (item_id,))

                row = cursor.fetchone()
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to get latest rank: {e}")
            return None

    def get_rank_change(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        전일 대비 순위 변화 계산

        Args:
            item_id: 아이템 ID

        Returns:
            {
                'current_rank': int,
                'previous_rank': int,
                'change': int (음수면 하락, 양수면 상승),
                'current_checked_at': str,
                'previous_checked_at': str
            }
            또는 None (데이터 부족 시)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT rank, checked_at, success
                    FROM rank_history
                    WHERE item_id = ? AND success = 1
                    ORDER BY checked_at DESC
                    LIMIT 2
                """, (item_id,))

                rows = cursor.fetchall()

                if len(rows) < 2:
                    # 데이터가 부족하면 None 반환
                    return None

                current = dict(rows[0])
                previous = dict(rows[1])

                if current['rank'] is None or previous['rank'] is None:
                    return None

                # 순위가 낮아지면 음수 (하락), 높아지면 양수 (상승)
                change = previous['rank'] - current['rank']

                return {
                    'current_rank': current['rank'],
                    'previous_rank': previous['rank'],
                    'change': change,
                    'current_checked_at': current['checked_at'],
                    'previous_checked_at': previous['checked_at']
                }

        except Exception as e:
            logger.error(f"Failed to get rank change: {e}")
            return None

    def get_statistics(
        self,
        item_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        기간별 통계 계산

        Args:
            item_id: 아이템 ID
            start_date: 시작일 (None이면 7일 전)
            end_date: 종료일 (None이면 오늘)

        Returns:
            {
                'avg_rank': float,
                'min_rank': int,
                'max_rank': int,
                'total_checks': int,
                'success_rate': float,
                'rank_trend': str ('up'/'down'/'stable')
            }
        """
        try:
            if end_date is None:
                end_date = date.today()
            if start_date is None:
                start_date = end_date - timedelta(days=7)

            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 기본 통계
                cursor.execute("""
                    SELECT
                        AVG(rank) as avg_rank,
                        MIN(rank) as min_rank,
                        MAX(rank) as max_rank,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                    FROM rank_history
                    WHERE item_id = ?
                      AND checked_at BETWEEN ? AND ?
                      AND rank IS NOT NULL
                """, (item_id, start_dt.isoformat(), end_dt.isoformat()))

                row = cursor.fetchone()

                if not row or row['total_checks'] == 0:
                    return {
                        'avg_rank': None,
                        'min_rank': None,
                        'max_rank': None,
                        'total_checks': 0,
                        'success_rate': 0.0,
                        'rank_trend': 'stable'
                    }

                stats = dict(row)

                # 성공률 계산
                success_rate = (stats['success_count'] / stats['total_checks']) * 100

                # 순위 추세 계산 (첫 날 vs 마지막 날)
                cursor.execute("""
                    SELECT rank FROM rank_history
                    WHERE item_id = ?
                      AND checked_at BETWEEN ? AND ?
                      AND success = 1
                      AND rank IS NOT NULL
                    ORDER BY checked_at ASC
                    LIMIT 1
                """, (item_id, start_dt.isoformat(), end_dt.isoformat()))

                first_row = cursor.fetchone()

                cursor.execute("""
                    SELECT rank FROM rank_history
                    WHERE item_id = ?
                      AND checked_at BETWEEN ? AND ?
                      AND success = 1
                      AND rank IS NOT NULL
                    ORDER BY checked_at DESC
                    LIMIT 1
                """, (item_id, start_dt.isoformat(), end_dt.isoformat()))

                last_row = cursor.fetchone()

                rank_trend = 'stable'
                if first_row and last_row:
                    first_rank = first_row['rank']
                    last_rank = last_row['rank']

                    if last_rank < first_rank - 5:  # 순위 상승 (숫자 감소)
                        rank_trend = 'up'
                    elif last_rank > first_rank + 5:  # 순위 하락 (숫자 증가)
                        rank_trend = 'down'

                return {
                    'avg_rank': round(stats['avg_rank'], 1) if stats['avg_rank'] else None,
                    'min_rank': stats['min_rank'],
                    'max_rank': stats['max_rank'],
                    'total_checks': stats['total_checks'],
                    'success_rate': round(success_rate, 1),
                    'rank_trend': rank_trend
                }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                'avg_rank': None,
                'min_rank': None,
                'max_rank': None,
                'total_checks': 0,
                'success_rate': 0.0,
                'rank_trend': 'stable'
            }

    def get_daily_summary(
        self,
        group_id: str,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        특정 날짜의 일별 요약 조회

        Args:
            group_id: 그룹 ID
            target_date: 조회할 날짜 (None이면 오늘)

        Returns:
            각 아이템의 당일 마지막 순위 리스트
        """
        try:
            if target_date is None:
                target_date = date.today()

            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 각 아이템의 당일 마지막 기록
                cursor.execute("""
                    SELECT h1.*
                    FROM rank_history h1
                    INNER JOIN (
                        SELECT item_id, MAX(checked_at) as max_checked
                        FROM rank_history
                        WHERE group_id = ?
                          AND checked_at BETWEEN ? AND ?
                        GROUP BY item_id
                    ) h2 ON h1.item_id = h2.item_id
                        AND h1.checked_at = h2.max_checked
                    ORDER BY h1.title
                """, (group_id, start_dt.isoformat(), end_dt.isoformat()))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get daily summary: {e}")
            return []

    def cleanup_old_records(self, keep_days: int = 90) -> int:
        """
        오래된 기록 삭제

        Args:
            keep_days: 보관할 일수 (기본 90일)

        Returns:
            삭제된 레코드 수
        """
        try:
            cutoff_date = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=keep_days)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM rank_history
                    WHERE checked_at < ?
                """, (cutoff_date.isoformat(),))

                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old records (older than {keep_days} days)")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0

    def vacuum(self):
        """데이터베이스 최적화 (VACUUM)"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            logger.info("Database vacuumed")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
