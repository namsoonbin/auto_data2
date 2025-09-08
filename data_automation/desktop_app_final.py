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
    QGraphicsDropShadowEffect, QDialogButtonBox
)
from PySide6.QtCore import QThread, Signal, Qt, QDate, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter
import re

# New improved imports - qt-material + qtawesome
from qt_material import apply_stylesheet
import qtawesome as qta
import pyqtdarktheme

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
            # pyqtdarktheme로 시스템 테마 감지
            pyqtdarktheme.setup_theme("auto")
            # qt-material 테마 추가 적용
            theme_name = "dark_teal.xml" if self.is_dark_mode else "light_blue.xml"
            apply_stylesheet(self.app, theme=theme_name)
        except Exception as e:
            logging.warning(f"자동 테마 설정 실패: {e}")
            self.apply_default_theme()
    
    def apply_default_theme(self):
        """기본 다크 테마 적용"""
        try:
            apply_stylesheet(self.app, theme='dark_teal.xml')
            self.is_dark_mode = True
        except Exception as e:
            logging.error(f"기본 테마 적용 실패: {e}")
    
    def toggle_theme(self):
        """수동 테마 전환"""
        try:
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
    def __init__(self, title, value, icon_name, color=MaterialColors.PRIMARY, tooltip=""):
        super().__init__()
        self.setFixedHeight(120)
        if tooltip:
            self.setToolTip(tooltip)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(229, 229, 229, 0.8);
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {color};
                background-color: rgba(248, 249, 250, 0.95);
                transform: translateY(-2px);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 헤더: 아이콘 + 제목
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # QtAwesome 아이콘
        try:
            icon = qta.icon(icon_name, color=color)
            icon_label = QLabel()
            icon_pixmap = icon.pixmap(24, 24)
            icon_label.setPixmap(icon_pixmap)
        except:
            # 아이콘 로드 실패 시 기본 이모지
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
    
    def update_value(self, new_value):
        """카드 값 업데이트"""
        self.value_label.setText(str(new_value))


# Apple Style Button
class AppleStyleButton(QPushButton):
    """Apple 스타일 버튼"""
    def __init__(self, text, icon_name=None, color=MaterialColors.PRIMARY, parent=None):
        super().__init__(text, parent)
        
        if icon_name:
            try:
                icon = qta.icon(icon_name, color='white')
                self.setIcon(icon)
            except:
                pass  # 아이콘 로드 실패 시 텍스트만 표시
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.2)};
                transform: translateY(0px);
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
            
            self.output_signal.emit("[INFO] 🚀 Material Design 3 자동화 시작!")
            self.output_signal.emit(f"[INFO] 📁 감시 폴더: {self.download_folder}")
            
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
        self.output_signal.emit("[INFO] ⏹️ 자동화 중지 요청...")


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
            
            self.output_signal.emit("[INFO] 🔄 작업폴더 수동 처리 시작...")
            
            # 기존 파일 처리
            file_handler.process_existing_files()
            
            self.output_signal.emit("[INFO] ✅ 작업폴더 처리 완료!")
            
        except Exception as e:
            error_msg = f"[ERROR] 수동 처리 중 오류: {str(e)}"
            self.output_signal.emit(error_msg)
        finally:
            self.finished_signal.emit()

# Weekly Report Worker
class WeeklyWorker(QThread):
    """주간 리포트 생성을 위한 워커 스레드"""
    output_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, start_date, end_date, download_folder):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.download_folder = download_folder

    def run(self):
        """주간 리포트 생성 실행"""
        try:
            self.output_signal.emit(f"[INFO] 📅 주간 리포트 생성 시작 ({self.start_date} ~ {self.end_date})...")
            config.DOWNLOAD_DIR = self.download_folder
            report_generator.create_weekly_report(self.start_date, self.end_date)
            self.output_signal.emit("[INFO] ✅ 주간 리포트 생성 완료!")
        except Exception as e:
            error_msg = f"[ERROR] 주간 리포트 생성 중 오류: {str(e)}"
            self.output_signal.emit(error_msg)
        finally:
            self.finished_signal.emit()

