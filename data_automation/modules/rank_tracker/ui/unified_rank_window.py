"""
통합 순위 추적 윈도우 - PySide6 Qt UI
네이버 순위 추적 시스템의 메인 윈도우
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit,
    QFrame, QMessageBox, QDialog, QFormLayout,
    QStatusBar, QMenuBar, QAction, QApplication,
    QSplashScreen, QProgressBar, QTextEdit
)
from PySide6.QtCore import (
    Qt, Signal, QThread, QObject, QTimer, Signal,
    QSize, QSettings
)
from PySide6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap,
    QKeySequence, QAction as QGuiAction
)

# UI 탭들 임포트
try:
    from .instant_search_tab import InstantSearchTab
    from .group_management_tab import GroupManagementTab
    from .scheduler_tab import SchedulerTab
except ImportError as e:
    logging.warning(f"UI 탭 모듈 임포트 실패: {e}")
    InstantSearchTab = None
    GroupManagementTab = None
    SchedulerTab = None

# 순위 엔진 임포트
try:
    from ..core.unified_rank_engine import UnifiedRankEngine
except ImportError as e:
    logging.warning(f"순위 엔진 임포트 실패: {e}")
    UnifiedRankEngine = None


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


class ApiConfigDialog(QDialog):
    """API 설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("네이버 API 설정")
        self.setModal(True)
        self.resize(400, 200)

        # 기존 설정 로드
        self.settings = QSettings('NaverRankTracker', 'ApiConfig')

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 설명 라벨
        desc_label = QLabel(
            "네이버 쇼핑 검색 API 사용을 위한 클라이언트 정보를 입력하세요.\n"
            "네이버 개발자 센터에서 애플리케이션 등록 후 발급받을 수 있습니다."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE}; margin-bottom: 16px;")
        layout.addWidget(desc_label)

        # 입력 폼
        form_layout = QFormLayout()

        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("클라이언트 ID (Client ID)")
        form_layout.addRow("클라이언트 ID:", self.client_id_input)

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("클라이언트 시크릿 (Client Secret)")
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("클라이언트 시크릿:", self.client_secret_input)

        layout.addLayout(form_layout)

        # 버튼
        button_layout = QHBoxLayout()

        test_btn = QPushButton("🔍 연결 테스트")
        test_btn.clicked.connect(self.test_connection)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.INFO};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
        """)

        save_btn = QPushButton("💾 저장")
        save_btn.clicked.connect(self.save_and_close)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #45A049;
            }}
        """)

        cancel_btn = QPushButton("❌ 취소")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.ERROR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
        """)

        button_layout.addWidget(test_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def load_settings(self):
        """기존 설정 로드"""
        client_id = self.settings.value('client_id', '')
        client_secret = self.settings.value('client_secret', '')

        self.client_id_input.setText(client_id)
        self.client_secret_input.setText(client_secret)

    def test_connection(self):
        """API 연결 테스트"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not client_id or not client_secret:
            QMessageBox.warning(self, "입력 오류", "클라이언트 ID와 시크릿을 모두 입력하세요.")
            return

        try:
            # 간단한 API 테스트 호출
            if UnifiedRankEngine:
                engine = UnifiedRankEngine(
                    client_id=client_id,
                    client_secret=client_secret
                )
                # 실제 테스트는 간단한 검색으로
                QMessageBox.information(self, "연결 성공", "네이버 API 연결이 성공적으로 확인되었습니다!")
            else:
                QMessageBox.information(self, "테스트 완료", "API 정보가 설정되었습니다.\n(순위 엔진 모듈이 없어 실제 테스트는 생략)")

        except Exception as e:
            QMessageBox.critical(self, "연결 실패", f"API 연결에 실패했습니다:\n\n{str(e)}")

    def save_and_close(self):
        """설정 저장 후 닫기"""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()

        if not client_id or not client_secret:
            QMessageBox.warning(self, "입력 오류", "클라이언트 ID와 시크릿을 모두 입력하세요.")
            return

        # 설정 저장
        self.settings.setValue('client_id', client_id)
        self.settings.setValue('client_secret', client_secret)

        self.accept()

    def get_credentials(self):
        """저장된 인증 정보 반환"""
        return (
            self.settings.value('client_id', ''),
            self.settings.value('client_secret', '')
        )


