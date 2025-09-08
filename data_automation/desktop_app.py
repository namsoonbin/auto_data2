import sys
import os
import logging
import json
import pandas as pd
from datetime import datetime, date
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QFileDialog, QLabel, QGroupBox, QGridLayout,
    QDialog, QTableWidget, QTableWidgetItem, QDateEdit, QHeaderView,
    QMessageBox, QSpinBox, QFrame, QProgressBar, QCheckBox, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import QThread, Signal, Qt, QDate, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter
import re

# New improved imports - qt-material + qtawesome
try:
    from qt_material import apply_stylesheet
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False
    print("qt-material을 사용할 수 없습니다.")

try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    QTAWESOME_AVAILABLE = False
    print("qtawesome을 사용할 수 없습니다.")

try:
    import pyqtdarktheme
    PYQTDARKTHEME_AVAILABLE = True
except ImportError:
    PYQTDARKTHEME_AVAILABLE = False
    print("pyqtdarktheme을 사용할 수 없습니다.")

# Import the existing modules
try:
    from modules import config, file_handler, report_generator
except ImportError as e:
    logging.error(f"모듈 import 실패: {e}")
    print("modules 폴더의 파이썬 파일들을 확인해주세요.")


# Material Design 3 Color System
class MaterialColors:
    """Material Design 3 색상 시스템"""
    PRIMARY = "#2563eb"
    SUCCESS = "#059669" 
    WARNING = "#ea580c"
    ERROR = "#dc2626"
    
    # 다크 모드
    DARK_BG = "#1a1a1a"
    DARK_SURFACE = "#2d2d2d"
    DARK_TEXT = "#ffffff"
    
    # 라이트 모드
    LIGHT_BG = "#f8fafc"
    LIGHT_SURFACE = "#ffffff"
    LIGHT_TEXT = "#1f2937"


# Theme Manager
class ThemeManager:
    """테마 관리 시스템"""
    def __init__(self, app):
        self.app = app
        self.is_dark_mode = True  # 다크모드 기본값
        
    def setup_auto_theme(self):
        """시스템 테마 자동 감지 및 적용"""
        try:
            if PYQTDARKTHEME_AVAILABLE:
                # pyqtdarktheme로 시스템 테마 감지
                pyqtdarktheme.setup_theme("auto")
            
            if QT_MATERIAL_AVAILABLE:
                # qt-material 테마 추가 적용
                theme_name = "dark_teal.xml" if self.is_dark_mode else "light_blue.xml"
                apply_stylesheet(self.app, theme=theme_name)
        except Exception as e:
            logging.warning(f"자동 테마 설정 실패: {e}")
            self.apply_default_theme()
    
    def apply_default_theme(self):
        """기본 다크 테마 적용"""
        try:
            if QT_MATERIAL_AVAILABLE:
                apply_stylesheet(self.app, theme='dark_teal.xml')
            self.is_dark_mode = True
        except Exception as e:
            logging.error(f"기본 테마 적용 실패: {e}")
    
    def toggle_theme(self):
        """수동 테마 전환"""
        try:
            if QT_MATERIAL_AVAILABLE:
                theme = "light_blue.xml" if self.is_dark_mode else "dark_teal.xml"
                apply_stylesheet(self.app, theme=theme)
            self.is_dark_mode = not self.is_dark_mode
            return self.is_dark_mode
        except Exception as e:
            logging.error(f"테마 전환 실패: {e}")
            return self.is_dark_mode


# Modern Card Widget
class ModernDataCard(QFrame):
    """Material Design 3 스타일 데이터 카드"""
    def __init__(self, title, value, icon_name, color=MaterialColors.PRIMARY, tooltip="", is_dark_mode=True):
        super().__init__()
        self.color = color
        self.is_dark_mode = is_dark_mode
        self.setFixedHeight(120)
        if tooltip:
            self.setToolTip(tooltip)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self.update_theme()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 헤더: 아이콘 + 제목
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # QtAwesome 아이콘
        if QTAWESOME_AVAILABLE:
            try:
                icon = qta.icon(icon_name, color=color)
                icon_label = QLabel()
                icon_pixmap = icon.pixmap(24, 24)
                icon_label.setPixmap(icon_pixmap)
            except Exception:
                # 아이콘 로드 실패 시 기본 이모지
                icon_label = QLabel("📊")
                icon_label.setStyleSheet("font-size: 20px;")
        else:
            icon_label = QLabel("📊")
            icon_label.setStyleSheet("font-size: 20px;")
        
        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {color};
            margin: 0;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 값 섹션
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: #212121;
            margin: 0;
        """)
        self.value_label.setObjectName(f"{title}_value")
        
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def update_theme(self):
        """테마에 따른 스타일 업데이트"""
        if self.is_dark_mode:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(48, 48, 48, 0.9);
                    border-radius: 12px;
                    border: 1px solid rgba(80, 80, 80, 0.8);
                    padding: 16px;
                    color: #ffffff;
                }}
                QFrame:hover {{
                    border-color: {self.color};
                    background-color: rgba(64, 64, 64, 0.95);
                    transform: translateY(-2px);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.9);
                    border-radius: 12px;
                    border: 1px solid rgba(229, 229, 229, 0.8);
                    padding: 16px;
                    color: #212121;
                }}
                QFrame:hover {{
                    border-color: {self.color};
                    background-color: rgba(248, 249, 250, 0.95);
                    transform: translateY(-2px);
                }}
            """)
    
    def update_value(self, new_value):
        """카드 값 업데이트"""
        self.value_label.setText(str(new_value))
        
    def set_dark_mode(self, is_dark):
        """다크모드 상태 변경"""
        self.is_dark_mode = is_dark
        self.update_theme()
        # 값 라벨 색상도 업데이트
        self.value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {'#ffffff' if self.is_dark_mode else '#212121'};
            margin: 0;
        """)


# Apple Style Button
class AppleStyleButton(QPushButton):
    """Apple 스타일 버튼"""
    def __init__(self, text, icon_name=None, color=MaterialColors.PRIMARY, parent=None):
        super().__init__(text, parent)
        
        if icon_name and QTAWESOME_AVAILABLE:
            try:
                icon = qta.icon(icon_name, color='white')
                self.setIcon(icon)
            except Exception:
                pass  # 아이콘 로드 실패 시 텍스트만 표시
        
        # 공식 문서에 따른 올바른 버튼 크기 설정
        self.setMinimumSize(100, 35)
        self.setMaximumSize(150, 45)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.2)};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)
    
    def _darken_color(self, color, factor=0.1):
        """색상을 어둡게 만드는 헬퍼 함수"""
        if color == MaterialColors.PRIMARY:
            return "#1d4ed8"  # 더 어두운 파란색
        elif color == MaterialColors.SUCCESS:
            return "#047857"  # 더 어두운 녹색
        elif color == MaterialColors.WARNING:
            return "#c2410c"  # 더 어두운 주황색
        elif color == MaterialColors.ERROR:
            return "#b91c1c"  # 더 어두운 빨간색
        else:
            return "#6b7280"  # 기본 회색


# Modern Log Viewer
class ModernLogViewer(QTextEdit):
    """Material Design 로그 뷰어"""
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(200)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MaterialColors.DARK_BG};
                color: {MaterialColors.DARK_TEXT};
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.4;
            }}
        """)


