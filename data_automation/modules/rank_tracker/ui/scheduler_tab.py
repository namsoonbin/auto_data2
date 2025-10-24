"""
스케줄링 탭 - PySide6 Qt UI
상품 그룹의 자동 순위 추적 스케줄 관리
"""

import sys
import os
import json
import logging
import requests
from datetime import datetime, timezone, timedelta, time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QTimeEdit, QDateEdit, QTextEdit, QFrame,
    QHeaderView, QAbstractItemView, QCheckBox, QProgressBar,
    QMessageBox, QInputDialog, QMenu, QScrollArea, QSplitter,
    QGroupBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QListWidget,
    QListWidgetItem, QStackedWidget, QSlider, QDialog
)
from PySide6.QtCore import (
    Qt, Signal, QThread, QObject, QTimer, Signal,
    QSize, QModelIndex, QTime, QDate
)
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QPixmap

# 기존 모듈 임포트 시도
try:
    from ..core.unified_rank_engine import UnifiedRankEngine, RankSearchResult
    from ..core.product_group import ProductGroup, GroupItem, ProductGroupManager
except ImportError:
    # 개발 시간 임포트 오류 방지
    UnifiedRankEngine = None
    RankSearchResult = None
    ProductGroup = None
    GroupItem = None
    ProductGroupManager = None


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
    keyword: str = ""  # 더 이상 사용하지 않지만 하위 호환성을 위해 유지
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    start_time: Optional[time] = None  # 시작 시간
    interval_minutes: int = 60  # 간격(분) - Custom용
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    success_runs: int = 0
    created_at: Optional[datetime] = None
    last_results: Optional[Dict] = None  # 최근 실행 결과 (하위 호환성)
    results_history: List[Dict] = None  # 실행 결과 히스토리 (시계열)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone(timedelta(hours=9)))
        if self.start_time is None:
            self.start_time = time(9, 0)  # 기본값: 오전 9시
        if self.results_history is None:
            self.results_history = []
        self.update_next_run()

    def add_result_to_history(self, results: Dict, run_time: datetime):
        """
        결과를 히스토리에 추가 (최대 10개 유지)

        상세한 순위 데이터는 rank_history.db에 저장되므로
        schedules.json에는 최근 10개만 유지하여 파일 크기 최소화
        """
        history_entry = {
            'run_time': run_time.isoformat(),
            'results': results
        }
        self.results_history.append(history_entry)

        # 최근 10개만 유지 (메모리 및 파일 크기 관리)
        if len(self.results_history) > 10:
            self.results_history = self.results_history[-10:]

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_results': self.last_results,
            'results_history': self.results_history
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
            success_runs=data.get('success_runs', 0),
            last_results=data.get('last_results'),
            results_history=data.get('results_history', [])
        )

        # Context7 2025: 로드 시에도 히스토리 10개 제한 적용
        if len(task.results_history) > 10:
            logging.info(f"Task {task.task_id}: 히스토리 {len(task.results_history)}개 → 최근 10개로 제한")
            task.results_history = task.results_history[-10:]

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
    view_results = Signal(str)  # task_id

    def __init__(self, task: ScheduleTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()
        
        # 카드 클릭 시 결과 보기
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("클릭하여 최근 실행 결과 보기")

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

        # ✅ Context7 2025: RUNNING 상태 처리 추가
        if self.task.status == ScheduleStatus.RUNNING:
            toggle_btn = QPushButton("⏹️ 실행 중...")
            toggle_btn.setEnabled(False)  # 실행 중에는 토글 불가
            btn_color = MaterialColors.INFO
        elif self.task.status == ScheduleStatus.ACTIVE:
            toggle_btn = QPushButton("⏸️ 일시정지")
            btn_color = MaterialColors.WARNING
        else:
            toggle_btn = QPushButton("▶️ 재시작")
            btn_color = MaterialColors.SUCCESS

        toggle_btn.clicked.connect(self.request_toggle)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #F57C00;
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #666666;
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

    def mousePressEvent(self, event):
        """카드 클릭 시 결과 보기"""
        if event.button() == Qt.LeftButton:
            self.view_results.emit(self.task.task_id)
        super().mousePressEvent(event)

class ScheduleResultsDialog(QDialog):
    """스케줄 실행 결과 표시 다이얼로그 - 시계열 뷰"""
    
    def __init__(self, task: ScheduleTask, group_name: str, parent=None):
        super().__init__(parent)
        self.task = task
        self.group_name = group_name
        self.setWindowTitle(f"스케줄 실행 결과 - {task.name}")
        self.setMinimumSize(1000, 700)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 헤더
        header = QLabel(f"📊 {self.task.name} - 실행 히스토리")
        header.setFont(QFont('', 14, QFont.Bold))
        header.setStyleSheet(f"color: {MaterialColors.PRIMARY}; padding: 10px;")
        layout.addWidget(header)
        
        # 정보 섹션
        info_layout = QHBoxLayout()
        
        group_info = QLabel(f"📁 그룹: {self.group_name}")
        group_info.setFont(QFont('', 10))
        group_info.setStyleSheet(f"color: {MaterialColors.SECONDARY}; padding: 5px;")
        info_layout.addWidget(group_info)
        
        history_count = len(self.task.results_history)
        history_info = QLabel(f"📈 총 실행: {history_count}회")
        history_info.setFont(QFont('', 10))
        history_info.setStyleSheet(f"color: {MaterialColors.SECONDARY}; padding: 5px;")
        info_layout.addWidget(history_info)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 히스토리가 없는 경우
        if not self.task.results_history:
            no_results = QLabel("아직 실행된 결과가 없습니다.")
            no_results.setFont(QFont('', 12))
            no_results.setStyleSheet(f"color: {MaterialColors.ERROR}; padding: 20px;")
            no_results.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_results)
        else:
            # 탭 위젯 생성 (개별 상품별 시계열)
            self.create_product_tabs(layout)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5A47A0;
            }}
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def create_product_tabs(self, layout):
        """상품별 탭 생성"""
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #F5F5F5;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
            }
        """)
        
        # 상품별로 데이터 그룹화
        products_data = self.group_results_by_product()
        
        # 각 상품별 탭 생성
        for product_info, history_list in products_data.items():
            product_title, product_keyword = product_info
            tab = self.create_product_timeline_tab(product_title, product_keyword, history_list)
            tab_widget.addTab(tab, f"{product_title[:20]}...")
        
        layout.addWidget(tab_widget)
    
    def group_results_by_product(self) -> dict:
        """상품별로 히스토리 그룹화"""
        products = {}
        
        for history_entry in self.task.results_history:
            run_time = history_entry.get('run_time')
            results = history_entry.get('results', {})
            
            # 각 그룹의 결과 처리
            for group_id, group_results in results.items():
                for item_id, result in group_results.items():
                    title = result.get('title', '상품명 없음')
                    keyword = result.get('keyword', 'N/A')
                    product_key = (title, keyword)
                    
                    if product_key not in products:
                        products[product_key] = []
                    
                    products[product_key].append({
                        'run_time': run_time,
                        'rank': result.get('rank'),
                        'success': result.get('success'),
                        'error': result.get('error_message'),
                        'url': result.get('url'),
                        'image_url': result.get('image_url')
                    })
        
        return products
    
    def create_product_timeline_tab(self, title: str, keyword: str, history_list: list):
        """상품별 시계열 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 상품 정보 헤더
        info_label = QLabel(f"🏷️ {title}\n🔍 키워드: {keyword}")
        info_label.setFont(QFont('', 10, QFont.Bold))
        info_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE}; padding: 10px; background: #F5F5F5; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        
        # 최신순으로 정렬
        sorted_history = sorted(history_list, key=lambda x: x['run_time'], reverse=True)
        
        # 각 시간대별 결과 카드
        for idx, entry in enumerate(sorted_history):
            card = self.create_timeline_card(entry, idx, sorted_history)
            container_layout.addWidget(card)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        return widget
    
    def create_timeline_card(self, entry: dict, idx: int, all_history: list):
        """시계열 카드 생성"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        
        # 성공/실패에 따른 색상
        success = entry.get('success')
        rank = entry.get('rank')
        
        if success and rank is not None:
            border_color = MaterialColors.SUCCESS
            bg_color = "#E8F5E8"
        else:
            border_color = MaterialColors.ERROR
            bg_color = "#FFEBEE"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 6px;
                padding: 12px;
                margin: 2px;
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setSpacing(12)

        # 상품 이미지 (크기 확대: 100x100)
        image_label = QLabel()
        image_label.setFixedSize(100, 100)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)

        image_url = entry.get('image_url')
        if image_url:
            try:
                response = requests.get(image_url, timeout=3)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            98, 98, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        image_label.setPixmap(scaled_pixmap)
                    else:
                        image_label.setText("📷")
                        image_label.setFont(QFont('', 24))
                else:
                    image_label.setText("📷")
                    image_label.setFont(QFont('', 24))
            except:
                image_label.setText("📷")
                image_label.setFont(QFont('', 24))
        else:
            image_label.setText("📷")
            image_label.setFont(QFont('', 24))

        layout.addWidget(image_label)

        # 시간 정보
        run_time = entry.get('run_time', '')
        if run_time:
            try:
                dt = datetime.fromisoformat(run_time)
                time_text = dt.strftime('%m-%d %H:%M')
            except:
                time_text = run_time[:16]
        else:
            time_text = "알 수 없음"

        time_label = QLabel(f"🕐 {time_text}")
        time_label.setFont(QFont('', 9, QFont.Bold))
        time_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE}; min-width: 100px;")
        layout.addWidget(time_label)
        
        # 순위 또는 오류
        if success and rank is not None:
            rank_label = QLabel(f"📊 {rank}위")
            rank_label.setFont(QFont('', 11, QFont.Bold))
            rank_label.setStyleSheet(f"color: {MaterialColors.SUCCESS}; min-width: 80px;")
            layout.addWidget(rank_label)
            
            # 순위 변화 표시
            if idx < len(all_history) - 1:
                prev_entry = all_history[idx + 1]
                prev_rank = prev_entry.get('rank')
                if prev_rank is not None:
                    change = prev_rank - rank
                    if change > 0:
                        change_label = QLabel(f"📈 +{change}")
                        change_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    elif change < 0:
                        change_label = QLabel(f"📉 {change}")
                        change_label.setStyleSheet("color: #F44336; font-weight: bold;")
                    else:
                        change_label = QLabel("➖ 0")
                        change_label.setStyleSheet("color: #9E9E9E;")
                    
                    change_label.setFont(QFont('', 9))
                    layout.addWidget(change_label)
        else:
            error_text = entry.get('error', '알 수 없는 오류')[:50]
            error_label = QLabel(f"❌ {error_text}")
            error_label.setFont(QFont('', 9))
            error_label.setStyleSheet(f"color: {MaterialColors.ERROR};")
            error_label.setWordWrap(True)
            layout.addWidget(error_label, 1)
        
        layout.addStretch()
        
        return card


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
            # 새 구조에서는 'items' 딕셔너리 사용
            item_count = len(group_data.get('items', {}))
            self.group_combo.addItem(f"{group_name} ({item_count}개)", group_id)
        basic_layout.addWidget(self.group_combo, 1, 1)

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
        # keyword_input은 제거되었으므로 더 이상 설정하지 않음

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
            keyword="",  # 그룹 기반 스케줄이므로 키워드 불필요
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
    schedules_changed = Signal()  # 스케줄 업데이트 시 저장 트리거

    def __init__(self, tasks: Dict[str, ScheduleTask]):
        super().__init__()
        self.tasks = tasks
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_schedules)
        self.timer.start(30000)  # 30초마다 체크

    def check_schedules(self):
        """스케줄 체크"""
        now = datetime.now(timezone(timedelta(hours=9)))

        updated = False  # 스케줄 업데이트 여부 추적

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
                updated = True

        # ✅ 스케줄이 업데이트되었으면 저장 시그널 발생
        if updated:
            self.schedules_changed.emit()

        self.status_updated.emit()

    def update_tasks(self, tasks: Dict[str, ScheduleTask]):
        """작업 목록 업데이트"""
        self.tasks = tasks


class SchedulerTab(QWidget):
    """스케줄링 탭 메인 UI"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 데이터 저장 경로 - exe 파일 위치 기준 (config.BASE_DIR 사용)
        try:
            from modules import config
            base_dir = str(config.BASE_DIR)
        except ImportError:
            # 폴백: 현재 파일 기준
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

        self.schedules_file = os.path.join(base_dir, 'schedules.json')
        self.groups_file = os.path.join(base_dir, 'product_groups.json')

        # 상태 관리
        self.tasks = {}  # Dict[str, ScheduleTask]
        self.groups = {}  # 그룹 데이터
        self.monitor = None
        self.engine = None  # 순위 엔진

        # ✅ ProductGroupManager 사용 - 경로는 ProductGroupManager가 자동으로 config.BASE_DIR 사용
        self.group_manager = ProductGroupManager() if ProductGroupManager else None

        # ✅ Phase 8: 워커 스레드 및 비동기 파일 저장 관리
        self.current_worker = None  # 현재 실행 중인 워커
        self.current_thread = None  # 현재 실행 중인 스레드
        self.save_executor = ThreadPoolExecutor(max_workers=1)  # 비동기 파일 저장용

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
        # 그룹 데이터 로드 (ProductGroupManager 사용)
        try:
            if self.group_manager:
                self.group_manager.load_groups()
                # ProductGroup 객체들을 딕셔너리로 변환
                for group in self.group_manager.get_all_groups():
                    self.groups[group.group_id] = {
                        'group_id': group.group_id,
                        'name': group.name,
                        'description': group.description,
                        'items': {item_id: item.to_dict() for item_id, item in group.items.items()}
                    }
                logging.info(f"그룹 {len(self.groups)}개 로드")
        except Exception as e:
            logging.error(f"그룹 데이터 로드 실패: {e}")

        # 스케줄 데이터 로드
        try:
            # ✅ Context7 2025: 현재 실행 중인 task 보호
            running_tasks = {
                tid: t for tid, t in self.tasks.items()
                if t.status == ScheduleStatus.RUNNING
            }

            if os.path.exists(self.schedules_file):
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = ScheduleTask.from_dict(task_data)

                        # ✅ Context7 2025: 실행 중인 task는 상태 보호
                        if task.task_id in running_tasks:
                            task.status = ScheduleStatus.RUNNING
                            logging.info(f"Task '{task.task_id}' RUNNING 상태 보호됨")

                        self.tasks[task.task_id] = task
                logging.info(f"스케줄 {len(self.tasks)}개 로드")
        except Exception as e:
            logging.error(f"스케줄 데이터 로드 실패: {e}")

        self.refresh_schedules_list()
        self.update_stats()

    def save_schedules(self):
        """스케줄 데이터 저장 (동기)

        Phase 10: UI 갱신 제거
        - save_schedules()는 파일 저장만 담당
        - UI 갱신은 호출하는 쪽에서 명시적으로 수행
        - 이유: 저장과 UI 갱신의 타이밍을 분리하여 경합 조건 방지
        """
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

    def save_schedules_async(self):
        """스케줄 데이터 비동기 저장 (백그라운드 스레드)

        Phase 8: 스케줄 완료 시 메인 스레드 블로킹을 방지하기 위한 비동기 저장
        - ThreadPoolExecutor를 사용하여 별도 스레드에서 파일 저장
        - UI 응답성 유지하면서 데이터 안전하게 저장
        """
        def _save():
            try:
                data = {
                    'tasks': [task.to_dict() for task in self.tasks.values()],
                    'saved_at': datetime.now(timezone(timedelta(hours=9))).isoformat()
                }
                os.makedirs(os.path.dirname(self.schedules_file), exist_ok=True)
                with open(self.schedules_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"스케줄 {len(self.tasks)}개 비동기 저장 완료")
            except Exception as e:
                logging.error(f"스케줄 비동기 저장 실패: {e}")

        # ThreadPoolExecutor를 사용하여 백그라운드 저장
        self.save_executor.submit(_save)

    def refresh_schedules_list(self):
        """스케줄 목록 새로고침

        Phase 10: Qt 공식 문서 패턴 적용
        - Context7: takeAt(0)을 반복 사용 (reversed range 대신)
        - QLayoutItem 자체도 명시적 삭제
        - 참고: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout
        """
        # ✅ Qt 권장 패턴: 항상 0번째 아이템을 take (reversed 대신)
        while True:
            child_item = self.schedules_layout.takeAt(0)
            if child_item is None:
                break

            # 위젯 삭제
            widget = child_item.widget()
            if widget:
                widget.deleteLater()

            # QLayoutItem 자체도 삭제 (메모리 누수 방지)
            del child_item

        # ✅ Phase 10: 디버그 로깅 추가
        logging.info(f"refresh_schedules_list() 호출 - 현재 task 수: {len(self.tasks)}")

        if not self.tasks:
            logging.warning("refresh_schedules_list() - task가 비어있음, 빈 메시지 표시")
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

        logging.info(f"refresh_schedules_list() - {len(sorted_tasks)}개 카드 생성 시작")

        for task in sorted_tasks:
            card = ScheduleCard(task)
            card.edit_requested.connect(self.edit_schedule)
            card.delete_requested.connect(self.delete_schedule)
            card.toggle_requested.connect(self.toggle_schedule)
            card.view_results.connect(self.view_schedule_results)
            self.schedules_layout.addWidget(card)

        logging.info(f"refresh_schedules_list() - {len(sorted_tasks)}개 카드 생성 완료")

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
        self.monitor.schedules_changed.connect(self.save_schedules)  # 스케줄 업데이트 시 자동 저장

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

        # ✅ Context7 2025: 실행 상태를 즉시 파일에 저장
        self.save_schedules()

        self.refresh_schedules_list()
        self.update_stats()

        # 실제 순위 검색 실행
        if not self.engine or not self.group_manager:
            logging.error("Engine 또는 GroupManager가 설정되지 않았습니다")
            self.task_completed(task_id, False)
            return

        try:
            # ScheduledRankWorker 임포트
            from ..core.scheduled_rank_worker import ScheduledRankWorker

            # 워커 생성 및 실행
            self.current_worker = ScheduledRankWorker(
                self.group_manager,
                self.engine,
                [task.group_id]
            )

            # 워커 스레드 생성
            self.current_thread = QThread()
            self.current_worker.moveToThread(self.current_thread)

            # 시그널 연결
            self.current_thread.started.connect(self.current_worker.run)
            self.current_worker.all_completed.connect(lambda results: self.on_schedule_completed(task_id, results))
            self.current_worker.error.connect(lambda gid, err: self.on_schedule_error(task_id, err))
            self.current_worker.all_completed.connect(self.current_thread.quit)
            self.current_worker.error.connect(self.current_thread.quit)

            # 스레드 시작
            self.current_thread.start()

        except Exception as e:
            logging.error(f"스케줄 실행 실패: {e}")
            self.task_completed(task_id, False)

    def on_schedule_completed(self, task_id: str, results: dict):
        """스케줄 완료 처리 및 결과 저장"""
        logging.info(f"스케줄 완료: {task_id}")

        # 결과를 task에 저장 (메모리 작업만)
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.last_results = results

            # 히스토리에도 추가 (시계열 추적)
            run_time = datetime.now(timezone(timedelta(hours=9)))
            task.add_result_to_history(results, run_time)

            logging.info(f"스케줄 결과 메모리 저장 완료 - 히스토리 {len(task.results_history)}개")

        # 작업 완료 처리 (파일 저장은 여기서)
        self.task_completed(task_id, True)

        # ✅ Phase 10: QTimer.singleShot으로 워커 정리를 이벤트 루프 다음 사이클로 연기
        # 이유: 시그널 핸들러 내부에서 즉시 워커를 삭제하면 워커 객체가 자신의 코드를 실행하는 중에 삭제됨
        QTimer.singleShot(0, self._cleanup_worker)
        logging.info("워커 정리 예약됨 (다음 이벤트 사이클)")

    def on_schedule_error(self, task_id: str, error: str):
        """스케줄 에러 처리"""
        logging.error(f"스케줄 에러: {task_id} - {error}")
        self.task_completed(task_id, False)

        # ✅ Phase 10: QTimer.singleShot으로 워커 정리를 이벤트 루프 다음 사이클로 연기
        QTimer.singleShot(0, self._cleanup_worker)
        logging.info("워커 정리 예약됨 (다음 이벤트 사이클, 에러)")

    def _cleanup_worker(self):
        """워커 스레드 및 객체 정리 (지연 실행용)

        Phase 10: QTimer.singleShot(0)으로 호출되어 이벤트 루프의 다음 사이클에서 실행됨
        - 시그널 핸들러가 완전히 종료된 후 워커를 정리하여 Use-after-free 방지
        - Qt 이벤트 루프의 안전한 타이밍에서 deleteLater() 호출
        """
        if self.current_thread:
            self.current_thread.quit()
            self.current_thread.wait(5000)  # 최대 5초 대기
            self.current_thread.deleteLater()
            self.current_thread = None
            logging.info("워커 스레드 정리 완료")

        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
            logging.info("워커 객체 정리 완료")

    def view_schedule_results(self, task_id: str):
        """스케줄 결과 보기"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        # 그룹 이름 가져오기
        group_name = "알 수 없음"
        if task.group_id in self.groups:
            group_name = self.groups[task.group_id]['name']
        
        # 결과 다이얼로그 표시
        dialog = ScheduleResultsDialog(task, group_name, self)
        dialog.exec()

    def task_completed(self, task_id: str, success: bool):
        """작업 완료 처리

        Phase 8: 비동기 파일 저장으로 UI 블로킹 방지
        - save_schedules() 동기 호출 → save_schedules_async() 비동기 호출
        - UI 업데이트는 즉시 수행 (메인 스레드)
        - 파일 저장은 백그라운드 스레드에서 처리
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        if success:
            task.success_runs += 1

        task.status = ScheduleStatus.ACTIVE
        task.update_next_run()

        # ✅ Phase 9: 동기 저장으로 복원 (비동기 저장 시 탭 전환 타이밍 문제)
        # Phase 8의 duplicate save 제거 및 worker cleanup 덕분에 블로킹 최소화
        self.save_schedules()

        # UI 업데이트는 즉시 수행 (Qt는 메인 스레드에서만 UI 업데이트 가능)
        self.refresh_schedules_list()
        self.update_stats()

        logging.info(f"스케줄 실행 완료: {task.name} - {'성공' if success else '실패'}")

    def set_engine(self, engine):
        """순위 엔진 설정"""
        self.engine = engine

    def showEvent(self, event):
        """탭이 표시될 때 자동으로 그룹 목록 새로고침"""
        super().showEvent(event)

        # ✅ Context7 2025: 현재 실행 중인 task 보호
        running_tasks = {
            task_id: task.status
            for task_id, task in self.tasks.items()
            if task.status == ScheduleStatus.RUNNING
        }

        # ✅ Phase 7: 스케줄 실행 중일 때는 파일 reload 건너뛰기
        # 이유: 워커 스레드가 파일에 쓰는 중에 메인 스레드에서 읽으면
        #       1) UI가 멈춤 (동기적 파일 I/O)
        #       2) 파일 잠금 충돌 가능
        if running_tasks:
            logging.info(f"SchedulerTab: showEvent - {len(running_tasks)}개 task 실행 중이므로 reload 건너뜀")
        elif self.group_manager:
            logging.info("SchedulerTab: showEvent - 그룹 목록 자동 새로고침")
            # 그룹 데이터 재로드
            self.groups.clear()
            self.group_manager.load_groups()
            for group in self.group_manager.get_all_groups():
                self.groups[group.group_id] = {
                    'group_id': group.group_id,
                    'name': group.name,
                    'description': group.description,
                    'items': {item_id: item.to_dict() for item_id, item in group.items.items()}
                }
            logging.info(f"SchedulerTab: 그룹 {len(self.groups)}개 재로드 완료")

        # ✅ Context7 2025: 실행 중인 task 상태 복원
        for task_id, status in running_tasks.items():
            if task_id in self.tasks:
                self.tasks[task_id].status = status
                logging.info(f"SchedulerTab: 실행 중인 task '{task_id}' 상태 복원")

        # ✅ Phase 10: 탭 표시 시 스케줄 목록 UI 새로고침 (필수!)
        # 이유: 다른 탭에 있는 동안 메모리의 tasks는 업데이트되었지만 UI는 업데이트되지 않음
        #       예: 스케줄 완료 → tasks 업데이트 → 다른 탭으로 이동 → 돌아옴 → UI가 옛날 것
        logging.info("SchedulerTab: showEvent - 스케줄 목록 UI 새로고침")
        self.refresh_schedules_list()
        self.update_stats()

    def closeEvent(self, event):
        """탭 종료 시 리소스 정리"""
        if self.monitor:
            self.monitor.timer.stop()

        # ✅ Phase 8: ThreadPoolExecutor 정리
        if hasattr(self, 'save_executor'):
            logging.info("ThreadPoolExecutor 종료 대기 중...")
            self.save_executor.shutdown(wait=True, cancel_futures=False)
            logging.info("ThreadPoolExecutor 종료 완료")

        # 마지막 저장 (동기로 확실하게 저장)
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