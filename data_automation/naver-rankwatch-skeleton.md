
# Naver RankWatch (PySide6 · Official API · Organic Only)

> 네이버 쇼핑 검색의 **유기(Organic) 순위**만 안전하게 추적하는 PySide6 데스크톱 앱의 **기초 뼈대**입니다.  
> **네이버 검색 > 쇼핑 오픈API**만 사용하여 크롤링 차단 리스크를 최소화합니다.  
> 실행과 확장은 프로젝트 루트의 `app.py`부터 시작하세요. (Python 3.10+ 권장)

---

## 왜 “공식 API 우선”인가요?

- 네이버 **검색 > 쇼핑** 오픈API는 쇼핑 검색 결과를 **JSON/XML**로 반환합니다. 요청은 `GET https://openapi.naver.com/v1/search/shop.json`이며, 헤더에 `X-Naver-Client-Id`/`X-Naver-Client-Secret`을 포함합니다. 하루 호출 한도는 **25,000회**입니다. citeturn1view0  
- 요청 파라미터 주요 제약: `display`(최대 100), `start`(최대 1000), `sort`(sim/date/asc/dsc). 응답에는 `items` 배열과 `productId`, `mallName`, `brand`, `category1..4` 등이 포함됩니다. citeturn1view0  
- PySide6에서 GUI 멈춤 없이 백그라운드 작업을 돌리려면 **QThread + Signals/Slots** 패턴을 권장합니다. `moveToThread()`로 워커를 옮기고 시그널로 통신합니다. citeturn0search2turn0search3turn0search6  
- HTTP는 `requests.Session()`을 사용해 커넥션 풀/세션 재사용으로 안정성과 성능을 확보합니다. citeturn0search4turn0search7turn0search18

> ⚠️ 광고(쇼핑검색광고 등) 슬롯은 검색 오픈API 응답에 포함되지 않으므로 **광고를 제외한 유기 순위**만 계산됩니다. 공식 문서의 파라미터/응답에는 광고 필드가 없습니다. citeturn1view0

---

## 프로젝트 트리

```
naver_rankwatch/
  app.py                 # PySide6 메인 윈도우/스케줄러/로그
  core/
    api.py               # 네이버 쇼핑 API 클라이언트 (지수백오프 + 지연)
    ranker.py            # 유기 순위 계산 (productId 기준)
    storage.py           # SQLite 스키마/입출력
  workers/
    fetcher.py           # QThread 워커(배치 실행)
  requirements.txt
  .env.example
  .gitignore
```

---

## 빠른 시작 (Quick Start)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env에 본인 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 기입
python app.py
```

- 오픈API 엔드포인트: `GET /v1/search/shop.json` (HTTPS, GET) citeturn1view0  
- 파라미터: `query`, `display(<=100)`, `start(<=1000)`, `sort(sim|date|asc|dsc)` citeturn1view0  
- 인증: `X-Naver-Client-Id`, `X-Naver-Client-Secret` 헤더 citeturn1view0  
- 제한: **25,000회/일** (클라이언트ID 기준 합산) citeturn1view0

---

## 순위 정의

- “순위”는 **정확도순(`sort=sim`)** 기준 **유기(Organic) 결과**에서의 상대 위치를 뜻합니다.  
- 광고/개인화 영역과는 다를 수 있습니다(오픈API는 광고 필드를 반환하지 않음). citeturn1view0

---

## 코드

### `requirements.txt`
```txt
PySide6>=6.7
requests>=2.32
python-dotenv>=1.0
```

### `.env.example`
```env
NAVER_CLIENT_ID=YOUR_NAVER_CLIENT_ID
NAVER_CLIENT_SECRET=YOUR_NAVER_CLIENT_SECRET
```

### `.gitignore`
```gitignore
.venv/
__pycache__/
rankwatch.db
.env
*.pyc
```

### `core/api.py`
```python
import os, time, random
import requests
from dotenv import load_dotenv

load_dotenv()

NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")
BASE = "https://openapi.naver.com/v1/search/shop.json"