# Worker Thread for File Monitoring
class ModernWorker(QThread):
    """현대화된 파일 모니터링 워커 스레드"""
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)
    stats_update_signal = Signal(dict)

    def __init__(self, download_folder, password="1234"):
        super().__init__()
        self.download_folder = download_folder
        self.password = password
        self.is_running = False

    def run(self):
        """워커 스레드 실행"""
        try:
            self.is_running = True
            config.DOWNLOAD_DIR = self.download_folder
            config.ORDER_FILE_PASSWORD = self.password
            
            self.output_signal.emit("[INFO] 자동화 시작!")
            self.output_signal.emit(f"[INFO] 감시 폴더: {self.download_folder}")
            
            # 파일 핸들러 시작
            file_handler.start_monitoring()
            
        except Exception as e:
            error_msg = f"[ERROR] 모니터링 중 오류 발생: {str(e)}"
            self.error_signal.emit(error_msg)
            self.output_signal.emit(error_msg)
        finally:
            self.is_running = False
            self.finished_signal.emit()

    def stop(self):
        """워커 스레드 중지"""
        self.is_running = False
        self.output_signal.emit("[INFO] 자동화 중지 요청...")


# Manual Process Worker
class ModernManualWorker(QThread):
    """현대화된 수동 처리 워커 스레드"""
    output_signal = Signal(str)
    finished_signal = Signal()
    
    def __init__(self, download_folder, password="1234"):
        super().__init__()
        self.download_folder = download_folder
        self.password = password

    def run(self):
        """수동 처리 실행"""
        try:
            config.DOWNLOAD_DIR = self.download_folder
            config.ORDER_FILE_PASSWORD = self.password
            
            self.output_signal.emit("[INFO] 작업폴더 수동 처리 시작...")
            
            # 기존 파일 처리
            file_handler.process_existing_files()
            
            self.output_signal.emit("[INFO] 작업폴더 처리 완료!")
            
        except Exception as e:
            error_msg = f"[ERROR] 수동 처리 중 오류: {str(e)}"
            self.output_signal.emit(error_msg)
        finally:
            self.finished_signal.emit()