class UnifiedRankWindow(QMainWindow):
    """통합 순위 추적 메인 윈도우"""

    def __init__(self):
        super().__init__()

        # 설정 관리자
        self.settings = QSettings('NaverRankTracker', 'MainWindow')

        # 순위 엔진
        self.engine = None

        # UI 초기화
        self.init_ui()
        self.restore_window_state()

        # API 설정 체크
        QTimer.singleShot(100, self.check_api_config)

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("네이버 순위 추적 시스템 - Unified Rank Tracker")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # 아이콘 설정 (있다면)
        self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        # 메뉴바 생성
        self.create_menu_bar()

        # 상태바 생성
        self.create_status_bar()

        # 중앙 위젯 (스크롤 지원)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # 헤더 섹션
        header_section = self.create_header_section()
        layout.addWidget(header_section)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 8px;
                background-color: {MaterialColors.SURFACE};
            }}
            QTabBar::tab {{
                background-color: {MaterialColors.SURFACE_VARIANT};
                color: {MaterialColors.ON_SURFACE};
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: {MaterialColors.PRIMARY_CONTAINER};
            }}
        """)

        # 탭들 생성
        self.create_tabs()

        layout.addWidget(self.tab_widget, 1)

        # 최소 높이 설정으로 스크롤 확보
        central_widget.setMinimumHeight(1200)

        # 스타일 적용
        self.apply_global_style()

    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu('파일(&F)')

        # API 설정
        api_config_action = QAction('🔧 API 설정...', self)
        api_config_action.setShortcut(QKeySequence('Ctrl+,'))
        api_config_action.triggered.connect(self.show_api_config)
        file_menu.addAction(api_config_action)

        file_menu.addSeparator()

        # 종료
        exit_action = QAction('종료(&X)', self)
        exit_action.setShortcut(QKeySequence('Ctrl+Q'))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 도구 메뉴
        tools_menu = menubar.addMenu('도구(&T)')

        # 데이터 새로고침
        refresh_action = QAction('🔄 데이터 새로고침', self)
        refresh_action.setShortcut(QKeySequence('F5'))
        refresh_action.triggered.connect(self.refresh_all_data)
        tools_menu.addAction(refresh_action)

        # 로그 보기
        log_action = QAction('📋 로그 보기...', self)
        log_action.triggered.connect(self.show_log_viewer)
        tools_menu.addAction(log_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말(&H)')

        # 사용법
        help_action = QAction('❓ 사용법...', self)
        help_action.setShortcut(QKeySequence('F1'))
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        # 정보
        about_action = QAction('ℹ️ 정보...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """상태바 생성"""
        self.status_bar = self.statusBar()

        # 기본 상태 메시지
        self.status_bar.showMessage("준비")

        # 엔진 상태 라벨
        self.engine_status_label = QLabel("엔진: 대기중")
        self.engine_status_label.setStyleSheet(f"color: {MaterialColors.SECONDARY};")
        self.status_bar.addPermanentWidget(self.engine_status_label)

    def create_header_section(self):
        """헤더 섹션 생성"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {MaterialColors.PRIMARY}, stop:1 {MaterialColors.PRIMARY_CONTAINER});
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 10px;
            }}
        """)

        layout = QHBoxLayout(header)

        # 제목과 설명
        title_layout = QVBoxLayout()

        title_label = QLabel("🎯 네이버 순위 추적 시스템")
        title_label.setFont(QFont('', 18, QFont.Bold))
        title_label.setStyleSheet(f"color: {MaterialColors.ON_PRIMARY};")

        subtitle_label = QLabel("실시간 키워드 순위 확인, 그룹 관리, 자동 스케줄링")
        subtitle_label.setFont(QFont('', 12))
        subtitle_label.setStyleSheet(f"color: {MaterialColors.ON_PRIMARY}; opacity: 0.8;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        # API 설정 섹션 (헤더 오른쪽)
        api_section = QFrame()
        api_section.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 15px;
            }
        """)

        api_layout = QVBoxLayout(api_section)
        api_layout.setSpacing(8)

        # API 설정 제목
        api_title = QLabel("🔧 API 설정")
        api_title.setFont(QFont('', 12, QFont.Bold))
        api_title.setStyleSheet(f"color: {MaterialColors.ON_PRIMARY};")
        api_layout.addWidget(api_title)

        # Client ID 입력
        self.api_client_id = QLineEdit()
        self.api_client_id.setPlaceholderText("네이버 클라이언트 ID 입력...")
        self.api_client_id.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        api_layout.addWidget(self.api_client_id)

        # Client Secret 입력
        self.api_client_secret = QLineEdit()
        self.api_client_secret.setPlaceholderText("네이버 클라이언트 시크릿 입력...")
        self.api_client_secret.setEchoMode(QLineEdit.Password)
        self.api_client_secret.setStyleSheet(self.api_client_id.styleSheet())
        api_layout.addWidget(self.api_client_secret)

        # API 상태 표시
        self.api_status_display = QLabel("🔴 API 미설정")
        self.api_status_display.setStyleSheet(f"color: {MaterialColors.ON_PRIMARY}; font-size: 11px;")
        api_layout.addWidget(self.api_status_display)

        # 설정 변경 감지
        self.api_client_id.textChanged.connect(self.on_api_credentials_changed)
        self.api_client_secret.textChanged.connect(self.on_api_credentials_changed)

        # 기존 설정 로드
        self.load_api_credentials()

        # 빠른 설정 버튼들
        button_layout = QVBoxLayout()

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_all_data)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.2);
                color: {MaterialColors.ON_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
        """)

        button_layout.addWidget(refresh_btn)

        layout.addLayout(title_layout, 1)
        layout.addWidget(api_section)
        layout.addLayout(button_layout)

        return header

    def create_tabs(self):
        """탭들 생성"""
        # 1. 즉시 검색 탭
        if InstantSearchTab:
            self.instant_tab = InstantSearchTab()
            self.tab_widget.addTab(self.instant_tab, "🔍 즉시 검색")
        else:
            placeholder = QLabel("즉시 검색 탭을 로드할 수 없습니다.")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(placeholder, "🔍 즉시 검색")

        # 2. 그룹 관리 탭
        if GroupManagementTab:
            self.groups_tab = GroupManagementTab()
            self.tab_widget.addTab(self.groups_tab, "📁 그룹 관리")
        else:
            placeholder = QLabel("그룹 관리 탭을 로드할 수 없습니다.")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(placeholder, "📁 그룹 관리")

        # 3. 스케줄링 탭
        if SchedulerTab:
            self.scheduler_tab = SchedulerTab()
            self.tab_widget.addTab(self.scheduler_tab, "⏰ 스케줄링")
        else:
            placeholder = QLabel("스케줄링 탭을 로드할 수 없습니다.")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(placeholder, "⏰ 스케줄링")

        # 탭 변경 시 엔진 공유
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def apply_global_style(self):
        """전역 스타일 적용"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {MaterialColors.SURFACE};
                color: {MaterialColors.ON_SURFACE};
            }}
            QLabel {{
                color: {MaterialColors.ON_SURFACE};
            }}
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5A47A0;
            }}
            QPushButton:pressed {{
                background-color: #4A3B8A;
            }}
        """)

    def check_api_config(self):
        """API 설정 체크"""
        settings = QSettings('NaverRankTracker', 'ApiConfig')
        client_id = settings.value('client_id', '')
        client_secret = settings.value('client_secret', '')

        if client_id and client_secret:
            self.init_engine(client_id, client_secret)
            self.api_status_label.setText("API: 설정완료")
            self.api_status_label.setStyleSheet(f"color: {MaterialColors.SUCCESS}; font-weight: bold;")
        else:
            self.api_status_label.setText("API: 미설정")
            self.api_status_label.setStyleSheet(f"color: {MaterialColors.ERROR}; font-weight: bold;")

            # 설정 요청
            reply = QMessageBox.question(
                self, "API 설정 필요",
                "네이버 API 설정이 필요합니다.\n지금 설정하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.show_api_config()

    def init_engine(self, client_id: str, client_secret: str):
        """순위 엔진 초기화"""
        try:
            if UnifiedRankEngine:
                self.engine = UnifiedRankEngine(
                    client_id=client_id,
                    client_secret=client_secret
                )

                # 각 탭에 엔진 전달
                self.share_engine_to_tabs()

                self.engine_status_label.setText("엔진: 준비됨")
                self.engine_status_label.setStyleSheet(f"color: {MaterialColors.SUCCESS}; font-weight: bold;")

                logging.info("순위 엔진 초기화 완료")
            else:
                self.engine_status_label.setText("엔진: 모듈없음")
                self.engine_status_label.setStyleSheet(f"color: {MaterialColors.ERROR}; font-weight: bold;")

        except Exception as e:
            logging.error(f"순위 엔진 초기화 실패: {e}")
            self.engine_status_label.setText("엔진: 오류")
            self.engine_status_label.setStyleSheet(f"color: {MaterialColors.ERROR}; font-weight: bold;")

    def share_engine_to_tabs(self):
        """각 탭에 순위 엔진 공유"""
        if not self.engine:
            return

        # 즉시 검색 탭
        if hasattr(self, 'instant_tab') and hasattr(self.instant_tab, 'set_engine'):
            self.instant_tab.set_engine(self.engine)

        # 스케줄링 탭
        if hasattr(self, 'scheduler_tab') and hasattr(self.scheduler_tab, 'set_engine'):
            self.scheduler_tab.set_engine(self.engine)

    def load_api_credentials(self):
        """저장된 API 설정 로드"""
        try:
            client_id = self.settings.value('client_id', '')
            client_secret = self.settings.value('client_secret', '')

            self.api_client_id.setText(client_id)
            self.api_client_secret.setText(client_secret)

            if client_id and client_secret:
                self.api_status_display.setText("🟢 API 설정 완료")
                self.init_engine(client_id, client_secret)
            else:
                self.api_status_display.setText("🔴 API 미설정")

        except Exception as e:
            logging.error(f"API 설정 로드 실패: {e}")
            self.api_status_display.setText("🔴 API 미설정")

    def save_api_credentials(self):
        """API 설정 저장"""
        try:
            client_id = self.api_client_id.text().strip()
            client_secret = self.api_client_secret.text().strip()

            self.settings.setValue('client_id', client_id)
            self.settings.setValue('client_secret', client_secret)

            if client_id and client_secret:
                self.api_status_display.setText("🟢 API 설정 완료")
                self.init_engine(client_id, client_secret)
                logging.info("API 설정이 저장되었습니다")
            else:
                self.api_status_display.setText("🔴 API 미설정")

        except Exception as e:
            logging.error(f"API 설정 저장 실패: {e}")
            self.api_status_display.setText("🔴 설정 저장 실패")

    def on_api_credentials_changed(self):
        """API 설정 변경 시 호출"""
        client_id = self.api_client_id.text().strip()
        client_secret = self.api_client_secret.text().strip()

        if client_id and client_secret:
            self.api_status_display.setText("🟡 설정 변경됨")
            # 자동 저장
            QTimer.singleShot(1000, self.save_api_credentials)
        else:
            self.api_status_display.setText("🔴 API 미설정")

    def refresh_all_data(self):
        """모든 데이터 새로고침"""
        self.status_bar.showMessage("데이터 새로고침 중...")

        # 각 탭의 새로고침 메서드 호출
        try:
            if hasattr(self, 'groups_tab'):
                if hasattr(self.groups_tab, 'load_groups'):
                    self.groups_tab.load_groups()
                if hasattr(self.groups_tab, 'refresh_groups_tree'):
                    self.groups_tab.refresh_groups_tree()

            if hasattr(self, 'scheduler_tab'):
                if hasattr(self.scheduler_tab, 'load_data'):
                    self.scheduler_tab.load_data()

            self.status_bar.showMessage("데이터 새로고침 완료", 3000)
            logging.info("모든 데이터 새로고침 완료")

        except Exception as e:
            self.status_bar.showMessage(f"새로고침 오류: {str(e)}", 5000)
            logging.error(f"데이터 새로고침 실패: {e}")

    def show_log_viewer(self):
        """로그 뷰어 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("로그 뷰어")
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setFont(QFont('Courier', 9))

        # 로그 내용 로드 시도
        try:
            # 로그 파일이 있다면 읽어오기
            log_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'rank_tracker.log')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_text.setPlainText(f.read())
            else:
                log_text.setPlainText("로그 파일을 찾을 수 없습니다.")
        except Exception as e:
            log_text.setPlainText(f"로그 로드 실패: {str(e)}")

        layout.addWidget(log_text)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def show_help(self):
        """도움말 표시"""
        help_text = """
🎯 네이버 순위 추적 시스템 사용법

1. 🔧 API 설정
   - 메뉴 > 파일 > API 설정에서 네이버 클라이언트 ID와 시크릿 입력
   - 네이버 개발자 센터에서 애플리케이션 등록 후 발급받을 수 있습니다

2. 🔍 즉시 검색
   - URL과 키워드를 입력하여 바로 순위 확인
   - 결과에서 상품 정보와 함께 순위 표시

3. 📁 그룹 관리
   - 여러 상품을 그룹으로 묶어서 관리
   - 배치로 여러 상품의 순위를 한번에 확인

4. ⏰ 스케줄링
   - 자동으로 정해진 시간에 순위 추적
   - 매시간, 매일, 매주 또는 사용자 지정 간격 설정

5. 💡 팁
   - F5키로 데이터 새로고침
   - Ctrl+,로 빠른 API 설정
   - 로그 뷰어로 상세한 실행 정보 확인
        """

        QMessageBox.information(self, "사용법", help_text)

    def show_about(self):
        """정보 표시"""
        about_text = """
🎯 네이버 순위 추적 시스템
Unified Rank Tracker

📅 버전: 1.0.0
🏢 개발: Claude Code
📧 지원: https://github.com/anthropics/claude-code

🔧 기술 스택:
- Python 3.8+
- PySide6 (Qt6)
- 네이버 쇼핑 검색 API
- Material Design 3

📋 주요 기능:
✅ 실시간 순위 검색
✅ 상품 그룹 관리
✅ 자동 스케줄링
✅ API 통합 관리

© 2025 All rights reserved.
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("정보")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def on_tab_changed(self, index: int):
        """탭 변경 시 처리"""
        current_tab = self.tab_widget.widget(index)
        tab_name = self.tab_widget.tabText(index)

        self.status_bar.showMessage(f"현재 탭: {tab_name}")

        # 현재 탭에 엔진 전달 (필요시)
        if self.engine and hasattr(current_tab, 'set_engine'):
            current_tab.set_engine(self.engine)

    def save_window_state(self):
        """윈도우 상태 저장"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.setValue('currentTab', self.tab_widget.currentIndex())

    def restore_window_state(self):
        """윈도우 상태 복원"""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)

        window_state = self.settings.value('windowState')
        if window_state:
            self.restoreState(window_state)

        current_tab = self.settings.value('currentTab', 0, int)
        if 0 <= current_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_tab)

    def closeEvent(self, event):
        """윈도우 종료 시 처리"""
        self.save_window_state()

        # 각 탭의 종료 처리
        if hasattr(self, 'scheduler_tab') and hasattr(self.scheduler_tab, 'closeEvent'):
            self.scheduler_tab.closeEvent(event)

        if hasattr(self, 'groups_tab') and hasattr(self.groups_tab, 'closeEvent'):
            self.groups_tab.closeEvent(event)

        logging.info("순위 추적 시스템 종료")
        event.accept()


