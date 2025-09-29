"""
스케줄링 탭 - PySide6 Qt UI
상품 그룹의 자동 순위 추적 스케줄 관리
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta, time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QTimeEdit, QDateEdit, QTextEdit, QFrame,
    QHeaderView, QAbstractItemView, QCheckBox, QProgressBar,
    QMessageBox, QInputDialog, QMenu, QScrollArea, QSplitter,
    QGroupBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QListWidget,
    QListWidgetItem, QStackedWidget, QSlider
)
from PySide6.QtCore import (
    Qt, Signal, QThread, QObject, QTimer, Signal,
    QSize, QModelIndex, QTime, QDate
)
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QAction

# 기존 모듈 임포트 시도
try:
    from ..core.unified_rank_engine import UnifiedRankEngine, RankSearchResult
except ImportError:
    # 개발 시간 임포트 오류 방지
    UnifiedRankEngine = None
    RankSearchResult = None


class MaterialColors:
    """Material Design 3 색상 팔레트"""
    PRIMARY = "#6750A4"
    PRIMARY_CONTAINER = "#EADDFF"
    SECONDARY = "#625B71"
    SURFACE = "#FFFBFE"
    SURFACE_VARIANT = "#E7E0EC"
    ON_SURFACE = "#1C1B1F"
    ON_PRIMARY = "#FFFFFF"
    ERROR = "#B3261E"
    SUCCESS = "#4CAF50"
    WARNING = "#FF9800"
    INFO = "#2196F3"


class ScheduleFrequency(Enum):
    """스케줄 빈도"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ScheduleStatus(Enum):
    """스케줄 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    RUNNING = "running"


@dataclass
class ScheduleTask:
    """스케줄 작업 데이터 클래스"""
    task_id: str
    name: str
    group_id: str
    keyword: str
    frequency: ScheduleFrequency
    start_time: time  # 시작 시간
    interval_minutes: int = 60  # 간격(분) - Custom용
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    success_runs: int = 0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone(timedelta(hours=9)))
        self.update_next_run()

    def update_next_run(self):
        """다음 실행 시간 계산"""
        now = datetime.now(timezone(timedelta(hours=9)))

        if self.frequency == ScheduleFrequency.HOURLY:
            # 매시간 지정된 분에 실행
            next_hour = now.replace(minute=self.start_time.minute, second=0, microsecond=0)
            if next_hour <= now:
                next_hour += timedelta(hours=1)
            self.next_run = next_hour

        elif self.frequency == ScheduleFrequency.DAILY:
            # 매일 지정된 시간에 실행
            next_day = now.replace(
                hour=self.start_time.hour,
                minute=self.start_time.minute,
                second=0,
                microsecond=0
            )
            if next_day <= now:
                next_day += timedelta(days=1)
            self.next_run = next_day

        elif self.frequency == ScheduleFrequency.WEEKLY:
            # 매주 지정된 요일과 시간에 실행
            next_week = now.replace(
                hour=self.start_time.hour,
                minute=self.start_time.minute,
                second=0,
                microsecond=0
            )
            days_ahead = 7 - now.weekday()  # 일주일 후 같은 요일
            if days_ahead <= 0 or (days_ahead == 0 and next_week <= now):
                days_ahead += 7
            next_week += timedelta(days=days_ahead)
            self.next_run = next_week

        elif self.frequency == ScheduleFrequency.CUSTOM:
            # 사용자 지정 간격(분)
            self.next_run = now + timedelta(minutes=self.interval_minutes)

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'name': self.name,
            'group_id': self.group_id,
            'keyword': self.keyword,
            'frequency': self.frequency.value,
            'start_time': self.start_time.strftime('%H:%M'),
            'interval_minutes': self.interval_minutes,
            'status': self.status.value,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'total_runs': self.total_runs,
            'success_runs': self.success_runs,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict):
        start_time = time.fromisoformat(data['start_time'])

        task = cls(
            task_id=data['task_id'],
            name=data['name'],
            group_id=data['group_id'],
            keyword=data['keyword'],
            frequency=ScheduleFrequency(data['frequency']),
            start_time=start_time,
            interval_minutes=data.get('interval_minutes', 60),
            status=ScheduleStatus(data.get('status', 'active')),
            total_runs=data.get('total_runs', 0),
            success_runs=data.get('success_runs', 0)
        )

        if data.get('last_run'):
            task.last_run = datetime.fromisoformat(data['last_run'])
        if data.get('next_run'):
            task.next_run = datetime.fromisoformat(data['next_run'])
        if data.get('created_at'):
            task.created_at = datetime.fromisoformat(data['created_at'])

        return task


class ScheduleCard(QFrame):
    """스케줄 작업 카드 UI"""
    edit_requested = Signal(str)  # task_id
    delete_requested = Signal(str)  # task_id
    toggle_requested = Signal(str)  # task_id

    def __init__(self, task: ScheduleTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()

    def init_ui(self):
        """카드 UI 초기화"""
        self.setFrameStyle(QFrame.Box)

        # 상태에 따른 색상 변경
        if self.task.status == ScheduleStatus.ACTIVE:
            border_color = MaterialColors.SUCCESS
            bg_color = "#E8F5E8"
        elif self.task.status == ScheduleStatus.RUNNING:
            border_color = MaterialColors.INFO
            bg_color = "#E3F2FD"
        elif self.task.status == ScheduleStatus.PAUSED:
            border_color = MaterialColors.WARNING
            bg_color = "#FFF3E0"
        else:  # STOPPED
            border_color = MaterialColors.ERROR
            bg_color = "#FFEBEE"

        self.setStyleSheet(f"""
            ScheduleCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 16px;
                margin: 8px;
            }}
            ScheduleCard:hover {{
                background-color: {MaterialColors.PRIMARY_CONTAINER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # 헤더: 제목과 상태
        header_layout = QHBoxLayout()

        title_label = QLabel(self.task.name)
        title_label.setFont(QFont('', 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE};")

        status_label = QLabel(self.get_status_text())
        status_label.setFont(QFont('', 10))
        status_label.setStyleSheet(f"color: {border_color}; font-weight: bold;")

        header_layout.addWidget(title_label, 1)
        header_layout.addWidget(status_label)

        # 정보 섹션
        info_layout = QVBoxLayout()

        # 키워드와 그룹 정보
        keyword_label = QLabel(f"🔍 키워드: {self.task.keyword}")
        keyword_label.setFont(QFont('', 9))
        keyword_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE};")

        group_label = QLabel(f"📁 그룹: {self.task.group_id}")
        group_label.setFont(QFont('', 9))
        group_label.setStyleSheet(f"color: {MaterialColors.SECONDARY};")

        # 스케줄 정보
        schedule_text = self.get_schedule_text()
        schedule_label = QLabel(f"⏰ {schedule_text}")
        schedule_label.setFont(QFont('', 9))
        schedule_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE};")

        # 실행 통계
        stats_text = f"📊 실행: {self.task.success_runs}/{self.task.total_runs} 성공"
        stats_label = QLabel(stats_text)
        stats_label.setFont(QFont('', 8))
        stats_label.setStyleSheet(f"color: {MaterialColors.SECONDARY};")

        # 다음 실행 시간
        if self.task.next_run and self.task.status == ScheduleStatus.ACTIVE:
            next_run_text = f"🕒 다음 실행: {self.task.next_run.strftime('%m-%d %H:%M')}"
            next_run_label = QLabel(next_run_text)
            next_run_label.setFont(QFont('', 8))
            next_run_label.setStyleSheet(f"color: {MaterialColors.INFO};")
            info_layout.addWidget(next_run_label)

        info_layout.addWidget(keyword_label)
        info_layout.addWidget(group_label)
        info_layout.addWidget(schedule_label)
        info_layout.addWidget(stats_label)

        # 버튼 섹션
        button_layout = QHBoxLayout()

        toggle_btn = QPushButton("⏸️ 일시정지" if self.task.status == ScheduleStatus.ACTIVE else "▶️ 재시작")
        toggle_btn.clicked.connect(self.request_toggle)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.WARNING if self.task.status == ScheduleStatus.ACTIVE else MaterialColors.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #F57C00;
            }}
        """)

        edit_btn = QPushButton("✏️ 편집")
        edit_btn.clicked.connect(self.request_edit)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #5A47A0;
            }}
        """)

        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(self.request_delete)
        delete_btn.setToolTip("스케줄 삭제")
        delete_btn.setFixedSize(28, 24)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.ERROR};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
        """)

        button_layout.addWidget(toggle_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)
        layout.addLayout(button_layout)

    def get_status_text(self):
        """상태 텍스트 반환"""
        status_map = {
            ScheduleStatus.ACTIVE: "🟢 활성",
            ScheduleStatus.RUNNING: "🔵 실행중",
            ScheduleStatus.PAUSED: "🟡 일시정지",
            ScheduleStatus.STOPPED: "🔴 중지"
        }
        return status_map.get(self.task.status, "❓ 불명")

    def get_schedule_text(self):
        """스케줄 정보 텍스트 반환"""
        if self.task.frequency == ScheduleFrequency.HOURLY:
            return f"매시간 {self.task.start_time.strftime('%M')}분"
        elif self.task.frequency == ScheduleFrequency.DAILY:
            return f"매일 {self.task.start_time.strftime('%H:%M')}"
        elif self.task.frequency == ScheduleFrequency.WEEKLY:
            return f"매주 {self.task.start_time.strftime('%H:%M')}"
        elif self.task.frequency == ScheduleFrequency.CUSTOM:
            return f"{self.task.interval_minutes}분마다"
        return "알 수 없음"

    def request_toggle(self):
        """상태 토글 요청"""
        self.toggle_requested.emit(self.task.task_id)

    def request_edit(self):
        """편집 요청"""
        self.edit_requested.emit(self.task.task_id)

    def request_delete(self):
        """삭제 요청"""
        self.delete_requested.emit(self.task.task_id)

    def update_task(self, task: ScheduleTask):
        """작업 정보 업데이트"""
        self.task = task
        self.init_ui()


class ScheduleDialog(QMessageBox):
    """스케줄 생성/편집 다이얼로그"""

    def __init__(self, groups: Dict[str, Any], existing_task: Optional[ScheduleTask] = None, parent=None):
        super().__init__(parent)
        self.groups = groups
        self.existing_task = existing_task
        self.result_task = None

        self.setup_ui()

        if existing_task:
            self.load_existing_task()

    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("스케줄 편집" if self.existing_task else "새 스케줄 생성")
        self.setIcon(QMessageBox.Information)

        # 커스텀 위젯 생성
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 기본 정보
        basic_group = QGroupBox("📋 기본 정보")
        basic_layout = QGridLayout(basic_group)

        # 스케줄 이름
        basic_layout.addWidget(QLabel("스케줄 이름:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("스케줄 이름을 입력하세요")
        basic_layout.addWidget(self.name_input, 0, 1)

        # 그룹 선택
        basic_layout.addWidget(QLabel("대상 그룹:"), 1, 0)
        self.group_combo = QComboBox()
        for group_id, group_data in self.groups.items():
            group_name = group_data.get('name', group_id)
            self.group_combo.addItem(f"{group_name} ({len(group_data.get('products', []))}개)", group_id)
        basic_layout.addWidget(self.group_combo, 1, 1)

        # 키워드
        basic_layout.addWidget(QLabel("검색 키워드:"), 2, 0)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("순위를 확인할 키워드")
        basic_layout.addWidget(self.keyword_input, 2, 1)

        # 스케줄 설정
        schedule_group = QGroupBox("⏰ 스케줄 설정")
        schedule_layout = QGridLayout(schedule_group)

        # 빈도 선택
        schedule_layout.addWidget(QLabel("실행 빈도:"), 0, 0)
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("매시간", ScheduleFrequency.HOURLY.value)
        self.frequency_combo.addItem("매일", ScheduleFrequency.DAILY.value)
        self.frequency_combo.addItem("매주", ScheduleFrequency.WEEKLY.value)
        self.frequency_combo.addItem("사용자 지정", ScheduleFrequency.CUSTOM.value)
        self.frequency_combo.currentTextChanged.connect(self.on_frequency_changed)
        schedule_layout.addWidget(self.frequency_combo, 0, 1)

        # 시작 시간
        schedule_layout.addWidget(QLabel("시작 시간:"), 1, 0)
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")
        schedule_layout.addWidget(self.time_input, 1, 1)

        # 사용자 지정 간격 (Custom용)
        self.interval_label = QLabel("간격(분):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(5)
        self.interval_spin.setMaximum(1440)  # 24시간
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix("분")

        schedule_layout.addWidget(self.interval_label, 2, 0)
        schedule_layout.addWidget(self.interval_spin, 2, 1)

        # 초기 상태에서는 간격 설정 숨김
        self.interval_label.setVisible(False)
        self.interval_spin.setVisible(False)

        layout.addWidget(basic_group)
        layout.addWidget(schedule_group)

        # 다이얼로그에 위젯 설정
        self.layout().addWidget(widget, 0, 0, 1, self.layout().columnCount())

        # 버튼
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    def on_frequency_changed(self, text: str):
        """빈도 변경 시 UI 업데이트"""
        is_custom = text == "사용자 지정"
        self.interval_label.setVisible(is_custom)
        self.interval_spin.setVisible(is_custom)

    def load_existing_task(self):
        """기존 작업 정보 로드"""
        self.name_input.setText(self.existing_task.name)
        self.keyword_input.setText(self.existing_task.keyword)

        # 그룹 선택
        for i in range(self.group_combo.count()):
            if self.group_combo.itemData(i) == self.existing_task.group_id:
                self.group_combo.setCurrentIndex(i)
                break

        # 빈도 선택
        for i in range(self.frequency_combo.count()):
            if self.frequency_combo.itemData(i) == self.existing_task.frequency.value:
                self.frequency_combo.setCurrentIndex(i)
                break

        # 시간 설정
        q_time = QTime(self.existing_task.start_time.hour, self.existing_task.start_time.minute)
        self.time_input.setTime(q_time)

        # 간격 설정
        if self.existing_task.frequency == ScheduleFrequency.CUSTOM:
            self.interval_spin.setValue(self.existing_task.interval_minutes)

    def get_result_task(self):
        """결과 작업 반환"""
        if self.result() != QMessageBox.Ok:
            return None

        task_id = self.existing_task.task_id if self.existing_task else f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        q_time = self.time_input.time()
        start_time = time(q_time.hour(), q_time.minute())

        frequency = ScheduleFrequency(self.frequency_combo.currentData())

        task = ScheduleTask(
            task_id=task_id,
            name=self.name_input.text().strip(),
            group_id=self.group_combo.currentData(),
            keyword=self.keyword_input.text().strip(),
            frequency=frequency,
            start_time=start_time,
            interval_minutes=self.interval_spin.value() if frequency == ScheduleFrequency.CUSTOM else 60
        )

        if self.existing_task:
            # 기존 통계 유지
            task.total_runs = self.existing_task.total_runs
            task.success_runs = self.existing_task.success_runs
            task.last_run = self.existing_task.last_run
            task.created_at = self.existing_task.created_at

        return task


class SchedulerMonitor(QObject):
    """스케줄러 모니터링 워커"""
    task_triggered = Signal(str)  # task_id
    status_updated = Signal()

    def __init__(self, tasks: Dict[str, ScheduleTask]):
        super().__init__()
        self.tasks = tasks
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_schedules)
        self.timer.start(30000)  # 30초마다 체크

    def check_schedules(self):
        """스케줄 체크"""
        now = datetime.now(timezone(timedelta(hours=9)))

        for task in self.tasks.values():
            if (task.status == ScheduleStatus.ACTIVE and
                task.next_run and
                now >= task.next_run):

                # 실행 트리거
                self.task_triggered.emit(task.task_id)

                # 다음 실행 시간 업데이트
                task.last_run = now
                task.total_runs += 1
                task.update_next_run()

        self.status_updated.emit()

    def update_tasks(self, tasks: Dict[str, ScheduleTask]):
        """작업 목록 업데이트"""
        self.tasks = tasks


class SchedulerTab(QWidget):
    """스케줄링 탭 메인 UI"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 데이터 저장 경로
        self.schedules_file = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'schedules.json'
        )
        self.groups_file = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'product_groups.json'
        )

        # 상태 관리
        self.tasks = {}  # Dict[str, ScheduleTask]
        self.groups = {}  # 그룹 데이터
        self.monitor = None
        self.engine = None  # 순위 엔진

        # UI 초기화
        self.init_ui()
        self.load_data()
        self.start_monitor()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 헤더 섹션
        header_layout = QHBoxLayout()

        title_label = QLabel("⏰ 자동 순위 추적 스케줄러")
        title_label.setFont(QFont('', 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE}; margin-bottom: 16px;")

        # 새 스케줄 생성 버튼
        new_schedule_btn = QPushButton("➕ 새 스케줄 생성")
        new_schedule_btn.clicked.connect(self.create_new_schedule)
        new_schedule_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #5A47A0;
            }}
        """)

        header_layout.addWidget(title_label, 1)
        header_layout.addWidget(new_schedule_btn)

        # 통계 섹션
        stats_section = self.create_stats_section()

        # 스케줄 목록
        self.schedules_scroll = QScrollArea()
        self.schedules_container = QWidget()
        self.schedules_layout = QVBoxLayout(self.schedules_container)
        self.schedules_layout.setAlignment(Qt.AlignTop)

        self.schedules_scroll.setWidget(self.schedules_container)
        self.schedules_scroll.setWidgetResizable(True)
        self.schedules_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 2px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 12px;
                background-color: {MaterialColors.SURFACE_VARIANT};
                padding: 8px;
            }}
        """)

        layout.addLayout(header_layout)
        layout.addWidget(stats_section)
        layout.addWidget(self.schedules_scroll, 1)

    def create_stats_section(self):
        """통계 섹션 생성"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {MaterialColors.SURFACE};
                border: 2px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QHBoxLayout(section)

        # 활성 스케줄 수
        self.active_count_label = QLabel("활성 스케줄: 0개")
        self.active_count_label.setFont(QFont('', 12, QFont.Bold))
        self.active_count_label.setStyleSheet(f"color: {MaterialColors.SUCCESS};")

        # 일시정지된 스케줄 수
        self.paused_count_label = QLabel("일시정지: 0개")
        self.paused_count_label.setFont(QFont('', 12))
        self.paused_count_label.setStyleSheet(f"color: {MaterialColors.WARNING};")

        # 실행중인 스케줄 수
        self.running_count_label = QLabel("실행중: 0개")
        self.running_count_label.setFont(QFont('', 12))
        self.running_count_label.setStyleSheet(f"color: {MaterialColors.INFO};")

        # 오늘 실행 통계
        self.today_runs_label = QLabel("오늘 실행: 0회")
        self.today_runs_label.setFont(QFont('', 12))
        self.today_runs_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE};")

        layout.addWidget(self.active_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.paused_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.running_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.today_runs_label)
        layout.addStretch()

        return section

    def load_data(self):
        """데이터 로드"""
        # 그룹 데이터 로드
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for group_data in data.get('groups', []):
                        group_id = group_data.get('group_id')
                        if group_id:
                            self.groups[group_id] = group_data
                logging.info(f"그룹 {len(self.groups)}개 로드")
        except Exception as e:
            logging.error(f"그룹 데이터 로드 실패: {e}")

        # 스케줄 데이터 로드
        try:
            if os.path.exists(self.schedules_file):
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = ScheduleTask.from_dict(task_data)
                        self.tasks[task.task_id] = task
                logging.info(f"스케줄 {len(self.tasks)}개 로드")
        except Exception as e:
            logging.error(f"스케줄 데이터 로드 실패: {e}")

        self.refresh_schedules_list()
        self.update_stats()

    def save_schedules(self):
        """스케줄 데이터 저장"""
        try:
            data = {
                'tasks': [task.to_dict() for task in self.tasks.values()],
                'saved_at': datetime.now(timezone(timedelta(hours=9))).isoformat()
            }

            os.makedirs(os.path.dirname(self.schedules_file), exist_ok=True)
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logging.info(f"스케줄 {len(self.tasks)}개 저장 완료")
        except Exception as e:
            logging.error(f"스케줄 저장 실패: {e}")

    def refresh_schedules_list(self):
        """스케줄 목록 새로고침"""
        # 기존 카드들 제거
        for i in reversed(range(self.schedules_layout.count())):
            child = self.schedules_layout.takeAt(i).widget()
            if child:
                child.deleteLater()

        if not self.tasks:
            empty_label = QLabel("생성된 스케줄이 없습니다")
            empty_label.setStyleSheet(f"color: {MaterialColors.SECONDARY}; text-align: center; padding: 40px; font-size: 14px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.schedules_layout.addWidget(empty_label)
            return

        # 스케줄 카드들 생성 (상태별 정렬)
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (t.status.value, t.next_run or datetime.min.replace(tzinfo=timezone.utc))
        )

        for task in sorted_tasks:
            card = ScheduleCard(task)
            card.edit_requested.connect(self.edit_schedule)
            card.delete_requested.connect(self.delete_schedule)
            card.toggle_requested.connect(self.toggle_schedule)
            self.schedules_layout.addWidget(card)

    def update_stats(self):
        """통계 업데이트"""
        active_count = len([t for t in self.tasks.values() if t.status == ScheduleStatus.ACTIVE])
        paused_count = len([t for t in self.tasks.values() if t.status == ScheduleStatus.PAUSED])
        running_count = len([t for t in self.tasks.values() if t.status == ScheduleStatus.RUNNING])

        # 오늘 실행 횟수 계산
        today = datetime.now(timezone(timedelta(hours=9))).date()
        today_runs = sum(
            t.total_runs for t in self.tasks.values()
            if t.last_run and t.last_run.date() == today
        )

        self.active_count_label.setText(f"활성 스케줄: {active_count}개")
        self.paused_count_label.setText(f"일시정지: {paused_count}개")
        self.running_count_label.setText(f"실행중: {running_count}개")
        self.today_runs_label.setText(f"오늘 실행: {today_runs}회")

    def start_monitor(self):
        """모니터링 시작"""
        if self.monitor:
            self.monitor.timer.stop()

        self.monitor = SchedulerMonitor(self.tasks)
        self.monitor.task_triggered.connect(self.execute_task)
        self.monitor.status_updated.connect(self.update_stats)

    def create_new_schedule(self):
        """새 스케줄 생성"""
        if not self.groups:
            QMessageBox.warning(
                self, "경고",
                "스케줄을 생성하려면 먼저 상품 그룹을 생성해야 합니다.\n\n"
                "그룹 관리 탭에서 상품 그룹을 생성한 후 다시 시도하세요."
            )
            return

        dialog = ScheduleDialog(self.groups)
        if dialog.exec_() == QMessageBox.Ok:
            task = dialog.get_result_task()
            if task:
                self.tasks[task.task_id] = task
                self.save_schedules()
                self.refresh_schedules_list()
                self.update_stats()

                if self.monitor:
                    self.monitor.update_tasks(self.tasks)

                logging.info(f"새 스케줄 생성: {task.name}")

    def edit_schedule(self, task_id: str):
        """스케줄 편집"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        dialog = ScheduleDialog(self.groups, task)

        if dialog.exec_() == QMessageBox.Ok:
            updated_task = dialog.get_result_task()
            if updated_task:
                self.tasks[task_id] = updated_task
                self.save_schedules()
                self.refresh_schedules_list()
                self.update_stats()

                if self.monitor:
                    self.monitor.update_tasks(self.tasks)

                logging.info(f"스케줄 편집: {updated_task.name}")

    def delete_schedule(self, task_id: str):
        """스케줄 삭제"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        reply = QMessageBox.question(
            self, "스케줄 삭제",
            f"'{task.name}' 스케줄을 삭제하시겠습니까?\n\n"
            f"이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.tasks[task_id]
            self.save_schedules()
            self.refresh_schedules_list()
            self.update_stats()

            if self.monitor:
                self.monitor.update_tasks(self.tasks)

            logging.info(f"스케줄 삭제: {task.name}")

    def toggle_schedule(self, task_id: str):
        """스케줄 상태 토글"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        if task.status == ScheduleStatus.ACTIVE:
            task.status = ScheduleStatus.PAUSED
        elif task.status == ScheduleStatus.PAUSED:
            task.status = ScheduleStatus.ACTIVE
            task.update_next_run()  # 다음 실행 시간 재계산

        self.save_schedules()
        self.refresh_schedules_list()
        self.update_stats()

        if self.monitor:
            self.monitor.update_tasks(self.tasks)

        logging.info(f"스케줄 상태 변경: {task.name} → {task.status.value}")

    def execute_task(self, task_id: str):
        """스케줄 작업 실행"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        logging.info(f"스케줄 실행 시작: {task.name}")

        # 상태를 실행중으로 변경
        task.status = ScheduleStatus.RUNNING
        self.refresh_schedules_list()
        self.update_stats()

        # 실제 순위 검색 실행 (백그라운드에서)
        # TODO: 실제 검색 로직은 배치 검색 워커를 사용하여 구현

        # 일시적으로 성공으로 처리 (실제 구현에서는 검색 결과에 따라 처리)
        QTimer.singleShot(5000, lambda: self.task_completed(task_id, True))

    def task_completed(self, task_id: str, success: bool):
        """작업 완료 처리"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        if success:
            task.success_runs += 1

        task.status = ScheduleStatus.ACTIVE
        task.update_next_run()

        self.save_schedules()
        self.refresh_schedules_list()
        self.update_stats()

        logging.info(f"스케줄 실행 완료: {task.name} - {'성공' if success else '실패'}")

    def set_engine(self, engine):
        """순위 엔진 설정"""
        self.engine = engine

    def closeEvent(self, event):
        """탭 종료 시 리소스 정리"""
        if self.monitor:
            self.monitor.timer.stop()

        self.save_schedules()
        event.accept()


if __name__ == "__main__":
    # 단독 테스트용
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Material Design 3 스타일 적용
    app.setStyle('Fusion')
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(MaterialColors.SURFACE))
    palette.setColor(QPalette.Base, QColor(MaterialColors.SURFACE))
    app.setPalette(palette)

    widget = SchedulerTab()
    widget.show()

    sys.exit(app.exec())