# Reward Manager Dialog - 원래 로직 완전 복원
class ModernRewardDialog(QDialog):
    """리워드 관리 팝업창 (하루 단위 설정) - 원래 로직"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('💰 일일 리워드 관리')
        self.setFixedSize(900, 650)  # 크기 축소
        self.setModal(True)
        
        # Material Design 3 스타일링 적용
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {MaterialColors.LIGHT_SURFACE};
                border-radius: 16px;
                border: 2px solid rgba(229, 229, 229, 0.8);
            }}
            QLabel {{
                color: {MaterialColors.LIGHT_TEXT};
            }}
            QPushButton {{
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                min-width: 80px;
                background-color: {MaterialColors.PRIMARY};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
            QTableWidget {{
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #F5F5F5;
            }}
            QTableWidget::item:selected {{
                background: #E3F2FD;
                color: #1976D2;
            }}
            QGroupBox {{
                font-weight: 600;
                border: 2px solid rgba(229, 229, 229, 0.8);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }}
        """)
        
        from modules import config
        self.reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
        self.margin_file = config.MARGIN_FILE
        
        self.all_rewards_data = {'rewards': []}
        self.products_df = pd.DataFrame()

        self.initUI()
        self.load_data_sources()
        self.load_rewards_for_date(QDate.currentDate())

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 스크롤 가능한 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(200, 200, 200, 0.3);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(150, 150, 150, 0.7);
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        # 스크롤 내용 위젯
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 헤더 (최소화)
        title_label = QLabel("리워드 관리")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #333333;
            margin: 5px 0px;
        """)
        layout.addWidget(title_label)
        
        # --- 날짜 선택 및 복사 ---
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setDate(QDate.currentDate())
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_rewards_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit()
        self.source_date_edit.setDate(QDate.currentDate().addDays(-1))
        self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        
        self.copy_button = QPushButton("의 설정 불러오기")
        self.copy_button.clicked.connect(self.copy_rewards)
        self.copy_button.setStyleSheet(f"background-color: {MaterialColors.WARNING}; color: white;")
        date_layout.addWidget(self.copy_button, 1, 2)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # --- 검색 및 일괄 설정 ---
        control_group = QGroupBox("검색 및 일괄 설정")
        control_layout = QGridLayout()
        
        # 첫 번째 줄: 검색
        control_layout.addWidget(QLabel("검색:"), 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("상품명으로 검색...")
        self.search_box.textChanged.connect(self.filter_products)
        control_layout.addWidget(self.search_box, 0, 1, 1, 2)
        
        # 두 번째 줄: 선택 관리
        self.select_all_checkbox = QCheckBox("전체 선택/해제")
        self.select_all_checkbox.clicked.connect(self.toggle_all_selection)
        control_layout.addWidget(self.select_all_checkbox, 1, 0)
        
        self.selected_count_label = QLabel("선택됨: 0개")
        self.selected_count_label.setStyleSheet("color: #666; font-size: 12px;")
        control_layout.addWidget(self.selected_count_label, 1, 1)
        
        # 세 번째 줄: 일괄 적용
        control_layout.addWidget(QLabel("선택된 항목에 적용:"), 2, 0)
        
        bulk_layout = QHBoxLayout()
        self.bulk_reward = QSpinBox()
        self.bulk_reward.setRange(0, 999999)
        self.bulk_reward.setSingleStep(1000)
        self.bulk_reward.setSuffix(" 원")
        self.bulk_reward.setValue(0)
        bulk_layout.addWidget(self.bulk_reward)
        
        # 빠른 설정 버튼들
        quick_buttons = [
            ("0원", 0),
            ("3K", 3000),
            ("6K", 6000),
            ("9K", 9000),
            ("12K", 12000)
        ]
        
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(50)
            btn.clicked.connect(lambda checked=False, v=value: self.bulk_reward.setValue(v))
            btn.setStyleSheet(f"""
                font-size: 11px; 
                padding: 4px;
                background-color: {MaterialColors.SUCCESS};
                min-width: 45px;
            """)
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        
        # 네 번째 줄: 적용 버튼
        self.apply_selected_button = QPushButton("선택된 항목에 적용")
        self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet(f"background-color: {MaterialColors.SUCCESS}; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # --- 상품 테이블 (스크롤 가능) ---
        # 스크롤 영역으로 테이블을 감싸기
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setMinimumHeight(350)  # 최소 높이 증가
        table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 테이블 위젯
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '리워드 금액'])
        self.product_table.setMinimumHeight(300)  # 테이블 최소 높이 설정
        self.product_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 테이블 스타일 개선
        self.product_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
                selection-background-color: #E3F2FD;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F5F5F5;
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
                color: #1976D2;
            }
            QHeaderView::section {
                background: #F8F9FA;
                border: none;
                padding: 12px 8px;
                font-weight: 600;
                font-size: 14px;
                color: #424242;
                border-bottom: 2px solid #E0E0E0;
            }
        """)
        
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 리워드
        
        # 행 높이 설정
        self.product_table.verticalHeader().setDefaultSectionSize(48)
        self.product_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.product_table)
        table_scroll.setWidget(table_container)
        
        layout.addWidget(table_scroll)
        
        # --- 저장 버튼 ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_rewards)
        self.save_button.setStyleSheet(f"background-color: {MaterialColors.SUCCESS}; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(f"background-color: {MaterialColors.ERROR}; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # 스크롤 영역에 내용 설정
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def load_data_sources(self):
        """초기 데이터 (상품 목록, 전체 리워드) 로드"""
        try:
            if os.path.exists(self.margin_file):
                df = pd.read_excel(self.margin_file, engine='openpyxl')
                if '상품번호' in df.columns:
                    df = df.rename(columns={'상품번호': '상품ID'})
                if '대표옵션' in df.columns:
                    df['대표옵션'] = df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                    df = df[df['대표옵션'] == True]
                self.products_df = df[['상품ID', '상품명']].drop_duplicates().sort_values(by='상품명')
            else:
                QMessageBox.warning(self, "경고", "마진정보.xlsx 파일을 찾을 수 없습니다.")

            if os.path.exists(self.reward_file):
                with open(self.reward_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        self.all_rewards_data = json.loads(content)
                    else:
                        self.all_rewards_data = {'rewards': []}
            else:
                self.all_rewards_data = {'rewards': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스를 로드하는 중 오류가 발생했습니다:\\n{e}")

    def load_rewards_for_date(self, q_date):
        """선택된 날짜의 리워드 정보를 테이블에 로드"""
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        # 날짜에 맞는 리워드 맵 생성
        reward_map = {}
        for entry in self.all_rewards_data.get('rewards', []):
            if entry.get('start_date') == target_date_str and entry.get('end_date') == target_date_str:
                reward_map[str(entry['product_id'])] = entry['reward']

        # 테이블 채우기
        self.product_table.setRowCount(0)
        self.product_table.setRowCount(len(self.products_df))
        
        for row, (_, product) in enumerate(self.products_df.iterrows()):
            product_id = str(product['상품ID'])
            
            # 체크박스 (0번 컬럼)
            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_selected_count)
            self.product_table.setCellWidget(row, 0, checkbox)
            
            # 상품ID (1번 컬럼)
            self.product_table.setItem(row, 1, QTableWidgetItem(product_id))
            
            # 상품명 (2번 컬럼)
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product['상품명'])))
            
            # 리워드 금액 (3번 컬럼)
            spinbox = QSpinBox()
            spinbox.setRange(0, 999999)
            spinbox.setSingleStep(1000)
            spinbox.setSuffix(" 원")
            spinbox.setValue(reward_map.get(product_id, 0))
            self.product_table.setCellWidget(row, 3, spinbox)
        
        self.filter_products()
        self.update_selected_count()

    def copy_rewards(self):
        """선택한 날짜의 설정을 현재 날짜의 테이블에 복사"""
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        
        reward_map = {}
        for entry in self.all_rewards_data.get('rewards', []):
            if entry.get('start_date') == source_date_str:
                reward_map[str(entry['product_id'])] = entry['reward']
        
        if not reward_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 리워드 설정이 없습니다.")
            return

        for row in range(self.product_table.rowCount()):
            product_id = self.product_table.item(row, 1).text()
            spinbox = self.product_table.cellWidget(row, 3)
            if spinbox and product_id in reward_map:
                spinbox.setValue(reward_map[product_id])
        
        QMessageBox.information(self, "완료", f"{source_date_str}의 설정이 현재 테이블로 복사되었습니다.\\n저장 버튼을 눌러야 최종 반영됩니다.")

    def toggle_all_selection(self):
        """전체 선택/해제 토글"""
        select_all = self.select_all_checkbox.isChecked()
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):  # 보이는 행만
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(select_all)
        self.update_selected_count()
    
    def update_selected_count(self):
        """선택된 항목 개수 업데이트"""
        selected_count = 0
        for row in range(self.product_table.rowCount()):
            checkbox = self.product_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        self.selected_count_label.setText(f"선택됨: {selected_count}개")
        self.apply_selected_button.setEnabled(selected_count > 0)
    
    def apply_to_selected(self):
        """선택된 항목에만 리워드 적용"""
        bulk_value = self.bulk_reward.value()
        applied_count = 0
        
        for row in range(self.product_table.rowCount()):
            checkbox = self.product_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                spinbox = self.product_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
        
        if applied_count > 0:
            QMessageBox.information(self, "완료", f"{applied_count}개 상품에 {bulk_value:,}원 리워드가 적용되었습니다.")
        else:
            QMessageBox.information(self, "알림", "선택된 상품이 없습니다.")

    def filter_products(self):
        """상품명으로 필터링"""
        search_text = self.search_box.text().lower()
        for row in range(self.product_table.rowCount()):
            product_name = self.product_table.item(row, 2).text().lower()
            self.product_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()

    def save_rewards(self):
        """현재 날짜의 리워드 설정을 저장"""
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            
            # 현재 날짜와 다른 날짜의 설정만 유지
            other_days_rewards = [
                entry for entry in self.all_rewards_data.get('rewards', [])
                if entry.get('start_date') != target_date_str
            ]
            
            # 현재 테이블의 설정 추가
            new_rewards_for_date = []
            for row in range(self.product_table.rowCount()):
                spinbox = self.product_table.cellWidget(row, 3)
                if spinbox and spinbox.value() > 0:  # 0원 초과만 저장
                    product_id = self.product_table.item(row, 1).text()
                    new_rewards_for_date.append({
                        'start_date': target_date_str,
                        'end_date': target_date_str,
                        'product_id': product_id,
                        'reward': spinbox.value()
                    })
            
            # 합치기
            self.all_rewards_data['rewards'] = other_days_rewards + new_rewards_for_date
            
            # 파일에 저장
            with open(self.reward_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_rewards_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "저장 완료", f"{target_date_str}의 리워드 설정이 저장되었습니다.\\n총 {len(new_rewards_for_date)}개 상품")
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"리워드 설정 저장 중 오류가 발생했습니다:\\n{str(e)}")