# Reward Manager Dialog - Material Design version
class ModernRewardDialog(QDialog):
    """Material Design 리워드 관리 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💰 리워드 관리")
        self.setMinimumSize(800, 600)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {MaterialColors.LIGHT_SURFACE};
                border-radius: 16px;
            }}
        """)
        
        self.init_ui()
        self.load_rewards()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 헤더
        header_layout = QHBoxLayout()
        
        try:
            reward_icon = qta.icon('fa5s.gift', color=MaterialColors.WARNING)
            icon_label = QLabel()
            icon_pixmap = reward_icon.pixmap(32, 32)
            icon_label.setPixmap(icon_pixmap)
        except:
            icon_label = QLabel("💰")
            icon_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel("상품별 리워드 설정")
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
        
        # 입력 섹션
        input_card = QFrame()
        input_card.setStyleSheet(f"""
            QFrame {{
                background-color: {MaterialColors.LIGHT_SURFACE};
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        input_layout = QGridLayout(input_card)
        
        # 입력 필드들
        input_layout.addWidget(QLabel("시작 날짜:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        input_layout.addWidget(self.start_date, 0, 1)
        
        input_layout.addWidget(QLabel("종료 날짜:"), 0, 2)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(30))
        self.end_date.setCalendarPopup(True)
        input_layout.addWidget(self.end_date, 0, 3)
        
        input_layout.addWidget(QLabel("상품 ID:"), 1, 0)
        self.product_id = QLineEdit()
        self.product_id.setPlaceholderText("상품 ID를 입력하세요")
        input_layout.addWidget(self.product_id, 1, 1)
        
        input_layout.addWidget(QLabel("리워드 금액:"), 1, 2)
        self.reward_amount = QSpinBox()
        self.reward_amount.setRange(0, 999999)
        self.reward_amount.setSuffix("원")
        input_layout.addWidget(self.reward_amount, 1, 3)
        
        layout.addWidget(input_card)
        
        # 빠른 설정 버튼들
        quick_layout = QHBoxLayout()
        quick_buttons = [
            ("0원", 0, MaterialColors.SUCCESS),
            ("3,000원", 3000, MaterialColors.PRIMARY),
            ("6,000원", 6000, MaterialColors.WARNING),
            ("9,000원", 9000, MaterialColors.ERROR)
        ]
        
        for text, value, color in quick_buttons:
            btn = AppleStyleButton(text, color=color)
            btn.clicked.connect(lambda checked, v=value: self.reward_amount.setValue(v))
            quick_layout.addWidget(btn)
        
        layout.addLayout(quick_layout)
        
        # 리워드 테이블
        self.reward_table = QTableWidget()
        self.reward_table.setColumnCount(5)
        self.reward_table.setHorizontalHeaderLabels(['시작일', '종료일', '상품ID', '리워드', '액션'])
        self.reward_table.setStyleSheet("""
            QTableWidget {
                background-color: #fafafa;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                selection-background-color: #e3f2fd;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: #424242;
            }
        """)
        
        # 컬럼 크기 조정
        header = self.reward_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.reward_table)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        add_btn = AppleStyleButton("추가", "fa5s.plus", MaterialColors.SUCCESS)
        add_btn.clicked.connect(self.add_reward)
        button_layout.addWidget(add_btn)
        
        save_btn = AppleStyleButton("저장", "fa5s.save", MaterialColors.PRIMARY)
        save_btn.clicked.connect(self.save_rewards)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        close_btn = AppleStyleButton("닫기", "fa5s.times", MaterialColors.ERROR)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def add_reward(self):
        """리워드 추가"""
        try:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            product_id = self.product_id.text().strip()
            reward = self.reward_amount.value()
            
            if not product_id:
                QMessageBox.warning(self, "입력 오류", "상품 ID를 입력해주세요.")
                return
            
            # 테이블에 추가
            row = self.reward_table.rowCount()
            self.reward_table.insertRow(row)
            
            self.reward_table.setItem(row, 0, QTableWidgetItem(start_date))
            self.reward_table.setItem(row, 1, QTableWidgetItem(end_date))
            self.reward_table.setItem(row, 2, QTableWidgetItem(product_id))
            self.reward_table.setItem(row, 3, QTableWidgetItem(f"{reward:,}원"))
            
            # 삭제 버튼
            delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
            delete_btn.clicked.connect(lambda: self.delete_reward(row))
            self.reward_table.setCellWidget(row, 4, delete_btn)
            
            # 입력 필드 초기화
            self.product_id.clear()
            self.reward_amount.setValue(0)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"리워드 추가 중 오류가 발생했습니다: {str(e)}")
    
    def delete_reward(self, row):
        """리워드 삭제"""
        reply = QMessageBox.question(self, "삭제 확인", "선택한 리워드를 삭제하시겠습니까?")
        if reply == QMessageBox.Yes:
            self.reward_table.removeRow(row)
            # 버튼들의 인덱스 재조정 필요
            self.refresh_table_buttons()
    
    def refresh_table_buttons(self):
        """테이블 버튼들 인덱스 재조정"""
        for row in range(self.reward_table.rowCount()):
            delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_reward(r))
            self.reward_table.setCellWidget(row, 4, delete_btn)
    
    def load_rewards(self):
        """기존 리워드 설정 로드"""
        try:
            reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
            if os.path.exists(reward_file):
                with open(reward_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                rewards = data.get('rewards', [])
                for reward in rewards:
                    row = self.reward_table.rowCount()
                    self.reward_table.insertRow(row)
                    
                    self.reward_table.setItem(row, 0, QTableWidgetItem(reward['start_date']))
                    self.reward_table.setItem(row, 1, QTableWidgetItem(reward['end_date']))
                    self.reward_table.setItem(row, 2, QTableWidgetItem(reward['product_id']))
                    self.reward_table.setItem(row, 3, QTableWidgetItem(f"{reward['reward']:,}원"))
                    
                    delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
                    delete_btn.clicked.connect(lambda checked, r=row: self.delete_reward(r))
                    self.reward_table.setCellWidget(row, 4, delete_btn)
                    
        except Exception as e:
            logging.warning(f"리워드 설정 로드 실패: {e}")
    
    def save_rewards(self):
        """리워드 설정 저장"""
        try:
            rewards = []
            
            for row in range(self.reward_table.rowCount()):
                reward_data = {
                    'start_date': self.reward_table.item(row, 0).text(),
                    'end_date': self.reward_table.item(row, 1).text(),
                    'product_id': self.reward_table.item(row, 2).text(),
                    'reward': int(self.reward_table.item(row, 3).text().replace(',', '').replace('원', ''))
                }
                rewards.append(reward_data)
            
            data = {'rewards': rewards}
            
            reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
            with open(reward_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "저장 완료", "리워드 설정이 성공적으로 저장되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"리워드 설정 저장 중 오류가 발생했습니다: {str(e)}")

# Weekly Report Dialog
class WeeklyReportDialog(QDialog):
    """주간 리포트 생성을 위한 날짜 선택 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 주간 리포트 생성")
        
        layout = QVBoxLayout(self)
        
        form_layout = QGridLayout()
        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        
        form_layout.addWidget(QLabel("시작 날짜:"), 0, 0)
        form_layout.addWidget(self.start_date_edit, 0, 1)
        form_layout.addWidget(QLabel("종료 날짜:"), 1, 0)
        form_layout.addWidget(self.end_date_edit, 1, 1)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

    def get_dates(self):
        """선택된 날짜를 문자열로 반환"""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

# Main Application Window
class ModernSalesAutomationApp(QMainWindow):
    """Material Design 3 판매 데이터 자동화 메인 애플리케이션"""
    
    def __init__(self):
        super().__init__()
        
        # 테마 매니저 초기화
        self.theme_manager = ThemeManager(QApplication.instance())
        
        # 애플리케이션 상태
        self.download_folder_path = ""
        self.password = "1234"
        self.worker = None
        self.manual_worker = None
        self.weekly_worker = None
        
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
        self.setWindowTitle("📊 판매 데이터 자동화 - Material Design 3")
        self.setMinimumSize(1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 헤더 섹션
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # 설정 섹션
        settings_card = self.create_settings_section()
        main_layout.addWidget(settings_card)
        
        # 통계 섹션
        self.stats_widget = self.create_stats_section()
        main_layout.addWidget(self.stats_widget)
        
        # 로그 섹션
        log_section = self.create_log_section()
        main_layout.addWidget(log_section)
        
        # 상태바
        self.statusBar().showMessage("🎨 Material Design 3 적용 완료 - 준비됨")
    
    def create_header(self):
        """헤더 섹션 생성"""
        header_layout = QHBoxLayout()
        
        # 앱 제목
        try:
            app_icon = qta.icon('fa5s.chart-bar', color=MaterialColors.PRIMARY)
            icon_label = QLabel()
            icon_pixmap = app_icon.pixmap(48, 48)
            icon_label.setPixmap(icon_pixmap)
        except:
            icon_label = QLabel("📊")
            icon_label.setStyleSheet("font-size: 36px;")
        
        title_label = QLabel("판매 데이터 자동화")
        title_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {MaterialColors.PRIMARY};
            margin-left: 12px;
        """)
        
        subtitle_label = QLabel("Material Design 3 • 스마트 데이터 처리")
        subtitle_label.setStyleSheet(f"""
            font-size: 16px;
            color: {MaterialColors.WARNING};
            margin-left: 12px;
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
        theme_btn = AppleStyleButton("🌙 다크모드", "fa5s.moon", "#6366f1")
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
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(229, 229, 229, 0.8);
                border-radius: 16px;
                padding: 24px;
            }}
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        settings_card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(settings_card)
        layout.setSpacing(20)
        
        # 제목
        settings_title = QLabel("⚙️ 설정")
        settings_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {MaterialColors.PRIMARY};
            margin-bottom: 10px;
        """)
        layout.addWidget(settings_title)
        
        # 설정 입력들
        form_layout = QGridLayout()
        
        # 다운로드 폴더 선택
        form_layout.addWidget(QLabel("다운로드 폴더:"), 0, 0)
        
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("폴더를 선택해주세요...")
        self.folder_label.setStyleSheet("color: #666; font-style: italic;")
        
        folder_btn = AppleStyleButton("📁 폴더 선택", "fa5s.folder-open", MaterialColors.PRIMARY)
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
        
        # 제어 버튼들
        control_layout = QHBoxLayout()
        
        self.start_btn = AppleStyleButton("🚀 자동화 시작", "fa5s.play", MaterialColors.SUCCESS)
        self.start_btn.clicked.connect(self.start_monitoring)
        
        self.stop_btn = AppleStyleButton("⏹️ 중지", "fa5s.stop", MaterialColors.ERROR)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        
        self.manual_btn = AppleStyleButton("🔄 작업폴더 처리", "fa5s.cog", MaterialColors.WARNING)
        self.manual_btn.clicked.connect(self.manual_process)
        
        self.reward_btn = AppleStyleButton("💰 리워드 관리", "fa5s.gift", "#8b5cf6")
        self.reward_btn.clicked.connect(self.show_reward_dialog)

        self.weekly_report_btn = AppleStyleButton("📅 주간 리포트", "fa5s.calendar-week", "#10b981")
        self.weekly_report_btn.clicked.connect(self.show_weekly_report_dialog)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.manual_btn)
        control_layout.addWidget(self.reward_btn)
        control_layout.addWidget(self.weekly_report_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        return settings_card
    
    def create_stats_section(self):
        """통계 섹션 생성"""
        stats_card = QFrame()
        stats_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(229, 229, 229, 0.8);
                border-radius: 16px;
                padding: 24px;
            }}
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        stats_card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(stats_card)
        layout.setSpacing(20)
        
        # 제목
        stats_title = QLabel("📈 실시간 통계")
        stats_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {MaterialColors.PRIMARY};
            margin-bottom: 10px;
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
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(229, 229, 229, 0.8);
                border-radius: 16px;
                padding: 24px;
            }}
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        log_card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(log_card)
        layout.setSpacing(15)
        
        # 제목
        log_title = QLabel("📋 처리 로그")
        log_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {MaterialColors.PRIMARY};
            margin-bottom: 10px;
        """)
        layout.addWidget(log_title)
        
        # 로그 뷰어
        self.log_output = ModernLogViewer()
        self.log_output.append("[INFO] 🎨 Material Design 3 애플리케이션이 준비되었습니다!")
        self.log_output.append("[INFO] 💡 다운로드 폴더를 선택하고 '자동화 시작'을 클릭하세요.")
        
        layout.addWidget(self.log_output)
        
        # 로그 제어 버튼들
        log_controls = QHBoxLayout()
        
        clear_btn = AppleStyleButton("🗑️ 로그 지우기", "fa5s.trash", MaterialColors.ERROR)
        clear_btn.clicked.connect(self.clear_log)
        
        save_btn = AppleStyleButton("💾 로그 저장", "fa5s.save", MaterialColors.PRIMARY)
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
            self.weekly_report_btn.setEnabled(False)
            
            self.statusBar().showMessage("🔄 자동화 실행 중...")
            self.update_log("[INFO] 🚀 파일 모니터링을 시작했습니다!")
            
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
            self.weekly_report_btn.setEnabled(False)
            
            self.statusBar().showMessage("🔄 수동 처리 실행 중...")
            
        except Exception as e:
            QMessageBox.critical(self, "처리 오류", f"수동 처리 중 오류가 발생했습니다:\n{str(e)}")
            self.update_log(f"[ERROR] 수동 처리 오류: {str(e)}")
    
    def show_reward_dialog(self):
        """리워드 관리 다이얼로그 표시"""
        dialog = ModernRewardDialog(self)
        dialog.exec()

    def show_weekly_report_dialog(self):
        """주간 리포트 생성 다이얼로그 표시"""
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return

        dialog = WeeklyReportDialog(self)
        if dialog.exec():
            start_date, end_date = dialog.get_dates()
            self.run_weekly_report_creation(start_date, end_date)

    def run_weekly_report_creation(self, start_date, end_date):
        """주간 리포트 생성 워커 실행"""
        try:
            self.weekly_worker = WeeklyWorker(start_date, end_date, self.download_folder_path)
            self.weekly_worker.output_signal.connect(self.update_log)
            self.weekly_worker.finished_signal.connect(self.on_weekly_report_finished)
            
            self.weekly_worker.start()

            # UI 상태 변경
            self.weekly_report_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.manual_btn.setEnabled(False)

            self.statusBar().showMessage("📅 주간 리포트 생성 중...")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"주간 리포트 생성 중 오류가 발생했습니다:\n{str(e)}")
            self.update_log(f"[ERROR] 주간 리포트 생성 오류: {str(e)}")

    def on_monitoring_finished(self):
        """모니터링 완료 처리"""
        # UI 상태 복원
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.manual_btn.setEnabled(True)
        self.weekly_report_btn.setEnabled(True)
        
        self.statusBar().showMessage("✅ 준비됨")
        self.update_log("[INFO] ⏹️ 모니터링이 중지되었습니다.")
    
    def on_manual_finished(self):
        """수동 처리 완료"""
        # UI 상태 복원
        self.manual_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.weekly_report_btn.setEnabled(True)
        
        self.statusBar().showMessage("✅ 준비됨")

    def on_weekly_report_finished(self):
        """주간 리포트 생성 완료 처리"""
        # UI 상태 복원
        self.weekly_report_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.manual_btn.setEnabled(True)
        
        self.statusBar().showMessage("✅ 준비됨")
        self.update_log("[INFO] ✅ 주간 리포트 생성이 완료되었습니다.")
    
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
        cursor.movePosition(cursor.End)
        self.log_output.setTextCursor(cursor)
    
    def clear_log(self):
        """로그 지우기"""
        reply = QMessageBox.question(self, "로그 지우기", "모든 로그를 지우시겠습니까?")
        if reply == QMessageBox.Yes:
            self.log_output.clear()
            self.update_log("[INFO] 🗑️ 로그가 지워졌습니다.")
    
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
                
                self.update_log(f"[INFO] 💾 로그가 저장되었습니다: {filepath}")
                QMessageBox.information(self, "저장 완료", "로그가 성공적으로 저장되었습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"로그 저장 중 오류가 발생했습니다:\n{str(e)}")


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("판매 데이터 자동화")
    app.setApplicationVersion("3.1.0") # Version updated
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
    
    # 테마 적용
    try:
        window.theme_manager.setup_auto_theme()
        logging.info("🎨 Material Design 3 테마 적용 완료")
    except Exception as e:
        logging.error(f"테마 적용 실패: {e}")
    
    # 윈도우 표시
    window.show()
    
    logging.info("🚀 Material Design 3 판매 데이터 자동화 애플리케이션 시작")
    
    # 이벤트 루프 시작
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
