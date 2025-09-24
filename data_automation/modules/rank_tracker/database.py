"""
순위 추적 데이터베이스 관리
Context7 모범 사례를 적용한 SQLite 기반 순위 데이터 저장소
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from enum import Enum

from .rank_calculator import RankResult, RankStatus


class DatabaseError(Exception):
    """데이터베이스 관련 예외"""
    pass


class MigrationError(DatabaseError):
    """데이터베이스 마이그레이션 예외"""
    pass


@dataclass
class Keyword:
    """검색 키워드 엔티티"""
    id: Optional[int] = None
    query: str = ""
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone(timedelta(hours=9)))  # KST
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class TrackingTarget:
    """추적 대상 상품 엔티티"""
    id: Optional[int] = None
    product_id: str = ""
    name: Optional[str] = None
    mall_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    keyword: str = ""  # UI에서 필요한 키워드 속성 추가
    target_rank: int = 10  # UI에서 필요한 목표 순위 속성 추가
    current_rank: Optional[int] = None  # UI에서 필요한 현재 순위 속성 추가
    last_checked: Optional[datetime] = None  # UI에서 필요한 마지막 확인 시간 속성 추가
    store_name: Optional[str] = None  # UI에서 필요한 스토어명 속성 추가
    enabled: bool = True  # UI에서 필요한 활성화 상태 속성 추가 (active와 동일한 의미)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone(timedelta(hours=9)))  # KST
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class KeywordTargetRelation:
    """키워드-상품 연관관계 엔티티"""
    id: Optional[int] = None
    keyword_id: int = 0
    target_id: int = 0
    active: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone(timedelta(hours=9)))  # KST


@dataclass
class RankObservation:
    """순위 관찰 기록 엔티티"""
    id: Optional[int] = None
    keyword_id: int = 0
    target_id: int = 0
    rank: Optional[int] = None
    status: str = RankStatus.NOT_FOUND.value
    total_scanned: int = 0
    error_message: Optional[str] = None
    checked_at: Optional[datetime] = None

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now(timezone(timedelta(hours=9)))  # KST

    @classmethod
    def from_rank_result(
        cls,
        result: RankResult,
        keyword_id: int,
        target_id: int
    ) -> "RankObservation":
        """RankResult에서 RankObservation 생성"""
        return cls(
            keyword_id=keyword_id,
            target_id=target_id,
            rank=result.rank,
            status=result.status.value,
            total_scanned=result.total_scanned,
            error_message=result.error_message,
            checked_at=result.checked_at
        )


class RankDatabase:
    """
    순위 추적 데이터베이스
    Context7 모범 사례를 적용한 SQLite 기반 데이터 관리 시스템
    """

    # Context7 모범 사례: 데이터베이스 버전 관리
    DATABASE_VERSION = 1

    # DDL 스크립트들
    INITIAL_DDL = """
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        -- 메타데이터 테이블
        CREATE TABLE IF NOT EXISTS db_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- 검색 키워드 테이블
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL UNIQUE,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- 추적 대상 상품 테이블
        CREATE TABLE IF NOT EXISTS tracking_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL UNIQUE,
            name TEXT,
            mall_name TEXT,
            brand TEXT,
            category TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- 키워드-상품 연관관계 테이블
        CREATE TABLE IF NOT EXISTS keyword_target_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES tracking_targets (id) ON DELETE CASCADE,
            UNIQUE (keyword_id, target_id)
        );

        -- 순위 관찰 기록 테이블
        CREATE TABLE IF NOT EXISTS rank_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            rank INTEGER,
            status TEXT NOT NULL,
            total_scanned INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            checked_at TEXT NOT NULL,
            FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES tracking_targets (id) ON DELETE CASCADE
        );

        -- 인덱스 생성
        CREATE INDEX IF NOT EXISTS idx_keywords_query ON keywords (query);
        CREATE INDEX IF NOT EXISTS idx_keywords_active ON keywords (active);
        CREATE INDEX IF NOT EXISTS idx_targets_product_id ON tracking_targets (product_id);
        CREATE INDEX IF NOT EXISTS idx_targets_active ON tracking_targets (active);
        CREATE INDEX IF NOT EXISTS idx_relations_keyword_id ON keyword_target_relations (keyword_id);
        CREATE INDEX IF NOT EXISTS idx_relations_target_id ON keyword_target_relations (target_id);
        CREATE INDEX IF NOT EXISTS idx_observations_keyword_id ON rank_observations (keyword_id);
        CREATE INDEX IF NOT EXISTS idx_observations_target_id ON rank_observations (target_id);
        CREATE INDEX IF NOT EXISTS idx_observations_checked_at ON rank_observations (checked_at);
        CREATE INDEX IF NOT EXISTS idx_observations_rank ON rank_observations (rank);
    """

    def __init__(self, db_path: Union[str, Path], logger: Optional[logging.Logger] = None):
        """
        데이터베이스 초기화

        Args:
            db_path: 데이터베이스 파일 경로
            logger: 로거 인스턴스
        """
        self.db_path = Path(db_path)
        self.logger = logger or logging.getLogger(__name__)

        # Context7 모범 사례: 데이터베이스 초기화
        self._initialize_database()
        self.logger.info(f"순위 데이터베이스 초기화 완료: {self.db_path}")

    def _initialize_database(self) -> None:
        """데이터베이스 초기화 및 마이그레이션"""
        try:
            # 데이터베이스 파일 디렉토리 생성
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            with self._get_connection() as conn:
                # 초기 스키마 생성
                conn.executescript(self.INITIAL_DDL)

                # 버전 정보 저장/확인
                self._set_database_version(conn, self.DATABASE_VERSION)

                conn.commit()

        except Exception as e:
            raise DatabaseError(f"데이터베이스 초기화 실패: {e}")

    def _set_database_version(self, conn: sqlite3.Connection, version: int) -> None:
        """데이터베이스 버전 설정"""
        now = datetime.now(timezone(timedelta(hours=9))).isoformat()

        conn.execute("""
            INSERT OR REPLACE INTO db_metadata (key, value, created_at, updated_at)
            VALUES ('version', ?, ?, ?)
        """, (str(version), now, now))

    def _get_database_version(self, conn: sqlite3.Connection) -> int:
        """현재 데이터베이스 버전 조회"""
        cursor = conn.execute("""
            SELECT value FROM db_metadata WHERE key = 'version'
        """)
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    @contextmanager
    def _get_connection(self):
        """Context7 모범 사례: 안전한 데이터베이스 연결 관리"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태 결과
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"데이터베이스 연결 오류: {e}")
            raise DatabaseError(f"데이터베이스 연결 실패: {e}")
        finally:
            if conn:
                conn.close()

    def _datetime_to_str(self, dt: datetime) -> str:
        """datetime을 문자열로 변환"""
        return dt.isoformat() if dt else datetime.now(timezone(timedelta(hours=9))).isoformat()

    def _str_to_datetime(self, dt_str: str) -> datetime:
        """문자열을 datetime으로 변환"""
        return datetime.fromisoformat(dt_str) if dt_str else None

    # === 키워드 관리 ===

    def create_keyword(self, keyword: Keyword) -> int:
        """키워드 생성"""
        with self._get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO keywords (query, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    keyword.query,
                    1 if keyword.active else 0,
                    self._datetime_to_str(keyword.created_at),
                    self._datetime_to_str(keyword.updated_at)
                ))

                keyword_id = cursor.lastrowid
                conn.commit()

                self.logger.info(f"키워드 생성: '{keyword.query}' (ID: {keyword_id})")
                return keyword_id

            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"중복된 키워드: '{keyword.query}'")

    def get_keyword_by_id(self, keyword_id: int) -> Optional[Keyword]:
        """ID로 키워드 조회"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, query, active, created_at, updated_at
                FROM keywords WHERE id = ?
            """, (keyword_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return Keyword(
                id=row['id'],
                query=row['query'],
                active=bool(row['active']),
                created_at=self._str_to_datetime(row['created_at']),
                updated_at=self._str_to_datetime(row['updated_at'])
            )

    def get_keyword_by_query(self, query: str) -> Optional[Keyword]:
        """쿼리로 키워드 조회"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, query, active, created_at, updated_at
                FROM keywords WHERE query = ?
            """, (query,))

            row = cursor.fetchone()
            if not row:
                return None

            return Keyword(
                id=row['id'],
                query=row['query'],
                active=bool(row['active']),
                created_at=self._str_to_datetime(row['created_at']),
                updated_at=self._str_to_datetime(row['updated_at'])
            )

    def list_keywords(self, active_only: bool = True) -> List[Keyword]:
        """키워드 목록 조회"""
        with self._get_connection() as conn:
            query = "SELECT id, query, active, created_at, updated_at FROM keywords"
            params = []

            if active_only:
                query += " WHERE active = 1"

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [
                Keyword(
                    id=row['id'],
                    query=row['query'],
                    active=bool(row['active']),
                    created_at=self._str_to_datetime(row['created_at']),
                    updated_at=self._str_to_datetime(row['updated_at'])
                )
                for row in rows
            ]

    # === 추적 대상 관리 ===

    def create_target(self, target: TrackingTarget) -> int:
        """추적 대상 생성"""
        with self._get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO tracking_targets
                    (product_id, name, mall_name, brand, category, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    target.product_id,
                    target.name,
                    target.mall_name,
                    target.brand,
                    target.category,
                    1 if target.active else 0,
                    self._datetime_to_str(target.created_at),
                    self._datetime_to_str(target.updated_at)
                ))

                target_id = cursor.lastrowid
                conn.commit()

                self.logger.info(f"추적 대상 생성: '{target.product_id}' (ID: {target_id})")
                return target_id

            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"중복된 상품 ID: '{target.product_id}'")

    def get_target_by_product_id(self, product_id: str) -> Optional[TrackingTarget]:
        """상품 ID로 추적 대상 조회"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, product_id, name, mall_name, brand, category, active, created_at, updated_at
                FROM tracking_targets WHERE product_id = ?
            """, (product_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return TrackingTarget(
                id=row['id'],
                product_id=row['product_id'],
                name=row['name'],
                mall_name=row['mall_name'],
                brand=row['brand'],
                category=row['category'],
                active=bool(row['active']),
                created_at=self._str_to_datetime(row['created_at']),
                updated_at=self._str_to_datetime(row['updated_at'])
            )

    def list_targets(self, active_only: bool = True) -> List[TrackingTarget]:
        """추적 대상 목록 조회"""
        with self._get_connection() as conn:
            query = """
                SELECT id, product_id, name, mall_name, brand, category, active, created_at, updated_at
                FROM tracking_targets
            """
            params = []

            if active_only:
                query += " WHERE active = 1"

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [
                TrackingTarget(
                    id=row['id'],
                    product_id=row['product_id'],
                    name=row['name'],
                    mall_name=row['mall_name'],
                    brand=row['brand'],
                    category=row['category'],
                    active=bool(row['active']),
                    created_at=self._str_to_datetime(row['created_at']),
                    updated_at=self._str_to_datetime(row['updated_at'])
                )
                for row in rows
            ]

    # === 키워드-대상 연관관계 관리 ===

    def create_relation(self, keyword_id: int, target_id: int) -> int:
        """키워드-대상 연관관계 생성"""
        with self._get_connection() as conn:
            try:
                relation = KeywordTargetRelation(
                    keyword_id=keyword_id,
                    target_id=target_id
                )

                cursor = conn.execute("""
                    INSERT INTO keyword_target_relations (keyword_id, target_id, active, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    relation.keyword_id,
                    relation.target_id,
                    1 if relation.active else 0,
                    self._datetime_to_str(relation.created_at)
                ))

                relation_id = cursor.lastrowid
                conn.commit()

                self.logger.info(f"연관관계 생성: 키워드 {keyword_id} - 대상 {target_id} (ID: {relation_id})")
                return relation_id

            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"중복된 연관관계: 키워드 {keyword_id} - 대상 {target_id}")

    def get_targets_for_keyword(self, keyword_id: int) -> List[TrackingTarget]:
        """특정 키워드의 추적 대상 목록"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT t.id, t.product_id, t.name, t.mall_name, t.brand, t.category,
                       t.active, t.created_at, t.updated_at
                FROM tracking_targets t
                JOIN keyword_target_relations r ON t.id = r.target_id
                WHERE r.keyword_id = ? AND r.active = 1 AND t.active = 1
                ORDER BY t.created_at DESC
            """, (keyword_id,))

            rows = cursor.fetchall()
            return [
                TrackingTarget(
                    id=row['id'],
                    product_id=row['product_id'],
                    name=row['name'],
                    mall_name=row['mall_name'],
                    brand=row['brand'],
                    category=row['category'],
                    active=bool(row['active']),
                    created_at=self._str_to_datetime(row['created_at']),
                    updated_at=self._str_to_datetime(row['updated_at'])
                )
                for row in rows
            ]

    # === 순위 기록 관리 ===

    def save_rank_observation(self, observation: RankObservation) -> int:
        """순위 관찰 기록 저장"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO rank_observations
                (keyword_id, target_id, rank, status, total_scanned, error_message, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                observation.keyword_id,
                observation.target_id,
                observation.rank,
                observation.status,
                observation.total_scanned,
                observation.error_message,
                self._datetime_to_str(observation.checked_at)
            ))

            observation_id = cursor.lastrowid
            conn.commit()

            self.logger.debug(f"순위 기록 저장: ID {observation_id}")
            return observation_id

    def save_batch_observations(self, observations: List[RankObservation]) -> List[int]:
        """순위 관찰 기록 배치 저장"""
        if not observations:
            return []

        with self._get_connection() as conn:
            observation_ids = []

            try:
                for obs in observations:
                    cursor = conn.execute("""
                        INSERT INTO rank_observations
                        (keyword_id, target_id, rank, status, total_scanned, error_message, checked_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        obs.keyword_id,
                        obs.target_id,
                        obs.rank,
                        obs.status,
                        obs.total_scanned,
                        obs.error_message,
                        self._datetime_to_str(obs.checked_at)
                    ))
                    observation_ids.append(cursor.lastrowid)

                conn.commit()
                self.logger.info(f"배치 순위 기록 저장 완료: {len(observations)}건")

            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"배치 저장 실패: {e}")

            return observation_ids

    def get_latest_ranks(self, keyword_id: int, limit: int = 100) -> List[RankObservation]:
        """특정 키워드의 최신 순위 기록"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, keyword_id, target_id, rank, status, total_scanned,
                       error_message, checked_at
                FROM rank_observations
                WHERE keyword_id = ?
                ORDER BY checked_at DESC
                LIMIT ?
            """, (keyword_id, limit))

            rows = cursor.fetchall()
            return [
                RankObservation(
                    id=row['id'],
                    keyword_id=row['keyword_id'],
                    target_id=row['target_id'],
                    rank=row['rank'],
                    status=row['status'],
                    total_scanned=row['total_scanned'],
                    error_message=row['error_message'],
                    checked_at=self._str_to_datetime(row['checked_at'])
                )
                for row in rows
            ]

    def get_rank_history(
        self,
        keyword_id: int,
        target_id: int,
        days: int = 7
    ) -> List[RankObservation]:
        """특정 키워드-상품의 순위 히스토리"""
        with self._get_connection() as conn:
            since_date = (datetime.now(timezone(timedelta(hours=9))) - timedelta(days=days)).isoformat()

            cursor = conn.execute("""
                SELECT id, keyword_id, target_id, rank, status, total_scanned,
                       error_message, checked_at
                FROM rank_observations
                WHERE keyword_id = ? AND target_id = ? AND checked_at >= ?
                ORDER BY checked_at ASC
            """, (keyword_id, target_id, since_date))

            rows = cursor.fetchall()
            return [
                RankObservation(
                    id=row['id'],
                    keyword_id=row['keyword_id'],
                    target_id=row['target_id'],
                    rank=row['rank'],
                    status=row['status'],
                    total_scanned=row['total_scanned'],
                    error_message=row['error_message'],
                    checked_at=self._str_to_datetime(row['checked_at'])
                )
                for row in rows
            ]

    # === 통계 및 인사이트 ===

    def get_rank_statistics(self, keyword_id: int, days: int = 30) -> Dict[str, Any]:
        """순위 통계 조회"""
        with self._get_connection() as conn:
            since_date = (datetime.now(timezone(timedelta(hours=9))) - timedelta(days=days)).isoformat()

            # 기본 통계
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_observations,
                    COUNT(rank) as ranked_observations,
                    AVG(rank) as avg_rank,
                    MIN(rank) as best_rank,
                    MAX(rank) as worst_rank,
                    AVG(total_scanned) as avg_scanned
                FROM rank_observations
                WHERE keyword_id = ? AND checked_at >= ?
            """, (keyword_id, since_date))

            stats = dict(cursor.fetchone())

            # 상태별 분포
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM rank_observations
                WHERE keyword_id = ? AND checked_at >= ?
                GROUP BY status
            """, (keyword_id, since_date))

            status_distribution = {row['status']: row['count'] for row in cursor.fetchall()}
            stats['status_distribution'] = status_distribution

            return stats

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Context7 모범 사례: 오래된 데이터 정리"""
        with self._get_connection() as conn:
            cutoff_date = (datetime.now(timezone(timedelta(hours=9))) - timedelta(days=days_to_keep)).isoformat()

            cursor = conn.execute("""
                DELETE FROM rank_observations
                WHERE checked_at < ?
            """, (cutoff_date,))

            deleted_count = cursor.rowcount
            conn.commit()

            self.logger.info(f"오래된 데이터 정리 완료: {deleted_count}건 삭제")
            return deleted_count

    # UI 호환성을 위한 편의 메소드들
    def get_active_targets(self) -> List[TrackingTarget]:
        """활성 추적 대상 목록 반환 (UI 호환성)"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT tt.id, tt.product_id, tt.name, tt.mall_name, tt.brand, tt.category,
                       tt.active, tt.created_at, tt.updated_at, k.query as keyword,
                       COALESCE(MAX(ro.checked_at), tt.created_at) as last_checked,
                       ro_latest.rank as current_rank
                FROM tracking_targets tt
                JOIN keyword_target_relations r ON tt.id = r.target_id
                JOIN keywords k ON r.keyword_id = k.id
                LEFT JOIN rank_observations ro ON r.keyword_id = ro.keyword_id AND r.target_id = ro.target_id
                LEFT JOIN (
                    SELECT keyword_id, target_id, rank, ROW_NUMBER() OVER (PARTITION BY keyword_id, target_id ORDER BY checked_at DESC) as rn
                    FROM rank_observations
                ) ro_latest ON r.keyword_id = ro_latest.keyword_id AND r.target_id = ro_latest.target_id AND ro_latest.rn = 1
                WHERE tt.active = 1 AND r.active = 1
                GROUP BY tt.id, tt.product_id, tt.name, tt.mall_name, tt.brand, tt.category,
                         tt.active, tt.created_at, tt.updated_at, k.query, ro_latest.rank
                ORDER BY tt.created_at DESC
            """)

            rows = cursor.fetchall()
            return [
                TrackingTarget(
                    id=row['id'],
                    product_id=row['product_id'],
                    name=row['name'],
                    mall_name=row['mall_name'],
                    brand=row['brand'],
                    category=row['category'],
                    keyword=row['keyword'],  # 키워드 정보 추가
                    target_rank=10,  # 기본 목표 순위 설정
                    current_rank=row['current_rank'] if row['current_rank'] else None,  # 현재 순위 추가
                    last_checked=self._str_to_datetime(row['last_checked']) if row['last_checked'] else None,
                    store_name=row['mall_name'],  # mall_name을 store_name으로도 사용
                    enabled=bool(row['active']),  # active를 enabled로도 매핑
                    active=bool(row['active']),
                    created_at=self._str_to_datetime(row['created_at']),
                    updated_at=self._str_to_datetime(row['updated_at'])
                )
                for row in rows
            ]

    def add_tracking_target(self, product_id: str, keyword: str, target_rank: int, store_name: str) -> int:
        """추적 대상 추가 (UI 호환성)"""
        # 키워드 생성 또는 조회
        keyword_obj = self.get_keyword_by_query(keyword)
        if not keyword_obj:
            keyword_obj = Keyword(query=keyword, active=True)
            keyword_id = self.create_keyword(keyword_obj)
        else:
            keyword_id = keyword_obj.id

        # 타겟 생성
        target = TrackingTarget(
            product_id=product_id,
            name=f"상품_{product_id}",
            mall_name=store_name,
            active=True
        )
        target_id = self.create_target(target)

        # 관계 생성
        relation_id = self.create_relation(keyword_id, target_id)

        self.logger.info(f"추적 대상 추가 완료: {product_id} - {keyword}")
        return target_id

    def remove_tracking_target(self, product_id: str, keyword: str):
        """추적 대상 제거 (UI 호환성)"""
        # 키워드 조회
        keyword_obj = self.get_keyword_by_query(keyword)
        if not keyword_obj:
            raise ValueError(f"키워드를 찾을 수 없습니다: {keyword}")

        # 타겟 조회
        target = self.get_target_by_product_id(product_id)
        if not target:
            raise ValueError(f"추적 대상을 찾을 수 없습니다: {product_id}")

        # 타겟을 비활성화
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tracking_targets SET active = 0, updated_at = ? WHERE id = ?",
                (self._datetime_to_str(datetime.now(timezone.utc)), target.id)
            )

            # 키워드-타겟 관계도 비활성화 (테이블이 존재하는 경우)
            cursor.execute("""
                UPDATE keyword_target_relations
                SET active = 0, updated_at = ?
                WHERE keyword_id = ? AND target_id = ?
            """, (
                self._datetime_to_str(datetime.now(timezone.utc)),
                keyword_obj.id,
                target.id
            ))

            conn.commit()

        self.logger.info(f"추적 대상 제거 완료: {product_id} - {keyword}")

    def save_rank_result(self, result, keyword_id: int, target_id: int):
        """순위 결과 저장 (UI 호환성)"""
        # RankResult를 RankObservation으로 변환
        observation = RankObservation.from_rank_result(result, keyword_id, target_id)
        return self.save_rank_observation(observation)

    def get_recent_results(self, limit: int = 10) -> List:
        """최근 순위 결과 조회 (UI 호환성)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ro.id, ro.keyword_id, ro.target_id, ro.rank,
                       ro.total_scanned, ro.status, ro.checked_at,
                       k.query as keyword, tt.product_id, tt.name as product_name
                FROM rank_observations ro
                JOIN keywords k ON ro.keyword_id = k.id
                JOIN tracking_targets tt ON ro.target_id = tt.id
                ORDER BY ro.checked_at DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                observation = RankObservation(
                    id=row[0],
                    keyword_id=row[1],
                    target_id=row[2],
                    rank=row[3],  # rank column
                    total_scanned=row[4],  # total_scanned column
                    status=row[5],  # status column
                    checked_at=self._str_to_datetime(row[6])  # checked_at column
                )
                # 추가 정보 설정 (동적 속성)
                observation.status = row[5]
                observation.keyword = row[7]
                observation.product_id = row[8]
                observation.product_name = row[9]
                results.append(observation)

            return results