# Purchase Manager Dialog - Material Design version
class ModernPurchaseDialog(QDialog):
    """가구매 관리 팝업창 (하루 단위 설정) - 리워드와 동일한 방식"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('일일 가구매 관리')
        self.setFixedSize(900, 650)
        self.setModal(True)
        
        # Material Design 3 스타일링 적용
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {MaterialColors.LIGHT_SURFACE};
                border-radius: 16px;
                border: 2px solid rgba(229, 229, 229, 0.8);
            }}
            QLabel {{
                color: {MaterialColors.LIGHT_TEXT};
            }}
            QPushButton {{
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                min-width: 80px;
                background-color: {MaterialColors.PRIMARY};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
            QTableWidget {{
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #F5F5F5;
            }}
            QTableWidget::item:selected {{
                background: #E3F2FD;
                color: #1976D2;
            }}
            QGroupBox {{
                font-weight: 600;
                border: 2px solid rgba(229, 229, 229, 0.8);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }}
        """)
        
        from modules import config
        self.purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')
        self.margin_file = config.MARGIN_FILE
        
        self.all_purchases_data = {'purchases': []}
        self.products_df = pd.DataFrame()

        self.initUI()
        self.load_data_sources()
    
    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 스크롤 가능한 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(200, 200, 200, 0.3);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(150, 150, 150, 0.7);
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        # 스크롤 내용 위젯
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 헤더
        header_layout = QHBoxLayout()
        
        if QTAWESOME_AVAILABLE:
            try:
                purchase_icon = qta.icon('fa5s.shopping-cart', color=MaterialColors.WARNING)
                icon_label = QLabel()
                icon_pixmap = purchase_icon.pixmap(32, 32)
                icon_label.setPixmap(icon_pixmap)
            except Exception:
                icon_label = QLabel("🛒")
                icon_label.setStyleSheet("font-size: 24px;")
        else:
            icon_label = QLabel("🛒")
            icon_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel("상품별 가구매 개수 설정")
        title_label.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: 700; 
            color: {MaterialColors.PRIMARY};
            margin: 0;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        
        
        # 저장 버튼 섹션
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_purchases)
        self.save_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("background-color: #6c757d; color: white; padding: 8px 16px;")
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 스크롤 영역에 내용 설정
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # UI 생성 완료 후 초기 데이터 로드
        self.load_purchases_for_date(QDate.currentDate())
    
    
    # 새로운 날짜별 방식 메서드들
    def load_data_sources(self):
        """마진 정보 파일에서 상품 데이터 로드"""
        try:
            if os.path.exists(self.margin_file):
                self.products_df = pd.read_excel(self.margin_file)
                if '상품ID' in self.products_df.columns and '상품명' in self.products_df.columns:
                    # 상품ID를 문자열로 변환
                    self.products_df['상품ID'] = self.products_df['상품ID'].astype(str)
                else:
                    QMessageBox.warning(self, "데이터 오류", "마진정보.xlsx 파일에 '상품ID' 또는 '상품명' 컬럼이 없습니다.")
            else:
                QMessageBox.warning(self, "파일 없음", "마진정보.xlsx 파일을 찾을 수 없습니다.")
        except Exception as e:
            QMessageBox.critical(self, "로드 실패", f"상품 데이터 로드 실패: {str(e)}")
    
    def load_purchases_for_date(self, date):
        """특정 날짜의 가구매 설정 로드"""
        date_str = date.toString("yyyy-MM-dd")
        
        # 기존 가구매 설정 로드
        if os.path.exists(self.purchase_file):
            try:
                with open(self.purchase_file, 'r', encoding='utf-8') as f:
                    self.all_purchases_data = json.load(f)
            except:
                self.all_purchases_data = {'purchases': []}
        
        # 해당 날짜의 가구매 설정 가져오기
        purchase_map = {}
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == date_str:
                purchase_map[str(entry['product_id'])] = entry['purchase_count']
        
        # 상품 테이블에 표시
        self.populate_product_table(purchase_map)
    
    def populate_product_table(self, purchase_map):
        """상품 테이블에 데이터 표시"""
        if self.products_df.empty:
            return
        
        self.product_table.setRowCount(0)
        
        # 대표옵션인 상품들만 표시
        representative_products = self.products_df[self.products_df.get('대표옵션', 'Y') == 'Y']
        
        for index, row in representative_products.iterrows():
            try:
                product_id = str(row['상품ID'])
                product_name = str(row.get('상품명', ''))
                
                row_idx = self.product_table.rowCount()
                self.product_table.insertRow(row_idx)
                
                # 체크박스
                checkbox = QCheckBox()
                checkbox.clicked.connect(self.update_selected_count)
                self.product_table.setCellWidget(row_idx, 0, checkbox)
                
                # 상품ID
                self.product_table.setItem(row_idx, 1, QTableWidgetItem(product_id))
                
                # 상품명
                self.product_table.setItem(row_idx, 2, QTableWidgetItem(product_name))
                
                # 가구매 개수 스핀박스
                spinbox = QSpinBox()
                spinbox.setRange(0, 9999)
                spinbox.setSuffix(" 개")
                spinbox.setSingleStep(1)
                spinbox.setValue(purchase_map.get(product_id, 0))
                self.product_table.setCellWidget(row_idx, 3, spinbox)
                
            except Exception as e:
                print(f"상품 데이터 처리 오류: {e}")
                continue
        
        self.filter_products()
        self.update_selected_count()
    
    def copy_purchases(self):
        """선택한 날짜의 설정을 현재 날짜에 복사"""
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        
        purchase_map = {}
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == source_date_str:
                purchase_map[str(entry['product_id'])] = entry['purchase_count']
        
        # 현재 테이블에 적용
        for row in range(self.product_table.rowCount()):
            product_id = self.product_table.item(row, 1).text()
            spinbox = self.product_table.cellWidget(row, 3)
            if spinbox and product_id in purchase_map:
                spinbox.setValue(purchase_map[product_id])
        
        if purchase_map:
            QMessageBox.information(self, "복사 완료", f"{source_date_str}의 설정을 복사했습니다.")
        else:
            QMessageBox.information(self, "복사 완료", f"{source_date_str}에는 설정된 가구매가 없습니다.")
    
    def filter_products(self):
        """상품명으로 필터링"""
        search_text = self.search_box.text().lower()
        
        for row in range(self.product_table.rowCount()):
            product_name_item = self.product_table.item(row, 2)
            if product_name_item:
                product_name = product_name_item.text().lower()
                should_show = search_text in product_name
                self.product_table.setRowHidden(row, not should_show)
    
    def toggle_all_selection(self):
        """전체 선택/해제"""
        check_all = self.select_all_checkbox.isChecked()
        
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(check_all)
        
        self.update_selected_count()
    
    def update_selected_count(self):
        """선택된 항목 수 업데이트"""
        selected_count = 0
        total_visible = 0
        
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):
                total_visible += 1
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    selected_count += 1
        
        self.selected_count_label.setText(f"선택됨: {selected_count}개")
        
        # 전체 선택 체크박스 상태 업데이트
        if total_visible == 0:
            self.select_all_checkbox.setChecked(False)
        elif selected_count == total_visible:
            self.select_all_checkbox.setChecked(True)
        else:
            self.select_all_checkbox.setChecked(False)
    
    def apply_bulk_purchase(self):
        """일괄 가구매 개수 적용"""
        purchase_count = self.bulk_purchase.value()
        applied_count = 0
        
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    spinbox = self.product_table.cellWidget(row, 3)
                    if spinbox:
                        spinbox.setValue(purchase_count)
                        applied_count += 1
        
        if applied_count > 0:
            QMessageBox.information(self, "적용 완료", f"{applied_count}개 상품에 {purchase_count}개가 적용되었습니다.")
        else:
            QMessageBox.warning(self, "적용 실패", "선택된 상품이 없습니다.")
    
    def save_purchases(self):
        """가구매 설정 저장"""
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            
            # 기존 해당 날짜 데이터 제거
            self.all_purchases_data['purchases'] = [
                entry for entry in self.all_purchases_data.get('purchases', [])
                if entry.get('start_date') != target_date_str
            ]
            
            # 새로운 가구매 설정 추가
            for row in range(self.product_table.rowCount()):
                if not self.product_table.isRowHidden(row):
                    product_id = self.product_table.item(row, 1).text()
                    spinbox = self.product_table.cellWidget(row, 3)
                    
                    if spinbox and spinbox.value() > 0:
                        purchase_entry = {
                            'start_date': target_date_str,
                            'product_id': product_id,
                            'purchase_count': spinbox.value()
                        }
                        self.all_purchases_data['purchases'].append(purchase_entry)
            
            # 파일 저장
            with open(self.purchase_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_purchases_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "저장 완료", f"{target_date_str}의 가구매 설정이 저장되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"가구매 설정 저장 중 오류: {str(e)}")


# Main Application Window
class ModernSalesAutomationApp(QMainWindow):
    """Material Design 3 판매 데이터 자동화 메인 애플리케이션"""
    
    def __init__(self):
        super().__init__()
        
        # 테마 매니저는 나중에 초기화
        self.theme_manager = None
        
        # 애플리케이션 상태
        self.download_folder_path = ""
        self.password = "1234"
        self.worker = None
        self.manual_worker = None
        
        # 통계 데이터
        self.stats = {
            'files_processed': 0,
            'total_sales': 0,
            'total_margin': 0,
            'error_count': 0
        }
        
        self.init_ui()
        self.setup_logging()
        
    def init_ui(self):
        """메인 UI 초기화"""
        self.setWindowTitle("판매 데이터 자동화 - Material Design 3")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 스크롤 가능한 메인 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(80, 80, 80, 0.3);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(150, 150, 150, 0.7);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(180, 180, 180, 0.8);
            }
        """)
        
        # 스크롤 가능한 위젯
        scroll_widget = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_widget)
        scroll_content_layout.setContentsMargins(15, 15, 15, 15)  # 여백 축소
        scroll_content_layout.setSpacing(15)  # 간격 축소
        
        # 헤더 섹션 (축소된 크기)
        header_layout = self.create_header()
        scroll_content_layout.addLayout(header_layout)
        
        # 설정 섹션 (컴팩트하게)
        settings_card = self.create_settings_section()
        scroll_content_layout.addWidget(settings_card)
        
        # 통계 섹션 (높이 제한)
        self.stats_widget = self.create_stats_section()
        scroll_content_layout.addWidget(self.stats_widget)
        
        # 로그 섹션 (높이 제한)
        log_section = self.create_log_section()
        scroll_content_layout.addWidget(log_section)
        
        # 스크롤 영역에 위젯 설정
        scroll_area.setWidget(scroll_widget)
        
        # 메인 레이아웃에 스크롤 영역 추가
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        main_layout.addWidget(scroll_area)
        
        # 상태바
        self.statusBar().showMessage("Material Design 3 적용 완료 - 준비됨")
    
    def create_header(self):
        """헤더 섹션 생성"""
        header_layout = QHBoxLayout()
        
        # 앱 제목 (컴팩트하게)
        if QTAWESOME_AVAILABLE:
            try:
                app_icon = qta.icon('fa5s.chart-bar', color=MaterialColors.PRIMARY)
                icon_label = QLabel()
                icon_pixmap = app_icon.pixmap(32, 32)  # 아이콘 크기 축소
                icon_label.setPixmap(icon_pixmap)
            except Exception:
                icon_label = QLabel("📊")
                icon_label.setStyleSheet("font-size: 24px;")  # 폰트 크기 축소
        else:
            icon_label = QLabel("📊")
            icon_label.setStyleSheet("font-size: 24px;")  # 폰트 크기 축소
        
        title_label = QLabel("판매 데이터 자동화")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: #ffffff;
            margin-left: 8px;
        """)
        
        subtitle_label = QLabel("Material Design 3 • 스마트 데이터 처리")
        subtitle_label.setStyleSheet(f"""
            font-size: 13px;
            color: {MaterialColors.WARNING};
            margin-left: 8px;
        """)
        
        header_left = QVBoxLayout()
        header_left.setSpacing(4)
        
        title_row = QHBoxLayout()
        title_row.addWidget(icon_label)
        title_row.addWidget(title_label)
        title_row.addStretch()
        
        header_left.addLayout(title_row)
        header_left.addWidget(subtitle_label)
        
        # 테마 전환 버튼
        theme_btn = AppleStyleButton("🌙 다크모드", "fa5s.moon" if QTAWESOME_AVAILABLE else None, "#6366f1")
        theme_btn.clicked.connect(self.toggle_theme)
        
        header_layout.addLayout(header_left)
        header_layout.addStretch()
        header_layout.addWidget(theme_btn)
        
        return header_layout
    
    def create_settings_section(self):
        """설정 섹션 생성"""
        settings_card = QFrame()
        settings_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(48, 48, 48, 0.95);
                border: 1px solid rgba(80, 80, 80, 0.8);
                border-radius: 12px;
                padding: 16px;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QLineEdit {{
                background-color: rgba(64, 64, 64, 0.8);
                border: 1px solid rgba(100, 100, 100, 0.6);
                border-radius: 6px;
                padding: 6px;
                color: #ffffff;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {MaterialColors.PRIMARY};
                background-color: rgba(64, 64, 64, 1.0);
            }}
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        settings_card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(settings_card)
        layout.setSpacing(12)  # 간격 축소
        
        # 제목
        settings_title = QLabel("⚙️ 설정")
        settings_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 8px;
        """)
        layout.addWidget(settings_title)
        
        # 설정 입력들
        form_layout = QGridLayout()
        
        # 다운로드 폴더 선택
        form_layout.addWidget(QLabel("다운로드 폴더:"), 0, 0)
        
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("폴더를 선택해주세요...")
        self.folder_label.setStyleSheet("color: #999; font-style: italic; font-size: 13px;")
        
        folder_btn = AppleStyleButton("폴더 선택", "fa5s.folder-open" if QTAWESOME_AVAILABLE else None, MaterialColors.PRIMARY)
        folder_btn.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(folder_btn)
        form_layout.addLayout(folder_layout, 0, 1)
        
        # 암호 입력
        form_layout.addWidget(QLabel("주문조회 파일 암호:"), 1, 0)
        self.password_input = QLineEdit("1234")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.update_password)
        form_layout.addWidget(self.password_input, 1, 1)
        
        layout.addLayout(form_layout)
        
        # 제어 버튼들 (2줄 배치로 공간 절약) - 공식 문서에 따른 올바른 설정
        buttons_container = QVBoxLayout()
        buttons_container.setSpacing(8)  # 수직 간격 축소
        buttons_container.setContentsMargins(5, 8, 5, 8)  # 전체 여백 축소
        
        # 첫 번째 줄: 주요 동작 버튼들 - 공식 문서에 따른 올바른 설정
        main_control_layout = QHBoxLayout()
        main_control_layout.setSpacing(15)  # 공식 문서 권장 최소 간격
        main_control_layout.setContentsMargins(5, 5, 5, 5)  # 여백 추가
        
        self.start_btn = AppleStyleButton("자동화 시작", "fa5s.play" if QTAWESOME_AVAILABLE else None, MaterialColors.SUCCESS)
        self.start_btn.clicked.connect(self.start_monitoring)
        
        self.stop_btn = AppleStyleButton("중지", "fa5s.stop" if QTAWESOME_AVAILABLE else None, MaterialColors.ERROR)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        
        self.manual_btn = AppleStyleButton("작업폴더 처리", "fa5s.cog" if QTAWESOME_AVAILABLE else None, MaterialColors.WARNING)
        self.manual_btn.clicked.connect(self.manual_process)
        
        main_control_layout.addWidget(self.start_btn)
        main_control_layout.addWidget(self.stop_btn)
        main_control_layout.addWidget(self.manual_btn)
        main_control_layout.addStretch()
        
        # 두 번째 줄: 설정 관리 버튼들 - 공식 문서에 따른 올바른 설정
        settings_control_layout = QHBoxLayout()
        settings_control_layout.setSpacing(15)  # 공식 문서 권장 최소 간격
        settings_control_layout.setContentsMargins(5, 5, 5, 5)  # 여백 추가
        
        self.reward_btn = AppleStyleButton("리워드 관리", "fa5s.gift" if QTAWESOME_AVAILABLE else None, "#8b5cf6")
        self.reward_btn.clicked.connect(self.show_reward_dialog)
        
        self.purchase_btn = AppleStyleButton("가구매 관리", "fa5s.shopping-cart" if QTAWESOME_AVAILABLE else None, "#f59e0b")
        self.purchase_btn.clicked.connect(self.show_purchase_dialog)
        
        settings_control_layout.addWidget(self.reward_btn)
        settings_control_layout.addWidget(self.purchase_btn)
        settings_control_layout.addStretch()
        
        buttons_container.addLayout(main_control_layout)
        buttons_container.addLayout(settings_control_layout)
        
        layout.addLayout(buttons_container)
        
        return settings_card
    
    def create_stats_section(self):
        """통계 섹션 생성"""
        stats_card = QFrame()
        stats_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(48, 48, 48, 0.95);
                border: 1px solid rgba(80, 80, 80, 0.8);
                border-radius: 12px;
                padding: 16px;
            }}
            QLabel {{
                color: #ffffff;
            }}
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        stats_card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(stats_card)
        layout.setSpacing(12)
        
        # 제목
        stats_title = QLabel("📈 실시간 통계")
        stats_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 8px;
        """)
        layout.addWidget(stats_title)
        
        # KPI 카드들
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(16)
        
        self.files_card = ModernDataCard(
            "처리된 파일", "0개", "fa5s.file-alt", MaterialColors.SUCCESS, "처리 완료된 파일 수"
        )
        self.sales_card = ModernDataCard(
            "총 매출", "₩0", "fa5s.dollar-sign", MaterialColors.PRIMARY, "총 매출액"
        )
        self.margin_card = ModernDataCard(
            "순이익", "₩0", "fa5s.chart-line", MaterialColors.WARNING, "총 순이익"
        )
        self.error_card = ModernDataCard(
            "에러", "0개", "fa5s.exclamation-triangle", MaterialColors.ERROR, "발생한 에러 수"
        )
        
        kpi_layout.addWidget(self.files_card, 0, 0)
        kpi_layout.addWidget(self.sales_card, 0, 1)
        kpi_layout.addWidget(self.margin_card, 0, 2)
        kpi_layout.addWidget(self.error_card, 0, 3)
        
        layout.addLayout(kpi_layout)
        
        return stats_card
    
    def create_log_section(self):
        """로그 섹션 생성"""
        log_card = QFrame()
        log_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(48, 48, 48, 0.95);
                border: 1px solid rgba(80, 80, 80, 0.8);
                border-radius: 12px;
                padding: 16px;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QTextEdit {{
                background-color: rgba(32, 32, 32, 0.9);
                border: 1px solid rgba(80, 80, 80, 0.6);
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.3;
                max-height: 200px;
            }}
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        log_card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(log_card)
        layout.setSpacing(10)
        
        # 제목
        log_title = QLabel("📋 처리 로그")
        log_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 8px;
        """)
        layout.addWidget(log_title)
        
        # 로그 뷰어
        self.log_output = ModernLogViewer()
        self.log_output.append("[INFO] Material Design 3 애플리케이션이 준비되었습니다!")
        self.log_output.append("[INFO] 다운로드 폴더를 선택하고 '자동화 시작'을 클릭하세요.")
        
        layout.addWidget(self.log_output)
        
        # 로그 제어 버튼들
        log_controls = QHBoxLayout()
        
        clear_btn = AppleStyleButton("🗑️ 로그 지우기", "fa5s.trash" if QTAWESOME_AVAILABLE else None, MaterialColors.ERROR)
        clear_btn.clicked.connect(self.clear_log)
        
        save_btn = AppleStyleButton("💾 로그 저장", "fa5s.save" if QTAWESOME_AVAILABLE else None, MaterialColors.PRIMARY)
        save_btn.clicked.connect(self.save_log)
        
        log_controls.addWidget(clear_btn)
        log_controls.addWidget(save_btn)
        log_controls.addStretch()
        
        layout.addLayout(log_controls)
        
        return log_card
    
    def setup_logging(self):
        """로깅 시스템 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sales_automation.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def select_folder(self):
        """다운로드 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(self, "다운로드 폴더 선택")
        if folder:
            self.download_folder_path = folder
            self.folder_label.setText(f"📁 {folder}")
            self.folder_label.setStyleSheet("color: #333; font-weight: 500;")
            self.update_log(f"[INFO] 다운로드 폴더 설정: {folder}")
    
    def update_password(self):
        """암호 업데이트"""
        self.password = self.password_input.text()
    
    def toggle_theme(self):
        """테마 전환"""
        if self.theme_manager is None:
            self.update_log("[WARNING] 테마 매니저가 초기화되지 않았습니다.")
            return
            
        is_dark = self.theme_manager.toggle_theme()
        theme_text = "☀️ 라이트모드" if is_dark else "🌙 다크모드"
        
        # 테마 버튼 텍스트 업데이트를 위해 버튼 찾기
        for child in self.findChildren(AppleStyleButton):
            if "모드" in child.text():
                child.setText(theme_text)
                break
        
        self.update_log(f"[INFO] 테마 변경: {'다크모드' if is_dark else '라이트모드'}")
    
    def start_monitoring(self):
        """파일 모니터링 시작"""
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return
        
        try:
            self.worker = ModernWorker(self.download_folder_path, self.password)
            self.worker.output_signal.connect(self.update_log)
            self.worker.finished_signal.connect(self.on_monitoring_finished)
            self.worker.error_signal.connect(self.on_error)
            
            self.worker.start()
            
            # UI 상태 변경
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.manual_btn.setEnabled(False)
            
            self.statusBar().showMessage("🔄 자동화 실행 중...")
            self.update_log("[INFO] 파일 모니터링을 시작했습니다!")
            
        except Exception as e:
            QMessageBox.critical(self, "시작 오류", f"모니터링 시작 중 오류가 발생했습니다:\n{str(e)}")
            self.update_log(f"[ERROR] 시작 오류: {str(e)}")
    
    def stop_monitoring(self):
        """파일 모니터링 중지"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(3000)  # 3초 대기
        
        self.on_monitoring_finished()
    
    def manual_process(self):
        """수동 작업폴더 처리"""
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return
        
        try:
            self.manual_worker = ModernManualWorker(self.download_folder_path, self.password)
            self.manual_worker.output_signal.connect(self.update_log)
            self.manual_worker.finished_signal.connect(self.on_manual_finished)
            
            self.manual_worker.start()
            
            # UI 상태 변경
            self.manual_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            
            self.statusBar().showMessage("🔄 수동 처리 실행 중...")
            
        except Exception as e:
            QMessageBox.critical(self, "처리 오류", f"수동 처리 중 오류가 발생했습니다:\n{str(e)}")
            self.update_log(f"[ERROR] 수동 처리 오류: {str(e)}")
    
    def show_reward_dialog(self):
        """리워드 관리 다이얼로그 표시"""
        dialog = ModernRewardDialog(self)
        dialog.exec()
    
    def show_purchase_dialog(self):
        """가구매 관리 다이얼로그 표시"""
        dialog = ModernPurchaseDialog(self)
        dialog.exec()
    
    def on_monitoring_finished(self):
        """모니터링 완료 처리"""
        # UI 상태 복원
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.manual_btn.setEnabled(True)
        
        self.statusBar().showMessage("✅ 준비됨")
        self.update_log("[INFO] ⏹️ 모니터링이 중지되었습니다.")
    
    def on_manual_finished(self):
        """수동 처리 완료"""
        # UI 상태 복원
        self.manual_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        
        self.statusBar().showMessage("✅ 준비됨")
    
    def on_error(self, error_msg):
        """에러 처리"""
        self.stats['error_count'] += 1
        self.error_card.update_value(f"{self.stats['error_count']}개")
    
    def update_log(self, message):
        """로그 업데이트"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_output.append(formatted_message)
        
        # 자동 스크롤
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)
    
    def clear_log(self):
        """로그 지우기"""
        reply = QMessageBox.question(self, "로그 지우기", "모든 로그를 지우시겠습니까?")
        if reply == QMessageBox.Yes:
            self.log_output.clear()
            self.update_log("[INFO] 로그가 지워졌습니다.")
    
    def save_log(self):
        """로그 저장"""
        try:
            filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath, _ = QFileDialog.getSaveFileName(
                self, "로그 저장", filename, "Text files (*.txt);;All files (*.*)"
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.log_output.toPlainText())
                
                self.update_log(f"[INFO] 로그가 저장되었습니다: {filepath}")
                QMessageBox.information(self, "저장 완료", "로그가 성공적으로 저장되었습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"로그 저장 중 오류가 발생했습니다:\n{str(e)}")


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("판매 데이터 자동화")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("Material Design Team")
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sales_automation.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 메인 윈도우 생성
    window = ModernSalesAutomationApp()
    
    # 테마 매니저 초기화 (QApplication 생성 후)
    window.theme_manager = ThemeManager(app)
    
    # 테마 적용
    try:
        window.theme_manager.setup_auto_theme()
        logging.info("Material Design 3 테마 적용 완료")
    except Exception as e:
        logging.error(f"테마 적용 실패: {e}")
    
    # 윈도우 표시
    window.show()
    
    logging.info("Material Design 3 판매 데이터 자동화 애플리케이션 시작")
    
    # 이벤트 루프 시작
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())