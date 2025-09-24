# -*- coding: utf-8 -*-
"""
순위 추적 UI 컴포넌트 모듈
Context7 2025 모범 사례 적용: Material Design 3, 타입 안전성, 사용자 경험
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QGridLayout, QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDateEdit, QTextEdit, QProgressBar,
    QCheckBox, QDialog, QDialogButtonBox, QScrollArea, QFrame,
    QMessageBox, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QPalette

from .settings import get_settings
from .rank_tracker.naver_api import NaverShopAPI, APIError
from .rank_tracker.database import RankDatabase
from .rank_tracker.scheduler import RankScheduler
from .rank_tracker.rank_calculator import RankCalculator, RankResult, RankStatus

logger = logging.getLogger(__name__)


@dataclass
class TrackingTarget:
    """추적 대상 데이터클래스"""
    id: int
    product_id: str
    keyword: str
    target_rank: int
    store_name: str
    enabled: bool
    created_at: datetime
    last_checked: Optional[datetime] = None
    current_rank: Optional[int] = None


class MaterialColors:
    """Material Design 3 색상 체계"""
    PRIMARY = "#2563eb"
    SUCCESS = "#059669"
    WARNING = "#ea580c"
    ERROR = "#dc2626"
    SURFACE = "#f8f9fa"
    ON_SURFACE = "#1a1a1a"
    OUTLINE = "#dee2e6"


class ModernCard(QFrame):
    """Modern 스타일 카드 위젯 - 반응형 개선"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.OUTLINE};
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }}
            ModernCard:hover {{
                border-color: {MaterialColors.PRIMARY};
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 600;
                color: {MaterialColors.ON_SURFACE};
                margin-bottom: 8px;
                padding: 4px 0;
            """)
            self.layout.addWidget(title_label)


class KeywordManagementDialog(QDialog):
    """키워드 관리 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("키워드 관리")
        self.setMinimumSize(800, 600)

        # 데이터베이스 초기화
        settings = get_settings()
        db_path = Path(settings.rank_tracking.db_file_name)
        self.db = RankDatabase(db_path)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 추가 섹션
        add_card = ModernCard("새 추적 대상 추가")
        layout.addWidget(add_card)

        form_layout = QGridLayout()
        add_card.layout.addLayout(form_layout)

        form_layout.addWidget(QLabel("상품ID:"), 0, 0)
        self.product_id_input = QLineEdit()
        self.product_id_input.setPlaceholderText("상품 ID를 입력하세요")
        form_layout.addWidget(self.product_id_input, 0, 1)

        form_layout.addWidget(QLabel("키워드:"), 1, 0)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("검색할 키워드를 입력하세요")
        form_layout.addWidget(self.keyword_input, 1, 1)

        form_layout.addWidget(QLabel("목표 순위:"), 2, 0)
        self.target_rank_input = QSpinBox()
        self.target_rank_input.setRange(1, 1000)
        self.target_rank_input.setValue(10)
        form_layout.addWidget(self.target_rank_input, 2, 1)

        form_layout.addWidget(QLabel("스토어:"), 3, 0)
        self.store_input = QLineEdit()
        self.store_input.setPlaceholderText("스토어명을 입력하세요")
        form_layout.addWidget(self.store_input, 3, 1)

        add_btn = QPushButton("➕ 추가")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
        """)
        add_btn.clicked.connect(self.add_tracking_target)
        form_layout.addWidget(add_btn, 4, 0, 1, 2)

        # 목록 섹션
        list_card = ModernCard("추적 대상 목록")
        layout.addWidget(list_card)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "상품ID", "키워드", "목표순위", "현재순위", "스토어", "상태", "마지막 확인"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        list_card.layout.addWidget(self.table)

        # 버튼 섹션
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.ERROR};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
            }}
        """)
        delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def add_tracking_target(self):
        """추적 대상 추가"""
        try:
            product_id = self.product_id_input.text().strip()
            keyword = self.keyword_input.text().strip()
            target_rank = self.target_rank_input.value()
            store_name = self.store_input.text().strip()

            if not all([product_id, keyword, store_name]):
                QMessageBox.warning(self, "입력 오류", "모든 필드를 입력해주세요.")
                return

            self.db.add_tracking_target(product_id, keyword, target_rank, store_name)

            # 입력 필드 초기화
            self.product_id_input.clear()
            self.keyword_input.clear()
            self.target_rank_input.setValue(10)
            self.store_input.clear()

            self.load_data()
            QMessageBox.information(self, "성공", "추적 대상이 추가되었습니다.")

        except Exception as e:
            logger.error(f"추적 대상 추가 실패: {e}")
            QMessageBox.critical(self, "오류", f"추가 실패: {str(e)}")

    def delete_selected(self):
        """선택된 항목 삭제"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "삭제할 항목을 선택해주세요.")
            return

        # 상품ID와 키워드로 삭제
        product_id = self.table.item(current_row, 0).text()
        keyword = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{product_id} - {keyword}' 항목을 삭제하시겠습니까?"
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.remove_tracking_target(product_id, keyword)
                self.load_data()
                QMessageBox.information(self, "성공", "추적 대상이 삭제되었습니다.")
            except Exception as e:
                logger.error(f"추적 대상 삭제 실패: {e}")
                QMessageBox.critical(self, "오류", f"삭제 실패: {str(e)}")

    def load_data(self):
        """데이터 로드"""
        try:
            targets = self.db.get_active_targets()
            self.table.setRowCount(len(targets))

            for row, target in enumerate(targets):
                self.table.setItem(row, 0, QTableWidgetItem(target.product_id))
                self.table.setItem(row, 1, QTableWidgetItem(target.keyword))
                self.table.setItem(row, 2, QTableWidgetItem(str(target.target_rank)))

                # 현재 순위 표시
                current_rank = target.current_rank if target.current_rank else "-"
                rank_item = QTableWidgetItem(str(current_rank))

                # 순위에 따른 색상 표시
                if target.current_rank:
                    if target.current_rank <= target.target_rank:
                        rank_item.setBackground(QPalette().color(QPalette.Light))
                    else:
                        rank_item.setBackground(QPalette().color(QPalette.Mid))

                self.table.setItem(row, 3, rank_item)
                self.table.setItem(row, 4, QTableWidgetItem(target.store_name))
                self.table.setItem(row, 5, QTableWidgetItem("활성" if target.enabled else "비활성"))

                # 마지막 확인 시간
                last_check = target.last_checked.strftime("%Y-%m-%d %H:%M") if target.last_checked else "-"
                self.table.setItem(row, 6, QTableWidgetItem(last_check))

        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            QMessageBox.critical(self, "오류", f"데이터 로드 실패: {str(e)}")


class RankTrackingWorker(QThread):
    """순위 추적 워커 스레드"""

    progress_updated = Signal(int, str)  # 진행률, 메시지
    rank_result = Signal(object)  # 순위 결과
    error_occurred = Signal(str)  # 오류 메시지
    finished = Signal()

    def __init__(self, api_client: NaverShopAPI, calculator: RankCalculator):
        super().__init__()
        self.api_client = api_client
        self.calculator = calculator

        # 데이터베이스 초기화
        settings = get_settings()
        db_path = Path(settings.rank_tracking.db_file_name)
        self.db = RankDatabase(db_path)

        self.should_stop = False

    def stop(self):
        """작업 중지"""
        self.should_stop = True

    def run(self):
        """순위 추적 실행"""
        try:
            targets = self.db.get_active_targets()

            if not targets:
                self.progress_updated.emit(100, "추적할 대상이 없습니다.")
                self.finished.emit()
                return

            total = len(targets)

            for i, target in enumerate(targets):
                if self.should_stop:
                    break

                progress = int((i / total) * 100)
                self.progress_updated.emit(
                    progress,
                    f"검색 중: {target.product_id} - {target.keyword}"
                )

                try:
                    # 순위 계산
                    rank_result = self.calculator.calculate_single_rank(
                        target.keyword,
                        target.product_id
                    )

                    # 결과 저장 (키워드 ID와 대상 ID 필요)
                    keyword_obj = self.db.get_keyword_by_query(target.keyword)
                    target_obj = self.db.get_target_by_product_id(target.product_id)

                    if keyword_obj and target_obj:
                        self.db.save_rank_result(rank_result, keyword_obj.id, target_obj.id)

                    # 신호 발송
                    self.rank_result.emit(rank_result)

                except APIError as e:
                    error_msg = f"API 오류 ({target.product_id}): {str(e)}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)

                except Exception as e:
                    error_msg = f"순위 계산 실패 ({target.product_id}): {str(e)}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)

            self.progress_updated.emit(100, "순위 추적 완료")
            self.finished.emit()

        except Exception as e:
            logger.error(f"순위 추적 워커 오류: {e}")
            self.error_occurred.emit(f"순위 추적 실패: {str(e)}")
            self.finished.emit()


class RankTrackingWidget(QWidget):
    """순위 추적 메인 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings().rank_tracking

        # 컴포넌트 초기화
        self.api_client = None
        self.calculator = None
        self.scheduler = None
        self.worker = None

        self.init_ui()
        self.init_components()
        self.load_settings()

    def init_ui(self):
        """UI 초기화 - 개별 스크롤 가능한 섹션들"""
        # 메인 레이아웃 (스크롤 없음)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 상단 섹션 (수평 배치 - 고정 높이)
        top_section = QHBoxLayout()
        top_section.setSpacing(12)

        # 상태 정보와 설정을 수평으로 배치 (비율 조정)
        status_widget = self.create_scrollable_status_section()
        settings_widget = self.create_scrollable_settings_section()

        top_section.addWidget(status_widget, 1)  # 상태: 작게
        top_section.addWidget(settings_widget, 3)  # 설정: 크게 (비율 3:1)

        main_layout.addLayout(top_section)

        # 제어 섹션 (고정)
        control_widget = self.create_compact_control_section()
        main_layout.addWidget(control_widget)

        # 결과 섹션 (스크롤 가능)
        results_widget = self.create_scrollable_results_section()
        main_layout.addWidget(results_widget)

    def create_compact_status_section(self):
        """미니 상태 섹션 생성 - 더 작고 간결하게"""
        status_card = ModernCard("📊 상태")
        status_card.setMaximumHeight(120)  # 더 작게 (200 → 120)
        status_card.setStyleSheet(f"""
            ModernCard {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.OUTLINE};
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }}
        """)

        # 수평 레이아웃으로 간단하게
        status_layout = QHBoxLayout()
        status_layout.setSpacing(12)
        status_card.layout.addLayout(status_layout)

        # 상태만 크게 표시
        self.status_label = QLabel("⭕ 준비됨")
        self.status_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {MaterialColors.SUCCESS};
            padding: 2px;
        """)

        # 추적 대상 수
        self.targets_count_label = QLabel("0개")
        self.targets_count_label.setStyleSheet("font-size: 10px; font-weight: 500; color: #666;")

        # 마지막 확인 시간
        self.last_check_label = QLabel("미확인")
        self.last_check_label.setStyleSheet("font-size: 10px; color: #666;")

        # 간단하게 배치
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.targets_count_label)
        status_layout.addWidget(QLabel("|"))
        status_layout.addWidget(self.last_check_label)
        status_layout.addStretch()

        # 진행 바 (더 작게)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(15)  # 더 작게
        self.progress_bar.setVisible(False)
        status_card.layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("font-size: 9px; color: #666;")
        self.progress_label.setVisible(False)
        status_card.layout.addWidget(self.progress_label)

        return status_card

    def create_scrollable_status_section(self):
        """스크롤 가능한 상태 섹션"""
        # 외곽 컨테이너
        container = QFrame()
        container.setFixedHeight(150)  # 고정 높이
        container.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {MaterialColors.OUTLINE};
                border-radius: 8px;
                background: {MaterialColors.SURFACE};
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 12px; }
            QScrollBar::handle:vertical { background: #ccc; border-radius: 6px; }
        """)

        # 상태 내용
        status_content = self.create_compact_status_section()
        scroll_area.setWidget(status_content)

        container_layout.addWidget(scroll_area)
        return container

    def create_scrollable_settings_section(self):
        """스크롤 가능한 설정 섹션"""
        # 외곽 컨테이너
        container = QFrame()
        container.setFixedHeight(300)  # 고정 높이 (더 크게)
        container.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {MaterialColors.OUTLINE};
                border-radius: 8px;
                background: {MaterialColors.SURFACE};
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 12px; }
            QScrollBar::handle:vertical { background: #ccc; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background: #999; }
        """)

        # 설정 내용
        settings_content = self.create_compact_settings_section()
        scroll_area.setWidget(settings_content)

        container_layout.addWidget(scroll_area)
        return container

    def create_scrollable_results_section(self):
        """스크롤 가능한 결과 섹션"""
        # 외곽 컨테이너
        container = QFrame()
        container.setMinimumHeight(250)  # 최소 높이
        container.setMaximumHeight(400)  # 최대 높이
        container.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {MaterialColors.OUTLINE};
                border-radius: 8px;
                background: {MaterialColors.SURFACE};
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 헤더
        header = QLabel("📈 최근 결과")
        header.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {MaterialColors.ON_SURFACE};
            padding: 12px;
            background: #f8f9fa;
            border-bottom: 1px solid {MaterialColors.OUTLINE};
        """)
        container_layout.addWidget(header)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: white; }
            QScrollBar:vertical { width: 12px; }
            QScrollBar::handle:vertical { background: #ccc; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background: #999; }
        """)

        # 결과 내용 위젯
        results_content = QWidget()
        results_layout = QVBoxLayout(results_content)
        results_layout.setContentsMargins(12, 12, 12, 12)

        # 테이블과 빈 상태 메시지
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "시간", "상품ID", "키워드", "순위", "상태", "비고"
        ])

        # 테이블 스타일
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 11px;
                selection-background-color: #e3f2fd;
                border: none;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: 600;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
        """)

        # 헤더 설정
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)

        # 빈 상태 메시지
        self.empty_results_label = QLabel("📋 순위 확인 결과가 여기에 표시됩니다")
        self.empty_results_label.setStyleSheet("""
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 40px;
            font-size: 12px;
        """)
        self.empty_results_label.setAlignment(Qt.AlignCenter)

        results_layout.addWidget(self.empty_results_label)
        results_layout.addWidget(self.results_table)

        scroll_area.setWidget(results_content)
        container_layout.addWidget(scroll_area)

        return container

    def create_info_label(self, text, style):
        """정보 라벨 생성 헬퍼"""
        label = QLabel(text)
        label.setStyleSheet(style)
        return label

    def create_compact_settings_section(self):
        """사용하기 편한 설정 섹션 생성 - 입력 필드 크게"""
        settings_card = ModernCard("⚙️ API 설정")
        settings_card.setMinimumHeight(240)  # 더 크게 (200 → 240)

        settings_layout = QGridLayout()
        settings_layout.setSpacing(12)  # 간격 늘림
        settings_card.layout.addLayout(settings_layout)

        label_style = "font-size: 14px; color: #333; font-weight: 600;"  # 라벨 더 크고 진하게

        # ID 입력 (크게 만들기)
        settings_layout.addWidget(self.create_info_label("클라이언트 ID:", label_style), 0, 0)
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("네이버 개발자센터에서 발급받은 클라이언트 ID")
        self.client_id_input.setMinimumHeight(40)  # 훨씬 크게 (28 → 40)
        self.client_id_input.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
        """)
        settings_layout.addWidget(self.client_id_input, 0, 1)

        # Secret 입력 (크게 만들기)
        settings_layout.addWidget(self.create_info_label("Client Secret:", label_style), 1, 0)
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        self.client_secret_input.setPlaceholderText("네이버 개발자센터에서 발급받은 클라이언트 Secret")
        self.client_secret_input.setMinimumHeight(40)  # 훨씬 크게 (28 → 40)
        self.client_secret_input.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
        """)
        settings_layout.addWidget(self.client_secret_input, 1, 1)

        # 간격 설정 (크게 만들기)
        settings_layout.addWidget(self.create_info_label("확인 간격(분):", label_style), 2, 0)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 1440)
        self.interval_input.setValue(self.settings.schedule_interval_minutes)
        self.interval_input.setMinimumHeight(40)  # 크게 (28 → 40)
        self.interval_input.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
        """)
        settings_layout.addWidget(self.interval_input, 2, 1)

        # 저장 버튼 (더 크게)
        save_settings_btn = QPushButton("💾 설정 저장")
        save_settings_btn.setMinimumHeight(45)  # 훨씬 크게 (32 → 45)
        save_settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                transform: translateY(0px);
            }}
        """)
        save_settings_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings_btn, 3, 0, 1, 2)

        return settings_card

    def create_compact_control_section(self):
        """사용하기 편한 제어 섹션 생성 - 버튼 크게"""
        control_card = ModernCard("🎮 제어")
        control_card.setMinimumHeight(120)  # 크게 (100 → 120)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(16)  # 간격 늘림
        control_card.layout.addLayout(control_layout)

        # 버튼 스타일 (크게 만들기)
        button_style_base = """
            QPushButton {{
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 20px;
                font-weight: 600;
                font-size: 14px;
                min-width: 130px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            QPushButton:pressed {{
                transform: translateY(0px);
            }}
        """

        # 키워드 관리 버튼 (크게)
        manage_keywords_btn = QPushButton("📝 키워드 관리")
        manage_keywords_btn.setStyleSheet(f"""
            {button_style_base}
            QPushButton {{ background-color: {MaterialColors.PRIMARY}; }}
            QPushButton:hover {{ background-color: #1d4ed8; }}
        """)
        manage_keywords_btn.clicked.connect(self.open_keyword_management)
        control_layout.addWidget(manage_keywords_btn)

        # 수동 확인 버튼 (크게)
        manual_check_btn = QPushButton("🔍 수동 확인")
        manual_check_btn.setStyleSheet(f"""
            {button_style_base}
            QPushButton {{ background-color: {MaterialColors.WARNING}; }}
            QPushButton:hover {{ background-color: #c2410c; }}
        """)
        manual_check_btn.clicked.connect(self.start_manual_check)
        control_layout.addWidget(manual_check_btn)

        # 스케줄러 토글 버튼 (크게)
        self.scheduler_btn = QPushButton("⏰ 자동 추적")
        self.scheduler_btn.setStyleSheet(f"""
            {button_style_base}
            QPushButton {{ background-color: {MaterialColors.SUCCESS}; }}
            QPushButton:hover {{ background-color: #047857; }}
        """)
        self.scheduler_btn.clicked.connect(self.toggle_scheduler)
        control_layout.addWidget(self.scheduler_btn)

        control_layout.addStretch()

        return control_card

    def init_components(self):
        """컴포넌트 초기화"""
        try:
            # API 클라이언트 초기화는 설정 로드 후에 진행
            pass
        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {e}")

    def load_settings(self):
        """설정 로드"""
        try:
            if self.settings.naver_client_id:
                self.client_id_input.setText(self.settings.naver_client_id)
            if self.settings.naver_client_secret:
                self.client_secret_input.setText(self.settings.naver_client_secret)

            self.update_status()
            self.load_recent_results()

        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")

    def save_settings(self):
        """설정 저장"""
        try:
            from .settings import update_settings

            update_settings(
                rank_tracking__naver_client_id=self.client_id_input.text().strip(),
                rank_tracking__naver_client_secret=self.client_secret_input.text().strip(),
                rank_tracking__schedule_interval_minutes=self.interval_input.value()
            )

            # API 클라이언트 재초기화
            self.init_api_client()

            QMessageBox.information(self, "성공", "설정이 저장되었습니다.")

        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            QMessageBox.critical(self, "오류", f"설정 저장 실패: {str(e)}")

    def init_api_client(self):
        """API 클라이언트 초기화"""
        try:
            client_id = self.client_id_input.text().strip()
            client_secret = self.client_secret_input.text().strip()

            if client_id and client_secret:
                self.api_client = NaverShopAPI(
                    client_id=client_id,
                    client_secret=client_secret,
                    min_delay=self.settings.api_rate_limit_min,
                    max_delay=self.settings.api_rate_limit_max
                )

                self.calculator = RankCalculator(
                    api_client=self.api_client,
                    max_scan_depth=self.settings.max_scan_depth
                )

                self.status_label.setText("✅ 준비완료")
                self.status_label.setStyleSheet(f"""
                    font-size: 18px;
                    font-weight: 600;
                    color: {MaterialColors.SUCCESS};
                    padding: 8px;
                """)

        except Exception as e:
            logger.error(f"API 클라이언트 초기화 실패: {e}")
            self.status_label.setText("❌ 오류")
            self.status_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: 600;
                color: {MaterialColors.ERROR};
                padding: 8px;
            """)

    def update_status(self):
        """상태 정보 업데이트"""
        try:
            settings = get_settings()
            db_path = Path(settings.rank_tracking.db_file_name)
            db = RankDatabase(db_path)
            targets = db.get_active_targets()
            self.targets_count_label.setText(f"{len(targets)}개")

            # 마지막 확인 시간 업데이트
            if targets:
                last_checks = [t.last_checked for t in targets if t.last_checked]
                if last_checks:
                    latest = max(last_checks)
                    self.last_check_label.setText(latest.strftime("%Y-%m-%d %H:%M"))
                else:
                    self.last_check_label.setText("없음")
            else:
                self.last_check_label.setText("없음")

        except Exception as e:
            logger.error(f"상태 업데이트 실패: {e}")

    def load_recent_results(self):
        """최근 결과 로드 - 빈 상태 처리 개선"""
        try:
            settings = get_settings()
            db_path = Path(settings.rank_tracking.db_file_name)
            db = RankDatabase(db_path)
            results = db.get_recent_results(limit=10)

            # 빈 상태 처리
            if not results:
                self.empty_results_label.setVisible(True)
                self.results_table.setVisible(False)
                self.results_table.setRowCount(0)
                return

            # 결과가 있으면 테이블 표시
            self.empty_results_label.setVisible(False)
            self.results_table.setVisible(True)
            self.results_table.setRowCount(len(results))

            for row, result in enumerate(results):
                # 시간 (더 간결하게)
                time_str = result.observed_at.strftime("%m-%d %H:%M") if hasattr(result, 'observed_at') else "알 수 없음"
                self.results_table.setItem(row, 0, QTableWidgetItem(time_str))

                # 상품ID
                product_id = getattr(result, 'product_id', '알 수 없음')
                self.results_table.setItem(row, 1, QTableWidgetItem(str(product_id)))

                # 키워드
                keyword = getattr(result, 'keyword', '알 수 없음')
                self.results_table.setItem(row, 2, QTableWidgetItem(str(keyword)))

                # 순위 표시 (개선된 색상)
                rank_position = getattr(result, 'rank_position', None)
                rank_text = str(rank_position) if rank_position else "-"
                rank_item = QTableWidgetItem(rank_text)

                # 순위별 색상 구분
                if rank_position:
                    if rank_position <= 10:
                        rank_item.setStyleSheet("background-color: #e8f5e8; color: #2d5a2d; font-weight: bold;")
                    elif rank_position <= 50:
                        rank_item.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold;")
                    else:
                        rank_item.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")

                self.results_table.setItem(row, 3, rank_item)

                # 상태 표시
                status = getattr(result, 'status', 'unknown')
                status_text = {
                    'FOUND': "✅ 발견",
                    'NOT_FOUND': "❌ 미발견",
                    'ERROR': "⚠️ 오류"
                }.get(status, f"? {status}")

                status_item = QTableWidgetItem(status_text)
                if 'ERROR' in status_text:
                    status_item.setStyleSheet("color: #dc2626;")
                elif '발견' in status_text:
                    status_item.setStyleSheet("color: #059669;")
                else:
                    status_item.setStyleSheet("color: #ea580c;")

                self.results_table.setItem(row, 4, status_item)

                # 비고 (더 자세한 정보)
                total_scanned = getattr(result, 'total_results', 0)
                note = f"총 {total_scanned}개 검색" if total_scanned else "정보 없음"
                self.results_table.setItem(row, 5, QTableWidgetItem(note))

        except Exception as e:
            logger.error(f"최근 결과 로드 실패: {e}")
            # 오류 시에도 빈 상태 표시
            self.empty_results_label.setText("⚠️ 결과 로드 중 오류가 발생했습니다")
            self.empty_results_label.setVisible(True)
            self.results_table.setVisible(False)

    def open_keyword_management(self):
        """키워드 관리 다이얼로그 열기"""
        dialog = KeywordManagementDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_status()

    def start_manual_check(self):
        """수동 확인 시작"""
        if not self.api_client:
            QMessageBox.warning(
                self, "설정 필요",
                "먼저 API 설정을 완료해주세요."
            )
            return

        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "진행 중", "이미 순위 확인이 진행 중입니다.")
            return

        self.worker = RankTrackingWorker(self.api_client, self.calculator)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.rank_result.connect(self.handle_rank_result)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.on_worker_finished)

        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker.start()

    def toggle_scheduler(self):
        """스케줄러 토글"""
        if not self.api_client:
            QMessageBox.warning(
                self, "설정 필요",
                "먼저 API 설정을 완료해주세요."
            )
            return

        if not self.scheduler or not self.scheduler.is_running():
            # 스케줄러 시작
            try:
                settings = get_settings()
                db_path = Path(settings.rank_tracking.db_file_name)
                db = RankDatabase(db_path)
                config = self.settings

                # RankTrackingSettings를 ScheduleConfig로 변환
                from .rank_tracker.scheduler import ScheduleConfig
                schedule_config = ScheduleConfig(
                    interval_minutes=config.schedule_interval_minutes,
                    max_concurrent_jobs=config.max_concurrent_jobs,
                    retry_attempts=config.retry_attempts,
                    error_threshold=config.error_threshold
                )

                self.scheduler = RankScheduler(
                    api_client=self.api_client,
                    database=db,
                    config=schedule_config,
                    result_callback=self.handle_rank_result
                )

                self.scheduler.start()

                self.scheduler_btn.setText("⏹️ 자동 추적 중지")
                self.scheduler_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {MaterialColors.ERROR};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-weight: 600;
                        min-width: 140px;
                    }}
                """)

                self.status_label.setText("🔄 자동 추적 중")
                self.status_label.setStyleSheet(f"""
                    font-size: 18px;
                    font-weight: 600;
                    color: {MaterialColors.PRIMARY};
                    padding: 8px;
                """)

            except Exception as e:
                logger.error(f"스케줄러 시작 실패: {e}")
                QMessageBox.critical(self, "오류", f"스케줄러 시작 실패: {str(e)}")
        else:
            # 스케줄러 중지
            self.scheduler.stop()

            self.scheduler_btn.setText("⏰ 자동 추적 시작")
            self.scheduler_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {MaterialColors.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 140px;
                }}
            """)

            self.status_label.setText("✅ 준비완료")
            self.status_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: 600;
                color: {MaterialColors.SUCCESS};
                padding: 8px;
            """)

    def update_progress(self, value: int, message: str):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)

    def handle_rank_result(self, result: RankResult):
        """순위 결과 처리"""
        self.load_recent_results()
        self.update_status()

    def handle_error(self, error_message: str):
        """오류 처리"""
        logger.error(f"순위 추적 오류: {error_message}")
        # 에러는 메인 앱의 오류 추적 시스템에서 처리됨

    def on_worker_finished(self):
        """워커 완료 처리"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.load_recent_results()
        self.update_status()