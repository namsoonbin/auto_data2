"""
순위 추적 스케줄러
Context7 모범 사례를 적용한 자동화된 순위 모니터링 시스템
"""

import time
import logging
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Thread, Event, Lock
import queue

from .naver_api import NaverShopAPI, APIError, RateLimitError
from .rank_calculator import RankCalculator, BatchRankResult, RankResult
from .database import RankDatabase, Keyword, TrackingTarget, RankObservation


class SchedulerStatus(Enum):
    """스케줄러 상태"""
    IDLE = "idle"                  # 유휴
    RUNNING = "running"           # 실행 중
    PAUSED = "paused"             # 일시 정지
    STOPPING = "stopping"        # 종료 중
    ERROR = "error"               # 오류 상태


class JobStatus(Enum):
    """작업 상태"""
    PENDING = "pending"           # 대기 중
    RUNNING = "running"           # 실행 중
    COMPLETED = "completed"       # 완료
    FAILED = "failed"             # 실패
    SKIPPED = "skipped"           # 건너뜀


@dataclass
class ScheduleConfig:
    """스케줄 설정"""
    interval_minutes: int = 10           # 실행 간격 (분)
    max_concurrent_jobs: int = 3         # 최대 동시 작업 수
    retry_attempts: int = 3              # 재시도 횟수
    retry_delay_seconds: int = 60        # 재시도 지연 (초)
    error_threshold: int = 5             # 연속 오류 임계값
    pause_on_error: bool = True          # 오류 시 일시 정지 여부

    def __post_init__(self):
        # Context7 모범 사례: 입력값 검증
        if not (1 <= self.interval_minutes <= 1440):  # 1분 ~ 24시간
            raise ValueError("interval_minutes는 1-1440 범위여야 합니다")
        if not (1 <= self.max_concurrent_jobs <= 10):
            raise ValueError("max_concurrent_jobs는 1-10 범위여야 합니다")


@dataclass
class ScheduledJob:
    """스케줄된 작업"""
    id: str
    keyword_id: int
    keyword_query: str
    target_ids: List[int]
    target_product_ids: List[str]
    scheduled_at: datetime
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[BatchRankResult] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class JobResult:
    """작업 결과"""
    job_id: str
    keyword_id: int
    success: bool
    rank_results: List[RankResult]
    execution_time: float
    error_message: Optional[str] = None


