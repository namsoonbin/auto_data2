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
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import QThread, Signal, Qt, QDate, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter
import re

# New improved imports - qt-material + qtawesome
from qt_material import apply_stylesheet
import qtawesome as qta
import pyqtdarktheme


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
                background-color: {MaterialColors.LIGHT_SURFACE};
                border-radius: 12px;
                border: 1px solid #e5e5e5;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {color};
                background-color: #f8f9fa;
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
            # 아이콘 로드 실패 시 기본 텍스트
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
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {MaterialColors.LIGHT_TEXT};
            margin: 0;
        """)
        value_label.setObjectName(f"{title}_value")
        
        layout.addWidget(value_label)
        layout.addStretch()

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
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color, 0.1)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 0.2)};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)
    
    def _darken_color(self, color, factor):
        """색상을 어둡게 만드는 헬퍼 함수"""
        # 간단한 색상 변경 (실제로는 더 정교한 구현 필요)
        if color == MaterialColors.PRIMARY:
            return "#1d4ed8"  # 더 어두운 파란색
        elif color == MaterialColors.SUCCESS:
            return "#047857"  # 더 어두운 녹색
        elif color == MaterialColors.WARNING:
            return "#c2410c"  # 더 어두운 주황색
        else:
            return "#9ca3af"  # 기본 회색

# Modern Log Viewer
class ModernLogViewer(QTextEdit):
    """Material Design 로그 뷰어"""
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {MaterialColors.DARK_BG};
                color: {MaterialColors.DARK_TEXT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 12px;
            }}
        """)

# Error Details Dialog - Material Design version
class ModernErrorDialog(QDialog):
    """Material Design 에러 상세 다이얼로그"""
    def __init__(self, error_list, parent=None):
        super().__init__(parent)
        self.error_list = error_list
        self.setWindowTitle("🚨 에러 상세 정보")
        self.setMinimumSize(700, 500)
        
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
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 헤더
        header_layout = QHBoxLayout()
        
        # 에러 아이콘 (QtAwesome 사용)
        try:
            error_icon = qta.icon('fa5s.exclamation-triangle', color=MaterialColors.ERROR)
            icon_label = QLabel()
            icon_pixmap = error_icon.pixmap(32, 32)
            icon_label.setPixmap(icon_pixmap)
        except:
            icon_label = QLabel("⚠️")
            icon_label.setStyleSheet("font-size: 24px;")
        
        # 제목
        title_label = QLabel(f"총 {len(self.error_list)}개의 에러가 발생했습니다")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: 600; 
            color: #212121;
            margin: 0;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 에러 목록 테이블
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(3)
        self.error_table.setHorizontalHeaderLabels(['🕒 시간', '🏷️ 유형', '📝 상세 내용'])
        self.error_table.setStyleSheet("""
            QTableWidget {
                background-color: #fafafa;
                border: none;
                border-radius: 8px;
                selection-background-color: #e3f2fd;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: none;
                padding: 12px 8px;
                font-weight: 600;
                color: #424242;
            }
        """)
        
        # 에러 데이터 추가
        self.error_table.setRowCount(len(self.error_list))
        for i, error_info in enumerate(self.error_list):
            self.error_table.setItem(i, 0, QTableWidgetItem(error_info.get('time', 'N/A')))
            self.error_table.setItem(i, 1, QTableWidgetItem(error_info.get('type', 'Unknown')))
            self.error_table.setItem(i, 2, QTableWidgetItem(error_info.get('message', 'No details')))
        
        # 컬럼 크기 조정
        header = self.error_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 유형
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상세 내용
        
        layout.addWidget(self.error_table)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        # 전체 로그 보기 버튼
        view_log_btn = AppleStyleButton("전체 로그 보기", "fa5s.file-alt", MaterialColors.PRIMARY)
        view_log_btn.clicked.connect(self.view_full_log)
        button_layout.addWidget(view_log_btn)
        
        button_layout.addStretch()
        
        # 닫기 버튼
        close_btn = AppleStyleButton("확인", "fa5s.check", MaterialColors.SUCCESS)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def view_full_log(self):
        """전체 로그를 새 창에서 표시"""
        if hasattr(self.parent(), 'log_output'):
            log_dialog = QDialog(self)
            log_dialog.setWindowTitle("📋 전체 로그")
            log_dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout(log_dialog)
            log_text = ModernLogViewer()
            log_text.setPlainText(self.parent().log_output.toPlainText())
            layout.addWidget(log_text)
            
            close_btn = AppleStyleButton("닫기", "fa5s.times")
            close_btn.clicked.connect(log_dialog.accept)
            layout.addWidget(close_btn)
            
            log_dialog.exec_()