class NaverShopAPI:
    """네이버 쇼핑 검색 오픈API 클라이언트 (유기 결과만 응답)
    - 문서: /v1/search/shop.json, query/display/start/sort 파라미터, 헤더 인증
    """
    def __init__(self, min_delay=0.3, max_delay=0.9, timeout=10):
        if not NAVER_ID or not NAVER_SECRET:
            raise RuntimeError("NAVER_CLIENT_ID/SECRET 환경변수를 설정하세요 (.env).")
        self.s = requests.Session()
        self.headers = {
            "X-Naver-Client-Id": NAVER_ID,
            "X-Naver-Client-Secret": NAVER_SECRET,
        }
        self.min_delay, self.max_delay, self.timeout = min_delay, max_delay, timeout

    def _sleep(self):
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def get_page(self, query: str, start: int = 1, display: int = 100, sort: str = "sim") -> dict:
        """페이지 단위 호출 (display<=100, start<=1000 권장)"""
        params = {"query": query, "start": start, "display": display, "sort": sort}
        # 429/5xx 대비 지수백오프 + 지터
        for attempt in range(5):
            self._sleep()
            r = self.s.get(BASE, headers=self.headers, params=params, timeout=self.timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep((2 ** attempt) + random.random())
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Naver API 실패: query={{query}} start={{start}}")
```

### `core/ranker.py`
```python
def find_rank_for_ids(api, query: str, target_ids: set[str], max_depth: int = 1000, display: int = 100):
    """타겟 productId 집합의 유기 순위를 찾아 dict로 반환
    - sort="sim"(정확도순) 고정으로 시점간 일관성 유지
    - 최대 1000위까지 스캔 (네이버 문서의 start<=1000, display<=100 권장)
    """
    found: dict[str, int] = {}
    total_seen = 0
    for start in range(1, min(max_depth, 1000) + 1, display):
        data = api.get_page(query=query, start=start, display=display, sort="sim")
        items = data.get("items", [])
        for idx, it in enumerate(items):
            pid = str(it.get("productId"))
            if pid in target_ids and pid not in found:
                found[pid] = total_seen + idx + 1  # 1-based rank
        total_seen += len(items)
        total = data.get("total", 0)
        if len(found) == len(target_ids) or total_seen >= total:
            break
    return found, total_seen
```

### `core/storage.py`
```python
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

DB_PATH = Path("rankwatch.db")

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS keywords (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS targets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id TEXT NOT NULL,
  name TEXT,
  mall_domain TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword_id INTEGER NOT NULL,
  product_id TEXT NOT NULL,
  checked_at TEXT NOT NULL,
  rank INTEGER,
  total_seen INTEGER,
  source TEXT NOT NULL DEFAULT 'naver_shop_api'
);
"""

def now_kst_iso():
    # Asia/Seoul (UTC+9) 고정 기록
    return (datetime.now(timezone.utc) + timedelta(hours=9)).isoformat()

def connect():
    create = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    if create:
        conn.executescript(DDL)
        conn.commit()
    return conn

def insert_keyword(conn, query: str):
    cur = conn.execute(
        "INSERT INTO keywords(query, active, created_at) VALUES (?, 1, ?)",
        (query, now_kst_iso()),
    )
    conn.commit()
    return cur.lastrowid

def insert_target(conn, product_id: str, name: str | None = None, mall_domain: str | None = None):
    cur = conn.execute(
        "INSERT INTO targets(product_id, name, mall_domain, created_at) VALUES (?, ?, ?, ?)",
        (product_id, name, mall_domain, now_kst_iso()),
    )
    conn.commit()
    return cur.lastrowid

def insert_observation(conn, keyword_id: int, product_id: str, rank: int | None, total_seen: int):
    conn.execute(
        "INSERT INTO observations(keyword_id, product_id, checked_at, rank, total_seen) VALUES (?, ?, ?, ?, ?)",
        (keyword_id, product_id, now_kst_iso(), rank, total_seen),
    )
    conn.commit()
```

### `workers/fetcher.py`
```python
from PySide6.QtCore import QObject, Signal, Slot
from core.api import NaverShopAPI
from core.ranker import find_rank_for_ids
import traceback

class RankWorker(QObject):
    progress = Signal(str)                     # 진행 로그
    result = Signal(str, dict, int, int)       # query, {pid:rank}, total_seen, keyword_id
    error = Signal(str)

    def __init__(self, jobs: list[tuple[int, str, set[str]]]):  # (keyword_id, query, target_ids)
        super().__init__()
        self.jobs = jobs
        self.api = NaverShopAPI()

    @Slot()
    def run(self):
        try:
            for keyword_id, query, target_ids in self.jobs:
                self.progress.emit(f"[작업] '{query}' 조회 중...")
                ranks, total_seen = find_rank_for_ids(self.api, query, target_ids)
                self.result.emit(query, ranks, total_seen, keyword_id)
        except Exception as e:
            self.error.emit(f"{e}\n{traceback.format_exc()}")
```

### `app.py`
```python
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
)
from PySide6.QtCore import Qt, QThread, QTimer
from core import storage
from workers.fetcher import RankWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Naver RankWatch (Organic) — PySide6")
        self.conn = storage.connect()

        # --- UI ---
        root = QWidget(); self.setCentralWidget(root)
        v = QVBoxLayout(root)

        # 입력 영역
        row = QHBoxLayout()
        self.keyword_edit = QLineEdit(); self.keyword_edit.setPlaceholderText("키워드 입력 (예: 휴대용선풍기)")
        self.product_edit = QLineEdit(); self.product_edit.setPlaceholderText("타겟 productId 콤마구분 (예: 123,456)")
        btn_add = QPushButton("추가")
        btn_add.clicked.connect(self.add_row)
        row.addWidget(QLabel("키워드:")); row.addWidget(self.keyword_edit, 2)
        row.addWidget(QLabel("productId들:")); row.addWidget(self.product_edit, 3)
        row.addWidget(btn_add)
        v.addLayout(row)

        # 테이블
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["keyword_id", "키워드", "productIds"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnHidden(0, True)  # 내부 id 숨김
        v.addWidget(self.table, 1)

        # 버튼들
        row2 = QHBoxLayout()
        self.btn_start = QPushButton("시작")
        self.btn_stop = QPushButton("중지")
        self.btn_stop.setEnabled(False)
        row2.addWidget(self.btn_start); row2.addWidget(self.btn_stop)
        v.addLayout(row2)

        # 로그
        self.log = QTextEdit(); self.log.setReadOnly(True)
        v.addWidget(self.log, 2)

        # 스케줄러: 기본 10분 주기
        self.timer = QTimer(self)
        self.timer.setInterval(10 * 60 * 1000)
        self.timer.timeout.connect(self.run_batch)

        self.btn_start.clicked.connect(self.start_schedule)
        self.btn_stop.clicked.connect(self.stop_schedule)

        self.thread: QThread | None = None
        self.worker: RankWorker | None = None

    def add_row(self):
        query = self.keyword_edit.text().strip()
        pids = [p.strip() for p in self.product_edit.text().split(",") if p.strip()]
        if not query or not pids:
            self.log_append("키워드와 productId를 입력하세요."); return
        kid = storage.insert_keyword(self.conn, query)
        # targets 테이블에 없는 pid는 등록
        for pid in pids:
            storage.insert_target(self.conn, product_id=pid)
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(str(kid)))
        self.table.setItem(r, 1, QTableWidgetItem(query))
        self.table.setItem(r, 2, QTableWidgetItem(",".join(pids)))
        self.keyword_edit.clear(); self.product_edit.clear()
        self.log_append(f"[추가] keyword_id={kid} '{query}' / targets={len(pids)}")

    def start_schedule(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.run_batch()
        self.timer.start()
        self.log_append("[스케줄] 10분 주기로 실행 시작")

    def stop_schedule(self):
        self.timer.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log_append("[스케줄] 중지됨")

    def run_batch(self):
        # 테이블 → 작업 리스트 구성
        jobs: list[tuple[int, str, set[str]]] = []
        for r in range(self.table.rowCount()):
            kid = int(self.table.item(r, 0).text())
            query = self.table.item(r, 1).text()
            pids = set(self.table.item(r, 2).text().split(","))
            jobs.append((kid, query, pids))
        if not jobs:
            self.log_append("작업 항목이 없습니다. 키워드를 추가하세요.")
            return
        self.spawn_worker(jobs)

    def spawn_worker(self, jobs):
        if self.thread:  # 기존 스레드가 살아있다면 무시
            self.log_append("이전 작업이 아직 진행 중입니다."); return
        self.thread = QThread()
        self.worker = RankWorker(jobs)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.log_append)
        self.worker.result.connect(self.handle_result)
        self.worker.error.connect(self.handle_error)
        self.thread.finished.connect(self.cleanup_thread)
        self.thread.start()

    def handle_result(self, query: str, ranks: dict, total_seen: int, keyword_id: int):
        # 스토리지 저장 (없으면 None 순위 저장)
        # 현재 테이블 행의 productIds 기준으로 저장
        for r in range(self.table.rowCount()):
            if int(self.table.item(r, 0).text()) != keyword_id:
                continue
            pids = [p.strip() for p in self.table.item(r, 2).text().split(",") if p.strip()]
            for pid in pids:
                rank = ranks.get(pid)
                storage.insert_observation(self.conn, keyword_id, pid, rank, total_seen)
                if rank:
                    self.log_append(f"[결과] '{query}' pid={pid} → {rank}위 (스캔:{total_seen})")
                else:
                    self.log_append(f"[결과] '{query}' pid={pid} → 미노출 (상위 {total_seen} 내)")

        # 한 배치 끝났으면 스레드 종료
        if self.thread:
            self.thread.quit()
            self.thread.wait()

    def handle_error(self, msg: str):
        self.log_append(f"[오류] {msg}")
        if self.thread:
            self.thread.quit()
            self.thread.wait()

    def cleanup_thread(self):
        self.thread = None
        self.worker = None

    def log_append(self, text: str):
        self.log.append(text)
        self.log.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(980, 720)
    w.show()
    sys.exit(app.exec())
```

---

## 운영 팁

- **레이트리밋/에러 대응**: 429/5xx 시 지수 백오프 + 지터로 재시도, 호출 간 0.3–0.9초 지연. (오픈API 오류코드/제약 참고) citeturn1view0  
- **세션 재사용**: `requests.Session()`으로 TCP 커넥션 재사용 (성능·안정성). citeturn0search4  
- **스레드 안전 UI**: 워커는 `moveToThread()`로 옮기고, **시그널/슬롯**으로만 UI 접근. citeturn0search2turn0search6  

**PriorityQueue 동순위 비교 오류(타입 에러) 방지**
- 스케줄러에서 (priority, job) 형태로 넣으면 우선순위가 같은 항목이 겹칠 때 파이썬이 ScheduledJob 인스턴스를 서로 < 비교하려 하여 TypeError가 납니다. 타이브레이커(증가 시퀀스) 를 함께 넣으세요.

# scheduler.py (_create_scheduled_jobs)
priority = int(job.scheduled_at.timestamp())
self._job_counter += 1
seq = self._job_counter
- self._job_queue.put((priority, job))
+ self._job_queue.put((priority, seq, job))

# _worker_loop
- priority, job = self._job_queue.get(timeout=1)
+ priority, seq, job = self._job_queue.get(timeout=1)

**중복 작업 억제(키워드 단위 디더링/락)**
# scheduler.py 예시
def _keyword_active(self, keyword_id: int) -> bool:
    with self._jobs_lock:
        if any(j.keyword_id == keyword_id for j in self._active_jobs.values()):
            return True
    return False

# _create_scheduled_jobs 내부
if self._keyword_active(keyword.id):
    self.logger.debug(f"'{keyword.query}' 활성 작업 존재 → 건너뜀")
    continue

**API 클라이언트 헤더에 Accept: application/json 추가**
self.session.headers.update({
    "X-Naver-Client-Id": self.client_id,
    "X-Naver-Client-Secret": self.client_secret,
    "User-Agent": "NaverShopRankTracker/1.0",
    "Accept": "application/json",
})

## 재시도 정책 문서화 & 버전 고정
- urllib3>=1.26 이상에서 allowed_methods 사용이 표준입니다. requirements.txt에 명시해 주세요. 또한 재시도/백오프 수치를 주석으로 남기면 운영 시 해석이 쉬워요. 

- 429 대응 레이어 2중화(현재도 좋지만 추가 팁)
지금은 HTTPAdapter(Retry) + 애플리케이션 레벨(429 → RateLimitError → sleep) 두 겹으로 되어 있습니다. respect_retry_after_header=True를 주면 어댑터 레벨에서 먼저 대기하고, 남아있는 429만 앱 레벨에서 한 번 더 완충하는 구조가 되어 안정적입니다. 

Qt/스케줄러 통합시 가이드
만약 GUI 쪽에서 돌리게 되면, APScheduler의 QtScheduler를 쓰면 Qt 이벤트루프와 자연스럽게 맞물립니다(현재 스레드형 스케줄러도 OK). 운영 중에는 coalesce/max_instances 같은 옵션으로 중첩 실행을 방지하세요.
---

## 라이선스 / 주의

- 본 뼈대는 참고용 샘플이며, 실제 서비스 투입 전 내부 보안/로깅/모니터링/백업 정책을 검토하세요.  
- 네이버 개발자센터의 **이용약관·쿼터·오류코드 정책**을 준수하세요. citeturn1view0

— Generated 2025-09-24 01:57:11