class RankScheduler:
    """
    순위 추적 스케줄러
    Context7 모범 사례를 적용한 백그라운드 순위 모니터링 시스템
    """

    def __init__(
        self,
        api_client: NaverShopAPI,
        database: RankDatabase,
        config: ScheduleConfig,
        result_callback: Optional[Callable[[JobResult], None]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        스케줄러 초기화

        Args:
            api_client: 네이버 API 클라이언트
            database: 순위 데이터베이스
            config: 스케줄 설정
            result_callback: 결과 콜백 함수
            logger: 로거 인스턴스
        """
        self.api_client = api_client
        self.database = database
        self.config = config
        self.result_callback = result_callback
        self.logger = logger or logging.getLogger(__name__)

        # Context7 모범 사례: 스레드 안전 상태 관리
        self._status = SchedulerStatus.IDLE
        self._status_lock = Lock()
        self._stop_event = Event()
        self._pause_event = Event()

        # 작업 관리
        self._job_queue = queue.PriorityQueue()
        self._active_jobs: Dict[str, ScheduledJob] = {}
        self._completed_jobs: List[ScheduledJob] = []
        self._job_counter = 0
        self._jobs_lock = Lock()

        # 스케줄러 스레드
        self._scheduler_thread: Optional[Thread] = None
        self._worker_threads: List[Thread] = []

        # 에러 추적
        self._consecutive_errors = 0
        self._last_error_time: Optional[datetime] = None

        # 순위 계산기
        self.rank_calculator = RankCalculator(api_client, logger=logger)

        self.logger.info(f"순위 스케줄러 초기화: 간격 {config.interval_minutes}분, 최대 동시작업 {config.max_concurrent_jobs}개")

    @property
    def status(self) -> SchedulerStatus:
        """현재 상태"""
        with self._status_lock:
            return self._status

    def _set_status(self, new_status: SchedulerStatus) -> None:
        """상태 변경"""
        with self._status_lock:
            old_status = self._status
            self._status = new_status
            if old_status != new_status:
                self.logger.info(f"스케줄러 상태 변경: {old_status.value} → {new_status.value}")

    def start(self) -> None:
        """스케줄러 시작"""
        if self.status != SchedulerStatus.IDLE:
            self.logger.warning(f"이미 실행 중인 상태: {self.status.value}")
            return

        self.logger.info("순위 추적 스케줄러 시작")

        # 이벤트 초기화
        self._stop_event.clear()
        self._pause_event.clear()

        # 상태 변경
        self._set_status(SchedulerStatus.RUNNING)

        # 메인 스케줄러 스레드 시작
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

        # 워커 스레드들 시작
        self._worker_threads.clear()
        for i in range(self.config.max_concurrent_jobs):
            worker_thread = Thread(target=self._worker_loop, args=(i,), daemon=True)
            worker_thread.start()
            self._worker_threads.append(worker_thread)

    def stop(self, timeout: float = 30.0) -> None:
        """스케줄러 중지"""
        if self.status == SchedulerStatus.IDLE:
            return

        self.logger.info("순위 추적 스케줄러 중지 중...")
        self._set_status(SchedulerStatus.STOPPING)

        # 중지 이벤트 설정
        self._stop_event.set()

        # 스케줄러 스레드 종료 대기
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=timeout)

        # 워커 스레드들 종료 대기
        for worker_thread in self._worker_threads:
            if worker_thread.is_alive():
                worker_thread.join(timeout=timeout / len(self._worker_threads))

        self._set_status(SchedulerStatus.IDLE)
        self.logger.info("순위 추적 스케줄러 중지 완료")

    def pause(self) -> None:
        """스케줄러 일시 정지"""
        if self.status != SchedulerStatus.RUNNING:
            return

        self.logger.info("순위 추적 스케줄러 일시 정지")
        self._set_status(SchedulerStatus.PAUSED)
        self._pause_event.set()

    def resume(self) -> None:
        """스케줄러 재개"""
        if self.status != SchedulerStatus.PAUSED:
            return

        self.logger.info("순위 추적 스케줄러 재개")
        self._pause_event.clear()
        self._consecutive_errors = 0  # 에러 카운트 리셋
        self._set_status(SchedulerStatus.RUNNING)

    def _scheduler_loop(self) -> None:
        """메인 스케줄러 루프"""
        self.logger.info("스케줄러 메인 루프 시작")

        next_run_time = datetime.now()

        while not self._stop_event.is_set():
            try:
                # 일시 정지 확인
                if self._pause_event.is_set():
                    time.sleep(1)
                    continue

                current_time = datetime.now()

                # 스케줄 시간 확인
                if current_time >= next_run_time:
                    self.logger.info("스케줄된 순위 추적 작업 생성 중...")

                    # 활성 키워드들에 대한 작업 생성
                    jobs_created = self._create_scheduled_jobs()

                    if jobs_created > 0:
                        self.logger.info(f"{jobs_created}개 작업을 큐에 추가")
                        next_run_time = current_time + timedelta(minutes=self.config.interval_minutes)
                    else:
                        self.logger.info("생성할 작업이 없습니다")
                        next_run_time = current_time + timedelta(minutes=5)  # 5분 후 재확인

                time.sleep(10)  # 10초마다 확인

            except Exception as e:
                self.logger.error(f"스케줄러 루프 오류: {e}")
                self._handle_error(e)
                time.sleep(60)  # 오류 시 1분 대기

        self.logger.info("스케줄러 메인 루프 종료")

    def _create_scheduled_jobs(self) -> int:
        """스케줄된 작업들 생성"""
        try:
            # 활성 키워드 목록 조회
            keywords = self.database.list_keywords(active_only=True)
            jobs_created = 0

            for keyword in keywords:
                # 중복 작업 억제 - 키워드별 활성 작업 확인
                if self._keyword_active(keyword.id):
                    self.logger.debug(f"키워드 '{keyword.query}' 활성 작업 존재 → 건너뜀")
                    continue

                # 해당 키워드의 추적 대상들 조회
                targets = self.database.get_targets_for_keyword(keyword.id)

                if not targets:
                    self.logger.debug(f"키워드 '{keyword.query}'에 추적 대상이 없음")
                    continue

                # 작업 생성
                job = ScheduledJob(
                    id=self._generate_job_id(),
                    keyword_id=keyword.id,
                    keyword_query=keyword.query,
                    target_ids=[t.id for t in targets],
                    target_product_ids=[t.product_id for t in targets],
                    scheduled_at=datetime.now(timezone(timedelta(hours=9)))  # KST
                )

                # 우선순위 큐에 추가 (현재 시간 기준) + 타이브레이커
                priority = int(job.scheduled_at.timestamp())
                self._job_counter += 1
                seq = self._job_counter
                self._job_queue.put((priority, seq, job))

                jobs_created += 1
                self.logger.debug(f"작업 생성: '{keyword.query}' - {len(targets)}개 대상")

            return jobs_created

        except Exception as e:
            self.logger.error(f"작업 생성 중 오류: {e}")
            return 0

    def _worker_loop(self, worker_id: int) -> None:
        """워커 스레드 루프"""
        self.logger.debug(f"워커 {worker_id} 시작")

        while not self._stop_event.is_set():
            try:
                # 일시 정지 확인
                if self._pause_event.is_set():
                    time.sleep(1)
                    continue

                # 작업 큐에서 작업 가져오기 (타임아웃 1초)
                try:
                    priority, seq, job = self._job_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # 작업 실행
                self._execute_job(job, worker_id)

                # 작업 완료 표시
                self._job_queue.task_done()

            except Exception as e:
                self.logger.error(f"워커 {worker_id} 오류: {e}")
                time.sleep(5)

        self.logger.debug(f"워커 {worker_id} 종료")

    def _execute_job(self, job: ScheduledJob, worker_id: int) -> None:
        """작업 실행"""
        job_start_time = time.time()

        # 작업 상태 업데이트
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone(timedelta(hours=9)))

        with self._jobs_lock:
            self._active_jobs[job.id] = job

        self.logger.info(f"[워커{worker_id}] 작업 시작: '{job.keyword_query}' ({len(job.target_product_ids)}개 상품)")

        try:
            # 순위 계산 실행
            batch_result = self.rank_calculator.calculate_batch_ranks(
                keyword=job.keyword_query,
                product_ids=job.target_product_ids,
                early_stop=True
            )

            job.result = batch_result

            # 데이터베이스에 결과 저장
            observations = []
            target_map = {target_id: product_id for target_id, product_id in
                         zip(job.target_ids, job.target_product_ids)}

            for result in batch_result.results:
                # 해당 상품의 target_id 찾기
                target_id = None
                for tid, pid in target_map.items():
                    if pid == result.product_id:
                        target_id = tid
                        break

                if target_id:
                    observation = RankObservation.from_rank_result(
                        result, job.keyword_id, target_id
                    )
                    observations.append(observation)

            if observations:
                self.database.save_batch_observations(observations)

            # 작업 완료
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone(timedelta(hours=9)))

            execution_time = time.time() - job_start_time

            # 결과 콜백 호출
            if self.result_callback:
                job_result = JobResult(
                    job_id=job.id,
                    keyword_id=job.keyword_id,
                    success=True,
                    rank_results=batch_result.results,
                    execution_time=execution_time
                )
                try:
                    self.result_callback(job_result)
                except Exception as e:
                    self.logger.error(f"결과 콜백 오류: {e}")

            # 성공한 경우 에러 카운트 리셋
            self._consecutive_errors = 0

            self.logger.info(
                f"[워커{worker_id}] 작업 완료: '{job.keyword_query}' "
                f"(성공률: {batch_result.success_rate:.1%}, "
                f"소요시간: {execution_time:.1f}초)"
            )

        except Exception as e:
            # 작업 실패
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone(timedelta(hours=9)))

            self.logger.error(f"[워커{worker_id}] 작업 실패: '{job.keyword_query}' - {e}")

            # 재시도 로직
            if job.retry_count < self.config.retry_attempts:
                job.retry_count += 1
                job.status = JobStatus.PENDING

                # 재시도 큐에 추가 (지연 후) + 타이브레이커
                retry_time = datetime.now() + timedelta(seconds=self.config.retry_delay_seconds)
                priority = int(retry_time.timestamp())
                self._job_counter += 1
                seq = self._job_counter
                self._job_queue.put((priority, seq, job))

                self.logger.info(
                    f"작업 재시도 예약: '{job.keyword_query}' "
                    f"({job.retry_count}/{self.config.retry_attempts})"
                )
            else:
                # 최대 재시도 횟수 초과
                execution_time = time.time() - job_start_time

                if self.result_callback:
                    job_result = JobResult(
                        job_id=job.id,
                        keyword_id=job.keyword_id,
                        success=False,
                        rank_results=[],
                        execution_time=execution_time,
                        error_message=str(e)
                    )
                    try:
                        self.result_callback(job_result)
                    except Exception as cb_error:
                        self.logger.error(f"결과 콜백 오류: {cb_error}")

                self._handle_error(e)

        finally:
            # 활성 작업 목록에서 제거
            with self._jobs_lock:
                if job.id in self._active_jobs:
                    del self._active_jobs[job.id]

                # 완료된 작업 목록에 추가 (최대 100개 유지)
                self._completed_jobs.append(job)
                if len(self._completed_jobs) > 100:
                    self._completed_jobs.pop(0)

    def _handle_error(self, error: Exception) -> None:
        """Context7 모범 사례: 에러 처리"""
        self._consecutive_errors += 1
        self._last_error_time = datetime.now()

        self.logger.error(f"연속 오류 {self._consecutive_errors}회: {error}")

        # 에러 임계값 초과 시 일시 정지
        if (self._consecutive_errors >= self.config.error_threshold and
            self.config.pause_on_error and
            self.status == SchedulerStatus.RUNNING):

            self.logger.warning(f"연속 오류 {self._consecutive_errors}회로 스케줄러 일시 정지")
            self.pause()
            self._set_status(SchedulerStatus.ERROR)

    def _keyword_active(self, keyword_id: int) -> bool:
        """키워드별 중복 작업 억제 - 활성 작업 확인"""
        with self._jobs_lock:
            if any(j.keyword_id == keyword_id for j in self._active_jobs.values()):
                return True
        return False

    def _generate_job_id(self) -> str:
        """작업 ID 생성"""
        self._job_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"job_{timestamp}_{self._job_counter:04d}"

    def get_status_info(self) -> Dict[str, Any]:
        """스케줄러 상태 정보"""
        with self._jobs_lock:
            active_count = len(self._active_jobs)
            completed_count = len(self._completed_jobs)

        return {
            "status": self.status.value,
            "consecutive_errors": self._consecutive_errors,
            "last_error_time": self._last_error_time.isoformat() if self._last_error_time else None,
            "active_jobs": active_count,
            "completed_jobs": completed_count,
            "queue_size": self._job_queue.qsize(),
            "config": {
                "interval_minutes": self.config.interval_minutes,
                "max_concurrent_jobs": self.config.max_concurrent_jobs,
                "retry_attempts": self.config.retry_attempts
            }
        }

    def get_active_jobs(self) -> List[ScheduledJob]:
        """활성 작업 목록"""
        with self._jobs_lock:
            return list(self._active_jobs.values())

    def get_recent_jobs(self, limit: int = 50) -> List[ScheduledJob]:
        """최근 작업 목록"""
        with self._jobs_lock:
            return self._completed_jobs[-limit:] if self._completed_jobs else []