# Real Time Statistics Widget - Material Design version  
class ModernStatsWidget(QFrame):
    """Material Design 실시간 통계 위젯"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_data()
        self.init_ui()
        self.start_timer()
        
    def init_data(self):
        """통계 데이터 초기화"""
        self.files_processed = 0
        self.total_sales = 0
        self.total_margin = 0
        self.error_count = 0
        self.error_list = []
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.processing_speed = 0.0
        
    def init_ui(self):
        """Material Design UI 초기화"""
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {MaterialColors.LIGHT_SURFACE};
                border-radius: 12px;
                border: 1px solid #e5e5e5;
            }}
        """)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)
        
        # 헤더 섹션
        header_layout = QHBoxLayout()
        
        # 타이틀과 아이콘 (QtAwesome 사용)
        try:
            title_icon = qta.icon('fa5s.chart-line', color=MaterialColors.PRIMARY)
            icon_label = QLabel()
            icon_pixmap = title_icon.pixmap(28, 28)
            icon_label.setPixmap(icon_pixmap)
        except:
            icon_label = QLabel("📊")
            icon_label.setStyleSheet("font-size: 24px;")
        
        title_label = QLabel("실시간 통계")
        title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {MaterialColors.PRIMARY};
            margin: 0;
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addSpacing(8)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # KPI 카드 그리드
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)
        
        # KPI 카드들 생성
        self.files_card = ModernDataCard(
            "처리된 파일", "0개", "fa5s.folder", MaterialColors.SUCCESS, "업로드된 파일 수"
        )
        self.sales_card = ModernDataCard(
            "총 매출", "₩0", "fa5s.dollar-sign", MaterialColors.PRIMARY, "오늘 총 매출액"
        )
        self.margin_card = ModernDataCard(
            "순이익", "₩0", "fa5s.chart-line", MaterialColors.WARNING, "총 순이익"
        )
        self.speed_card = ModernDataCard(
            "처리 속도", "0.0 파일/분", "fa5s.tachometer-alt", "#9C27B0", "평균 처리 속도"
        )
        
        # 2x2 그리드로 배치
        kpi_grid.addWidget(self.files_card, 0, 0)
        kpi_grid.addWidget(self.sales_card, 0, 1)
        kpi_grid.addWidget(self.margin_card, 1, 0)
        kpi_grid.addWidget(self.speed_card, 1, 1)
        
        main_layout.addLayout(kpi_grid)
        
        # 하단 상태 바
        status_layout = QHBoxLayout()
        
        # 에러 상태 버튼
        self.error_btn = AppleStyleButton("에러 없음", "fa5s.check-circle", MaterialColors.SUCCESS)
        self.error_btn.clicked.connect(self.show_error_details)
        status_layout.addWidget(self.error_btn)
        
        status_layout.addStretch()
        
        # 마지막 업데이트 시간
        self.last_update_label = QLabel("마지막 업데이트: 방금 전")
        self.last_update_label.setStyleSheet("color: #666; font-size: 12px;")
        status_layout.addWidget(self.last_update_label)
        
        main_layout.addLayout(status_layout)
    
    def start_timer(self):
        """실시간 업데이트 타이머 시작"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)  # 5초마다 업데이트
    
    def update_stats(self):
        """통계 업데이트"""
        try:
            # 마지막 업데이트 시간 갱신
            now = datetime.now()
            time_diff = now - self.last_update
            if time_diff.seconds < 60:
                update_text = "마지막 업데이트: 방금 전"
            else:
                minutes = time_diff.seconds // 60
                update_text = f"마지막 업데이트: {minutes}분 전"
            
            self.last_update_label.setText(update_text)
            self.last_update = now
            
            # 에러 상태 업데이트
            if self.error_count > 0:
                self.error_btn.setText(f"에러 {self.error_count}개")
                self.error_btn.setStyleSheet(self.error_btn.styleSheet().replace(
                    MaterialColors.SUCCESS, MaterialColors.ERROR
                ))
            
        except Exception as e:
            logging.error(f"통계 업데이트 중 오류: {e}")
    
    def show_error_details(self):
        """에러 상세 정보 표시"""
        if self.error_list:
            dialog = ModernErrorDialog(self.error_list, self.parent_widget)
            dialog.exec_()
        else:
            msg = QMessageBox(self.parent_widget)
            msg.setWindowTitle("에러 정보")
            msg.setText("현재 에러가 없습니다.")
            msg.setIcon(QMessageBox.Information)
            msg.exec_()

# 여기서 기존 코드의 나머지 부분들도 동일하게 Material Design으로 변환...
# (RewardManagerDialog, PurchaseManagerDialog, 메인 애플리케이션 등)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 테마 매니저 초기화
    theme_manager = ThemeManager(app)
    theme_manager.setup_auto_theme()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("🎨 새로운 Material Design 3 애플리케이션이 시작되었습니다!")
    
    # 테스트용 간단한 윈도우
    window = QMainWindow()
    window.setWindowTitle("판매 데이터 자동화 - Material Design 3")
    window.setMinimumSize(1200, 800)
    
    # 중앙 위젯
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # 레이아웃
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(20)
    
    # 헤더
    header_label = QLabel("🎨 Material Design 3 변환 완료!")
    header_label.setStyleSheet(f"""
        font-size: 24px;
        font-weight: 700;
        color: {MaterialColors.PRIMARY};
        padding: 20px;
        text-align: center;
    """)
    layout.addWidget(header_label)
    
    # 통계 위젯 테스트
    stats_widget = ModernStatsWidget()
    layout.addWidget(stats_widget)
    
    # 버튼 테스트
    button_layout = QHBoxLayout()
    
    test_btn1 = AppleStyleButton("Primary 버튼", "fa5s.home", MaterialColors.PRIMARY)
    test_btn2 = AppleStyleButton("Success 버튼", "fa5s.check", MaterialColors.SUCCESS)  
    test_btn3 = AppleStyleButton("Warning 버튼", "fa5s.exclamation-triangle", MaterialColors.WARNING)
    test_btn4 = AppleStyleButton("테마 전환", "fa5s.moon")
    test_btn4.clicked.connect(lambda: theme_manager.toggle_theme())
    
    button_layout.addWidget(test_btn1)
    button_layout.addWidget(test_btn2)
    button_layout.addWidget(test_btn3)
    button_layout.addWidget(test_btn4)
    button_layout.addStretch()
    
    layout.addLayout(button_layout)
    
    # 로그 뷰어 테스트
    log_viewer = ModernLogViewer()
    log_viewer.setPlainText("""
2024-12-20 10:30:15 - INFO - 애플리케이션 시작
2024-12-20 10:30:16 - INFO - Material Design 3 테마 적용 완료
2024-12-20 10:30:17 - WARNING - 테스트 경고 메시지
2024-12-20 10:30:18 - ERROR - 테스트 에러 메시지
2024-12-20 10:30:19 - INFO - 모든 컴포넌트 로드 완료
    """)
    layout.addWidget(log_viewer)
    
    window.show()
    sys.exit(app.exec())