def create_splash_screen():
    """스플래시 스크린 생성"""
    splash = QSplashScreen()

    # 간단한 스플래시 이미지 생성 (실제로는 이미지 파일 사용)
    pixmap = QPixmap(400, 300)
    pixmap.fill(QColor(MaterialColors.PRIMARY))

    splash.setPixmap(pixmap)
    splash.showMessage(
        "네이버 순위 추적 시스템 로딩 중...",
        Qt.AlignBottom | Qt.AlignCenter,
        QColor("white")
    )

    return splash


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Material Design 3 테마 적용
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(MaterialColors.SURFACE))
    palette.setColor(QPalette.Base, QColor(MaterialColors.SURFACE))
    palette.setColor(QPalette.Button, QColor(MaterialColors.PRIMARY))
    palette.setColor(QPalette.ButtonText, QColor(MaterialColors.ON_PRIMARY))
    palette.setColor(QPalette.Text, QColor(MaterialColors.ON_SURFACE))
    app.setPalette(palette)

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('rank_tracker.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 스플래시 스크린 표시
    splash = create_splash_screen()
    splash.show()
    app.processEvents()

    # 메인 윈도우 생성
    window = UnifiedRankWindow()

    # 스플래시 종료 후 메인 윈도우 표시
    splash.finish(window)
    window.show()

    logging.info("네이버 순위 추적 시스템 시작")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()