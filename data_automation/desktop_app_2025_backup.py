import sys
import os


import logging
import json
import pandas as pd
from datetime import datetime, date
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QFileDialog, QLabel, QGroupBox, QGridLayout,
    QDialog, QTableWidget, QTableWidgetItem, QDateEdit, QHeaderView,
    QMessageBox, QSpinBox, QFrame, QProgressBar, QCheckBox, QScrollArea
)
from PySide6.QtCore import QThread, Signal, Qt, QDate, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter
import re

# PyQt Fluent Widgets imports
from qfluentwidgets import (
    FluentWindow, NavigationInterface, NavigationItemPosition,
    PushButton, PrimaryPushButton, ToggleButton, TransparentPushButton,
    LineEdit, TextEdit, ComboBox, SpinBox, DoubleSpinBox, 
    CheckBox, RadioButton, DatePicker, TimePicker,
    FluentIcon, qconfig, Theme, setTheme, 
    MessageBox, InfoBar, InfoBarPosition,
    CardWidget, ElevatedCardWidget, SimpleCardWidget,
    GroupHeaderCardWidget, HeaderCardWidget,
    ProgressBar, IndeterminateProgressBar, 
    ScrollArea, SmoothScrollArea,
    ToolTipFilter, ToolTipPosition,
    isDarkTheme, setThemeColor
)

# Material Icons import (PySide6 설치로 호환성 해결)
# from qt_material_icons import MaterialIcon

# PyInstaller 호환성을 위한 MaterialIcon 대체 클래스
class MaterialIcon:
    """PyInstaller 호환성을 위한 MaterialIcon 대체"""
    def __init__(self, icon_name=''):
        self.icon_name = icon_name
        # 기본 QIcon 생성 (빈 아이콘)
        self._qicon = QIcon()
    
    def __call__(self):
        return self._qicon

# --- Error Details Dialog ---
class ErrorDetailsDialog(QDialog):
    """에러 상세 정보를 표시하는 Material Design 다이얼로그"""
    def __init__(self, error_list, parent=None):
        super().__init__(parent)
        self.error_list = error_list
        self.setWindowTitle("🚨 에러 상세 정보")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 헤더 카드
        header_card = ElevatedCardWidget()
        header_card.setFixedHeight(80)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        # 아이콘
        error_icon = MaterialIcon('error')
        error_icon.set_color(QColor('#F44336'))
        icon_label = QLabel()
        icon_pixmap = error_icon.pixmap(32, 32)
        icon_label.setPixmap(icon_pixmap)
        
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
        
        layout.addWidget(header_card)
        
        # 에러 목록 카드
        table_card = ElevatedCardWidget()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        
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
        
        header = self.error_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 유형
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상세 내용
        
        # 에러 데이터 추가
        self.error_table.setRowCount(len(self.error_list))
        for i, error_info in enumerate(self.error_list):
            self.error_table.setItem(i, 0, QTableWidgetItem(error_info.get('time', 'N/A')))
            self.error_table.setItem(i, 1, QTableWidgetItem(error_info.get('type', 'Unknown')))
            self.error_table.setItem(i, 2, QTableWidgetItem(error_info.get('message', 'No details')))
        
        table_layout.addWidget(self.error_table)
        layout.addWidget(table_card)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        # 로그 전체 보기 버튼
        view_log_btn = PushButton("전체 로그 보기")
        view_log_btn.setIcon(MaterialIcon('description'))
        view_log_btn.clicked.connect(self.view_full_log)
        button_layout.addWidget(view_log_btn)
        
        button_layout.addStretch()
        
        # 닫기 버튼
        close_btn = PrimaryPushButton("확인")
        close_btn.setIcon(MaterialIcon('check'))
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
            log_text = QTextEdit()
            log_text.setPlainText(self.parent().log_output.toPlainText())
            log_text.setReadOnly(True)
            layout.addWidget(log_text)
            
            close_btn = QPushButton("닫기")
            close_btn.clicked.connect(log_dialog.accept)
            layout.addWidget(close_btn)
            
            log_dialog.exec_()

# --- Real Time Statistics Widget ---
class RealTimeStatsWidget(ElevatedCardWidget):
    """실시간 통계를 표시하는 Material Design 위젯"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent  # 부모 위젯 참조 저장
        self.init_data()
        self.init_ui()
        self.start_timer()
        
    def init_data(self):
        """통계 데이터 초기화"""
        self.files_processed = 0
        self.total_sales = 0
        self.total_margin = 0
        self.error_count = 0
        self.error_list = []  # 에러 상세 정보를 저장할 리스트
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.processing_speed = 0.0
        self.hourly_activity = [0] * 24  # 24시간 활동 데이터
        
    def init_ui(self):
        """Material Design UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)
        
        # 헤더 섹션
        header_layout = QHBoxLayout()
        
        # 타이틀과 아이콘
        title_icon = MaterialIcon('analytics')
        title_icon.set_color(QColor('#2196F3'))
        icon_label = QLabel()
        icon_pixmap = title_icon.pixmap(28, 28)
        icon_label.setPixmap(icon_pixmap)
        
        title_label = QLabel("실시간 통계")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #1976D2;
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
        self.files_card = self.create_material_kpi_card(
            MaterialIcon('folder'), "처리된 파일", "0", "개", "#4CAF50", "업로드된 파일 수"
        )
        self.sales_card = self.create_material_kpi_card(
            MaterialIcon('attach_money'), "총 매출", "₩0", "", "#2196F3", "오늘 총 매출액"
        )
        self.margin_card = self.create_material_kpi_card(
            MaterialIcon('trending_up'), "순이익", "₩0", "", "#FF9800", "총 순이익"
        )
        self.speed_card = self.create_material_kpi_card(
            MaterialIcon('speed'), "처리 속도", "0.0", "파일/분", "#9C27B0", "평균 처리 속도"
        )
        
        # 2x2 그리드로 배치
        kpi_grid.addWidget(self.files_card, 0, 0)
        kpi_grid.addWidget(self.sales_card, 0, 1)
        kpi_grid.addWidget(self.margin_card, 1, 0)
        kpi_grid.addWidget(self.speed_card, 1, 1)
        
        main_layout.addLayout(kpi_grid)
        
        # 하단 상태 바 카드
        status_card = SimpleCardWidget()
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(20, 16, 20, 16)
        status_layout.setSpacing(24)
        
        # 에러 상태 (클릭 가능한 에러 카드)
        self.error_card = self.create_error_status_card()
        status_layout.addWidget(self.error_card)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("QFrame { background-color: #E0E0E0; }")
        separator.setFixedWidth(1)
        status_layout.addWidget(separator)
        
        # 활동 상태
        activity_layout = QVBoxLayout()
        activity_layout.setSpacing(6)
        
        activity_header = QHBoxLayout()
        activity_icon = MaterialIcon('timeline')
        activity_icon.set_color(QColor('#4CAF50'))
        activity_icon_label = QLabel()
        activity_icon_label.setPixmap(activity_icon.pixmap(16, 16))
        
        activity_label = QLabel("오늘 활동")
        activity_label.setStyleSheet("color: #666; font-size: 13px; font-weight: 600;")
        
        activity_header.addWidget(activity_icon_label)
        activity_header.addSpacing(6)
        activity_header.addWidget(activity_label)
        activity_header.addStretch()
        
        # 진행 바
        self.activity_progress = ProgressBar()
        self.activity_progress.setMaximum(100)
        self.activity_progress.setValue(0)
        self.activity_progress.setFixedHeight(6)
        
        activity_layout.addLayout(activity_header)
        activity_layout.addWidget(self.activity_progress)
        status_layout.addLayout(activity_layout)
        
        status_layout.addStretch()
        
        # 마지막 업데이트 시간
        update_layout = QVBoxLayout()
        update_layout.setSpacing(2)
        
        update_label = QLabel("마지막 업데이트")
        update_label.setStyleSheet("color: #999; font-size: 11px; font-weight: 500;")
        
        self.last_update_label = QLabel("방금 전")
        self.last_update_label.setStyleSheet("color: #666; font-size: 12px; font-weight: 600;")
        
        update_layout.addWidget(update_label)
        update_layout.addWidget(self.last_update_label)
        status_layout.addLayout(update_layout)
        
        main_layout.addWidget(status_card)
        
        # 가운데 구분선
        v_separator = QFrame()
        v_separator.setFrameShape(QFrame.VLine)
        v_separator.setStyleSheet("QFrame { color: #E0E0E0; }")
        main_layout.addWidget(v_separator)
        
        # 활동 진행 바 (시각적 효과)
        activity_layout = QVBoxLayout()
        activity_layout.setSpacing(5)
        activity_label = QLabel("📈 오늘 활동")
        activity_label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        
        self.activity_progress = QProgressBar()
        self.activity_progress.setMaximum(100)
        self.activity_progress.setValue(0)
        self.activity_progress.setTextVisible(False)
        self.activity_progress.setFixedHeight(8)
        self.activity_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E8F5E8;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4CAF50, stop: 1 #81C784);
                border-radius: 4px;
            }
        """)
        
        activity_layout.addWidget(activity_label)
        activity_layout.addWidget(self.activity_progress)
        main_layout.addLayout(activity_layout)
        
        # 마지막 업데이트 시간
        update_layout = QVBoxLayout()
        update_layout.setSpacing(5)
        update_label = QLabel("🕒 마지막 업데이트")
        update_label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        self.last_update_label = QLabel("방금 전")
        self.last_update_label.setStyleSheet("color: #666; font-size: 12px;")
        update_layout.addWidget(update_label)
        update_layout.addWidget(self.last_update_label)
        main_layout.addLayout(update_layout)
        
        # 전체 위젯 스타일
        self.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                margin-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px 5px 10px;
                background-color: #FAFAFA;
                border-radius: 5px;
            }
        """)
        
    def create_kpi_card(self, icon, title, value, unit, color):
        """KPI 카드 생성"""
        card = QFrame()
        card.setFixedHeight(80)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
            QFrame:hover {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-color: {color};
            }}
        """ )
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        
        # 상단: 아이콘 + 제목
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px; color: {color};")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10px; color: #666; font-weight: normal;")
        
        top_layout.addWidget(icon_label)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        # 하단: 값 + 단위
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        value_label.setObjectName(f"{title}_value")  # 나중에 업데이트용
        
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("font-size: 12px; color: #999; font-weight: normal;")
        
        bottom_layout.addWidget(value_label)
        bottom_layout.addWidget(unit_label)
        bottom_layout.addStretch()
        
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        
        return card
        
    def create_material_kpi_card(self, icon, title, value, unit, color, tooltip):
        """Material Design KPI 카드 생성"""
        card = ElevatedCardWidget()
        card.setFixedHeight(120)
        card.setToolTip(tooltip)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # 헤더: 아이콘 + 제목
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # 아이콘
        icon.set_color(QColor(color))
        icon_label = QLabel()
        icon_pixmap = icon.pixmap(24, 24)
        icon_label.setPixmap(icon_pixmap)
        
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
        value_layout = QHBoxLayout()
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #212121;
            margin: 0;
        """)
        value_label.setObjectName(f"{title}_value")
        
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("""
                font-size: 14px;
                font-weight: 500;
                color: #757575;
                margin-left: 4px;
            """)
            value_layout.addWidget(unit_label)
        
        value_layout.addWidget(value_label)
        value_layout.addStretch()
        
        layout.addLayout(value_layout)
        layout.addStretch()
        
        return card
    
    def create_error_status_card(self):
        """에러 상태를 표시하는 클릭 가능한 카드 생성"""
        error_widget = QWidget()
        error_widget.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(error_widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # 에러 아이콘
        error_icon = MaterialIcon('error_outline')
        error_icon.set_color(QColor('#F44336'))
        icon_label = QLabel()
        icon_label.setPixmap(error_icon.pixmap(20, 20))
        
        # 에러 텍스트
        error_layout = QVBoxLayout()
        error_layout.setSpacing(2)
        
        error_title = QLabel("에러")
        error_title.setStyleSheet("color: #666; font-size: 12px; font-weight: 600;")
        
        self.error_count_label = QLabel("0건")
        self.error_count_label.setStyleSheet("""
            color: #F44336; 
            font-size: 16px; 
            font-weight: 700;
            margin: 0;
        """)
        
        error_layout.addWidget(error_title)
        error_layout.addWidget(self.error_count_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(error_layout)
        
        # 클릭 이벤트 연결
        error_widget.mousePressEvent = self.show_error_details
        
        # 호버 효과
        def on_enter(event):
            error_widget.setStyleSheet("background-color: rgba(244, 67, 54, 0.08); border-radius: 8px;")
        def on_leave(event):
            error_widget.setStyleSheet("")
            
        error_widget.enterEvent = on_enter
        error_widget.leaveEvent = on_leave
        
        return error_widget
        
    def start_timer(self):
        """1초마다 화면 업데이트"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 1초
        
    def update_display(self):
        """통계 화면 업데이트"""
        # 처리 속도 계산
        elapsed_minutes = max((datetime.now() - self.start_time).total_seconds() / 60, 0.1)
        self.processing_speed = self.files_processed / elapsed_minutes
        
        # KPI 카드 값 업데이트 (Material Design 스타일)
        self.update_kpi_card("처리된 파일", f"{self.files_processed}")
        self.update_kpi_card("총 매출", f"₩{self.total_sales:,0f}")
        self.update_kpi_card("순이익", f"₩{self.total_margin:,0f}")
        self.update_kpi_card("처리 속도", f"{self.processing_speed:.1f}")
        
        # 에러 카운트 업데이트 (Material Design 스타일)
        self.error_count_label.setText(f"{self.error_count}건")
        
        # 에러 상태에 따른 색상 변경
        if self.error_count > 0:
            self.error_count_label.setStyleSheet("""
                color: #F44336; 
                font-size: 16px; 
                font-weight: 700;
                margin: 0;
            """)
        else:
            self.error_count_label.setStyleSheet("""
                color: #4CAF50; 
                font-size: 16px; 
                font-weight: 700;
                margin: 0;
            """)
        
        # 활동 진행 바 업데이트 (파일 처리량에 따라)
        activity_percent = min(self.files_processed * 10, 100)  # 파일 10개당 100%
        self.activity_progress.setValue(activity_percent)
        
        # 마지막 업데이트 시간
        time_diff = datetime.now() - self.last_update
        if time_diff.total_seconds() < 60:
            time_text = "방금 전"
        elif time_diff.total_seconds() < 3600:
            time_text = f"{int(time_diff.total_seconds() // 60)}분 전"
        else:
            time_text = f"{int(time_diff.total_seconds() // 3600)}시간 전"
        self.last_update_label.setText(time_text)
        
    def update_kpi_card(self, title, value):
        """특정 KPI 카드의 값 업데이트"""
        value_label = self.findChild(QLabel, f"{title}_value")
        if value_label:
            value_label.setText(value)
    
    def parse_log_message(self, log_message):
        """로그 메시지를 파싱하여 통계 업데이트"""
        try:
            # 파일 처리 완료 감지
            if any(keyword in log_message for keyword in ["생성 완료", "처리 완료", ".xlsx 생성", "리포트 생성"]):
                self.files_processed += 1
                self.last_update = datetime.now()
                
            # 매출 정보 추출 (리포트 로그에서 나오는 패턴들)
            # 패턴: "총 매출: 1,234,567원", "- 총 매출: 1234567", "매출: 1,234,567"
            sales_patterns = [
                r'총 매출[:\s]*([0-9,]+)',
                r'총매출[:\s]*([0-9,]+)', 
                r'매출[:\s]*([0-9,]+)',
                r'총 매출: ([0-9,]+)원'
            ]
            
            for pattern in sales_patterns:
                sales_match = re.search(pattern, log_message)
                if sales_match:
                    try:
                        sales_value = int(sales_match.group(1).replace(',', ''))
                        if sales_value > 0:  # 0원 제외
                            self.total_sales += sales_value
                            self.last_update = datetime.now()
                        break
                    except:
                        continue
                        
            # 마진 정보 추출
            margin_patterns = [
                r'총 판매마진[:\s]*([0-9,]+)',
                r'총판매마진[:\s]*([0-9,]+)',
                r'판매마진[:\s]*([0-9,]+)',
                r'총 마진[:\s]*([0-9,]+)'
            ]
            
            for pattern in margin_patterns:
                margin_match = re.search(pattern, log_message)
                if margin_match:
                    try:
                        margin_value = int(margin_match.group(1).replace(',', ''))
                        if margin_value > 0:  # 0원 제외
                            self.total_margin += margin_value
                            self.last_update = datetime.now()
                        break
                    except:
                        continue
                
            # 에러 감지 및 상세 정보 저장
            error_keywords = ['오류', 'error', '실패', '에러', 'exception', 'failed', '처리 실패', '생성 실패']
            # 정보성 메시지 제외
            info_keywords = ['info', '완료', '시작', '성공', 'success']
            
            log_lower = log_message.lower()
            has_error = any(keyword in log_lower for keyword in error_keywords)
            has_info = any(keyword in log_lower for keyword in info_keywords)
            
            if has_error and not has_info:
                self.error_count += 1
                self.last_update = datetime.now()
                
                # 에러 상세 정보 저장
                error_info = {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'type': self.extract_error_type(log_message),
                    'message': log_message.strip()
                }
                self.error_list.append(error_info)
                
                # 에러 리스트가 너무 길어지면 오래된 것부터 제거 (최대 100개)
                if len(self.error_list) > 100:
                    self.error_list.pop(0)
                
        except Exception as e:
            # 파싱 실패해도 프로그램은 계속 실행
            pass
    
    def extract_error_type(self, log_message):
        """로그 메시지에서 에러 타입 추출"""
        error_patterns = {
            '파일 오류': ['파일을 찾을 수 없습니다', '파일 접근', 'FileNotFoundError', '읽을 수 없습니다'],
            '데이터 오류': ['컬럼', '데이터 타입', 'KeyError', '병합 실패', '매칭 실패'],
            '메모리 오류': ['메모리', 'MemoryError', 'OutOfMemory'],
            '권한 오류': ['권한', 'PermissionError', '접근 거부'],
            '네트워크 오류': ['연결', 'ConnectionError', 'TimeoutError'],
            '계산 오류': ['나누기', 'ZeroDivisionError', '계산 실패'],
            '일반 오류': ['Exception', 'Error', '예외']
        }
        
        log_lower = log_message.lower()
        for error_type, keywords in error_patterns.items():
            if any(keyword.lower() in log_lower for keyword in keywords):
                return error_type
        
        return '일반 오류'
    
    def show_error_details(self, event):
        """에러 상세 정보 팝업 표시"""
        if self.error_count == 0:
            QMessageBox.information(self, "정보", "현재 발생한 에러가 없습니다. ✅")
            return
            
        # 에러 상세 다이얼로그 표시
        dialog = ErrorDetailsDialog(self.error_list, self.parent_widget)
        dialog.exec_()
    
    def reset_daily_stats(self):
        """일일 통계 리셋"""
        self.files_processed = 0
        self.total_sales = 0
        self.total_margin = 0
        self.error_count = 0
        self.error_list = []  # 에러 목록도 초기화
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.processing_speed = 0.0

# --- Reward Manager Dialog ---
class RewardManagerDialog(QDialog):
    """리워드 관리 팝업창 (하루 단위 설정)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('💰 일일 리워드 관리')
        self.setFixedSize(950, 750)  # 사이즈 약간 확대
        self.setModal(True)
        
        # 2025 디자인 트렌드 적용
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FAFAFA, stop:1 #F5F5F5);
                border-radius: 16px;
                border: 2px solid #E0E0E0;
            }
            QLabel {
                color: #212121;
            }
            QPushButton {
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QTableWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F5F5F5;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
                color: #1976D2;
            }
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
        layout = QVBoxLayout(self)
        
        # 헤더
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFE0B2, stop:1 #FFCC02);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        """)
        header_layout = QVBoxLayout(header_widget)
        
        title_label = QLabel("💰 일일 리워드 설정")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #E65100;
            margin: 0;
        """)
        
        subtitle_label = QLabel("상품별 리워드 금액을 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #BF360C;
            margin-top: 4px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_widget)
        
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
            btn.clicked.connect(lambda checked, v=value: self.bulk_reward.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        
        # 네 번째 줄: 적용 버튼
        self.apply_selected_button = QPushButton("선택된 항목에 적용")
        self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # --- 상품 테이블 ---
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '리워드 금액'])
        
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 리워드
        
        layout.addWidget(self.product_table)
        
        # --- 저장 버튼 ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_rewards)
        self.save_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)

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
                    # 파일이 비어있을 경우 대비
                    content = f.read()
                    if content:
                        self.all_rewards_data = json.loads(content)
                    else:
                        self.all_rewards_data = {'rewards': []}
            else:
                self.all_rewards_data = {'rewards': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스를 로드하는 중 오류가 발생했습니다:\n{e}")

    def load_rewards_for_date(self, q_date):
        """선택된 날짜의 리워드 정보를 테이블에 로드"""
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        # 날짜에 맞는 리워드 맵 생성 (start_date 기준, 백엔드 로직과 동일하게)
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
            product_id = self.product_table.item(row, 1).text()  # 1번 컬럼으로 변경
            spinbox = self.product_table.cellWidget(row, 3)  # 3번 컬럼으로 변경
            if spinbox and product_id in reward_map:
                spinbox.setValue(reward_map[product_id])
        
        QMessageBox.information(self, "완료", f"{source_date_str}의 설정이 현재 테이블로 복사되었습니다.\n저장 버튼을 눌러야 최종 반영됩니다.")

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
            product_name = self.product_table.item(row, 2).text().lower()  # 2번 컬럼으로 변경
            self.product_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()  # 필터링 후 선택 개수 업데이트

    def save_rewards(self):
        """현재 날짜의 리워드 설정을 저장 (덮어쓰기 방식)"""
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            
            # 현재 날짜와 다른 날짜의 설정만 유지 (start_date 기준)
            other_days_rewards = [
                entry for entry in self.all_rewards_data.get('rewards', [])
                if entry.get('start_date') != target_date_str
            ]
            
            # 현재 테이블의 설정 추가 (백엔드와 호환되도록 start_date, end_date 사용)
            new_rewards_for_date = []
            for row in range(self.product_table.rowCount()):
                spinbox = self.product_table.cellWidget(row, 3)  # 3번 컬럼으로 변경
                if spinbox:
                    # 0원 리워드도 의미가 있을 수 있으므로 저장
                    entry = {
                        'start_date': target_date_str,
                        'end_date': target_date_str,
                        'product_id': self.product_table.item(row, 1).text(),  # 1번 컬럼으로 변경
                        'reward': spinbox.value()
                    }
                    new_rewards_for_date.append(entry)
            
            self.all_rewards_data['rewards'] = other_days_rewards + new_rewards_for_date
            
            # 파일 저장
            with open(self.reward_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_rewards_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "완료", f"{target_date_str}의 리워드 설정이 저장되었습니다.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"리워드 설정 저장 중 오류가 발생했습니다:\n{e}")


# --- Purchase Manager Dialog ---
class PurchaseManagerDialog(QDialog):
    """가구매 개수 관리 팝업창 (하루 단위 설정)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🛒 일일 가구매 개수 관리')
        self.setFixedSize(950, 750)  # 사이즈 약간 확대
        self.setModal(True)
        
        # 2025 디자인 트렌드 적용
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FAFAFA, stop:1 #F5F5F5);
                border-radius: 16px;
                border: 2px solid #E0E0E0;
            }
            QLabel {
                color: #212121;
            }
            QPushButton {
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QTableWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F5F5F5;
            }
            QTableWidget::item:selected {
                background: #E1F5FE;
                color: #01579B;
            }
        """)
        
        from modules import config
        self.purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')
        self.margin_file = config.MARGIN_FILE
        
        self.all_purchases_data = {'purchases': []}
        self.products_df = pd.DataFrame()

        self.initUI()
        self.load_data_sources()
        self.load_purchases_for_date(QDate.currentDate())

    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 헤더
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #E1F5FE, stop:1 #81D4FA);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        """)
        header_layout = QVBoxLayout(header_widget)
        
        title_label = QLabel("🛒 일일 가구매 개수 설정")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #01579B;
            margin: 0;
        """)
        
        subtitle_label = QLabel("상품별 가구매 개수를 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #0277BD;
            margin-top: 4px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_widget)
        
        # --- 날짜 선택 및 복사 ---
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setDate(QDate.currentDate())
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_purchases_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit()
        self.source_date_edit.setDate(QDate.currentDate().addDays(-1))
        self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        
        self.copy_button = QPushButton("의 설정 불러오기")
        self.copy_button.clicked.connect(self.copy_purchases)
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
        self.bulk_purchase = QSpinBox()
        self.bulk_purchase.setRange(0, 9999)
        self.bulk_purchase.setSuffix(" 개")
        self.bulk_purchase.setSingleStep(1)
        self.bulk_purchase.setValue(0)
        bulk_layout.addWidget(self.bulk_purchase)
        
        # 빠른 설정 버튼들
        quick_buttons = [
            ("0개", 0),
            ("1개", 1),
            ("3개", 3),
            ("5개", 5),
            ("10개", 10)
        ]
        
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(50)
            btn.clicked.connect(lambda checked, v=value: self.bulk_purchase.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        
        # 네 번째 줄: 적용 버튼
        self.apply_selected_button = QPushButton("선택된 항목에 적용")
        self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # --- 상품 테이블 ---
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '가구매 개수'])
        
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 가구매 개수
        
        layout.addWidget(self.product_table)
        
        # --- 저장 버튼 ---
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_purchases)
        self.save_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)

    def load_data_sources(self):
        """초기 데이터 (상품 목록, 전체 가구매 설정) 로드"""
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

            if os.path.exists(self.purchase_file):
                with open(self.purchase_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        self.all_purchases_data = json.loads(content)
                    else:
                        self.all_purchases_data = {'purchases': []}
            else:
                self.all_purchases_data = {'purchases': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스를 로드하는 중 오류가 발생했습니다:\n{e}")

    def load_purchases_for_date(self, q_date):
        """선택된 날짜의 가구매 정보를 테이블에 로드"""
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        purchase_map = {}
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == target_date_str and entry.get('end_date') == target_date_str:
                purchase_map[str(entry['product_id'])] = entry['purchase_count']

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
            
            # 가구매 개수 (3번 컬럼)
            spinbox = QSpinBox()
            spinbox.setRange(0, 9999)
            spinbox.setSingleStep(1)
            spinbox.setSuffix(" 개")
            spinbox.setValue(purchase_map.get(product_id, 0))
            self.product_table.setCellWidget(row, 3, spinbox)
        
        self.filter_products()
        self.update_selected_count()

    def copy_purchases(self):
        """선택한 날짜의 설정을 현재 날짜의 테이블에 복사"""
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        
        purchase_map = {}
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == source_date_str:
                purchase_map[str(entry['product_id'])] = entry['purchase_count']
        
        if not purchase_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 가구매 설정이 없습니다.")
            return

        for row in range(self.product_table.rowCount()):
            product_id = self.product_table.item(row, 1).text()  # 1번 컬럼으로 변경
            spinbox = self.product_table.cellWidget(row, 3)  # 3번 컬럼으로 변경
            if spinbox and product_id in purchase_map:
                spinbox.setValue(purchase_map[product_id])
        
        QMessageBox.information(self, "완료", f"{source_date_str}의 설정이 현재 테이블로 복사되었습니다.\n저장 버튼을 눌러야 최종 반영됩니다.")

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
        """선택된 항목에만 가구매 개수 적용"""
        bulk_value = self.bulk_purchase.value()
        applied_count = 0
        
        for row in range(self.product_table.rowCount()):
            checkbox = self.product_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                spinbox = self.product_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
        
        if applied_count > 0:
            QMessageBox.information(self, "완료", f"{applied_count}개 상품에 {bulk_value}개 가구매가 적용되었습니다.")
        else:
            QMessageBox.information(self, "알림", "선택된 상품이 없습니다.")

    def filter_products(self):
        """상품명으로 필터링"""
        search_text = self.search_box.text().lower()
        for row in range(self.product_table.rowCount()):
            product_name = self.product_table.item(row, 2).text().lower()  # 2번 컬럼으로 변경
            self.product_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()  # 필터링 후 선택 개수 업데이트

    def save_purchases(self):
        """현재 날짜의 가구매 설정을 저장 (덮어쓰기 방식)"""
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            
            # 현재 날짜와 다른 날짜의 설정만 유지
            other_days_purchases = [
                entry for entry in self.all_purchases_data.get('purchases', [])
                if entry.get('start_date') != target_date_str
            ]
            
            # 현재 테이블의 설정 추가
            new_purchases_for_date = []
            for row in range(self.product_table.rowCount()):
                spinbox = self.product_table.cellWidget(row, 3)  # 3번 컬럼으로 변경
                if spinbox:
                    entry = {
                        'start_date': target_date_str,
                        'end_date': target_date_str,
                        'product_id': self.product_table.item(row, 1).text(),  # 1번 컬럼으로 변경
                        'purchase_count': spinbox.value()
                    }
                    new_purchases_for_date.append(entry)
            
            self.all_purchases_data['purchases'] = other_days_purchases + new_purchases_for_date
            
            with open(self.purchase_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_purchases_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "완료", f"{target_date_str}의 가구매 설정이 저장되었습니다.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"가구매 설정 저장 중 오류가 발생했습니다:\n{e}")



# --- Custom Logging Handler ---
class PyQtSignalHandler(logging.Handler):
    """A logging handler that emits a PyQt signal."""
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

# --- Worker Thread ---
class Worker(QThread):
    """
    Runs the file monitoring and processing logic in a separate thread.
    """
    output_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, download_folder_path, password=None):
        super().__init__()
        self.download_folder_path = download_folder_path
        self.password = password
        self.handler = None

    def run(self):
        """
        Configures logging for this thread, sets the download directory,
        and starts the file monitoring process.
        """
        # Configure logging to emit signals
        self.handler = PyQtSignalHandler(self.output_signal)
        self.handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.INFO)

        try:
            # Dynamically import and set config
            from modules import config
            config.DOWNLOAD_DIR = self.download_folder_path
            
            # Set password if provided
            if hasattr(self, 'password') and self.password:
                config.ORDER_FILE_PASSWORD = self.password
                logging.info(f"주문조회 파일 암호가 설정되었습니다.")
            
            # Dynamically import file_handler and start monitoring
            from modules import file_handler
            file_handler.start_monitoring()

        except Exception as e:
            logging.error(f"자동화 프로세스 실행 중 오류 발생: {e}")
        finally:
            # 안전한 정리 작업
            try:
                if self.handler:
                    logging.getLogger().removeHandler(self.handler)
            except:
                pass  # 로깅 핸들러 제거 실패해도 계속 진행
            
            self.finished_signal.emit()

# --- Manual Process Worker Thread ---
class ManualProcessWorker(QThread):
    """작업폴더의 미완료 파일들을 수동으로 처리하는 워커 스레드"""
    output_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, download_folder_path, password):
        super().__init__()
        self.download_folder_path = download_folder_path
        self.password = password
        self.handler = None

    def run(self):
        # Configure logging to emit signals
        self.handler = PyQtSignalHandler(self.output_signal)
        self.handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.INFO)

        try:
            # Dynamically import and set config
            from modules import config, file_handler
            config.DOWNLOAD_DIR = self.download_folder_path
            
            if self.password:
                config.ORDER_FILE_PASSWORD = self.password
            
            # 작업폴더 초기화
            file_handler.initialize_folders()
            
            # 미완료 파일들 처리
            file_handler.process_incomplete_files()
            
            # 최종 정리 수행 (전체 통합 리포트 생성 및 파일 이동)
            file_handler.finalize_all_processing()
            
        except Exception as e:
            logging.error(f"수동 처리 중 오류 발생: {e}")
        finally:
            try:
                if self.handler:
                    logging.getLogger().removeHandler(self.handler)
            except:
                pass
            
            self.finished_signal.emit()

# --- Main Application UI ---
class DesktopApp(FluentWindow):
    def __init__(self):
        super().__init__()
        self.is_monitoring = False
        self.is_manual_processing = False  # 수동 처리 상태 추가
        self.worker = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.stop_flag_path = os.path.join(self.base_dir, 'stop.flag')
        self.download_folder_path = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle('🚀 판매 데이터 자동화 - 2025 Edition')
        self.resize(1200, 900)  # 더 넓고 높게
        
        # 2025 트렌드: 앱 아이콘 설정 (유니코드 이모지를 사용한 시각적 아이덴티티)
        try:
            # Windows에서 이모지 아이콘 설정 (최신 트렌드)
            import win32gui
            import win32con
            # 아이콘은 실제로는 ico 파일이 필요하지만, 2025년에는 이모지 기반 브랜딩이 트렌드
        except ImportError:
            pass  # win32gui 없어도 괜찮음
        
        # 테마 설정
        setTheme(Theme.LIGHT)
        setThemeColor('#2196F3')
        
        # 메인 위젯 생성
        main_widget = QWidget()
        main_widget.setObjectName('mainWidget')
        
        # 스크롤 영역 설정
        scroll_area = SmoothScrollArea()
        scroll_area.setObjectName('mainInterface')
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 메인 레이아웃 - 2025 트렌드 적용
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(24, 16, 24, 24)  # 상단 여백 줄임
        main_layout.setSpacing(20)  # 카드 간격 줄임
        
        self.setup_header(main_layout)
        self.setup_main_controls(main_layout)
        self.setup_statistics(main_layout)
        self.setup_log_section(main_layout)
        
        # FluentWindow의 메인 인터페이스로 설정
        self.addSubInterface(scroll_area, FluentIcon.HOME, '메인')
    
    def setup_header(self, layout):
        """헤더 섹션 설정"""
        header_card = HeaderCardWidget()
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(32, 24, 32, 24)  # 좀 더 넓은 여백
        
        # 로고와 제목
        title_layout = QVBoxLayout()
        
        app_title = QLabel("🚀 판매 데이터 자동화")
        app_title.setStyleSheet("""
            font-size: 32px;
            font-weight: 800;
            color: #1976D2;
            margin: 0;
        """)
        
        app_subtitle = QLabel("네이버 스마트스토어 판매 데이터를 자동으로 처리합니다")
        app_subtitle.setStyleSheet("""
            font-size: 16px;
            color: #757575;
            margin-top: 8px;
        """)
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # 상태 표시
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1976D2;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #E3F2FD, stop:1 #BBDEFB);
            padding: 12px 20px;
            border-radius: 25px;
            border: 2px solid #2196F3;
        """)
        
        header_layout.addWidget(self.status_label)
        layout.addWidget(header_card)
    
    def setup_main_controls(self, layout):
        """메인 컨트롤 섹션 설정"""
        controls_card = ElevatedCardWidget()
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(24, 20, 24, 20)
        controls_layout.setSpacing(20)
        
        # 폴더 선택 섹션
        folder_section = self.create_folder_selection_section()
        controls_layout.addWidget(folder_section)
        
        # 설정 섹션
        settings_section = self.create_settings_section()
        controls_layout.addWidget(settings_section)
        
        # 버튼 섹션
        button_section = self.create_button_section()
        controls_layout.addWidget(button_section)
        
        layout.addWidget(controls_card)
    
    def create_folder_selection_section(self):
        """폴더 선택 섹션 생성"""
        section_widget = QWidget()
        layout = QVBoxLayout(section_widget)
        layout.setSpacing(12)
        
        # 섹션 제목
        title = QLabel("📁 다운로드 폴더 설정")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #333; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # 폴더 선택 컨트롤
        folder_layout = QHBoxLayout()
        
        self.folder_path_input = LineEdit()
        self.folder_path_input.setReadOnly(True)
        self.folder_path_input.setPlaceholderText("다운로드 폴더를 선택해주세요...")
        
        self.browse_button = PushButton("폴더 선택")
        self.browse_button.setIcon(MaterialIcon('folder_open'))
        self.browse_button.clicked.connect(self.browse_folder)
        
        folder_layout.addWidget(self.folder_path_input, 1)
        folder_layout.addWidget(self.browse_button)
        
        layout.addLayout(folder_layout)
        return section_widget
    
    def create_settings_section(self):
        """설정 섹션 생성"""
        section_widget = QWidget()
        layout = QVBoxLayout(section_widget)
        layout.setSpacing(12)
        
        # 섹션 제목
        title = QLabel("🔐 파일 암호 설정")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #333; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # 암호 입력 컨트롤
        password_layout = QHBoxLayout()
        
        self.password_input = LineEdit()
        self.password_input.setText("1234")  # 기본값
        self.password_input.setEchoMode(LineEdit.Password)
        self.password_input.setPlaceholderText("주문조회 파일 암호 (기본: 1234)")
        
        self.show_password_button = PushButton()
        self.show_password_button.setIcon(MaterialIcon('visibility'))
        self.show_password_button.setFixedSize(44, 44)
        self.show_password_button.clicked.connect(self.toggle_password_visibility)
        self.show_password_button.setToolTip("암호 표시/숨기기")
        self.show_password_button.setStyleSheet("""
            PushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F5F5F5, stop:1 #EEEEEE);
                border: 2px solid #E0E0E0;
                border-radius: 22px;
                padding: 8px;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E8F5E8, stop:1 #C8E6C9);
                border: 2px solid #4CAF50;
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A5D6A7, stop:1 #81C784);
            }
        """)
        
        password_layout.addWidget(self.password_input, 1)
        password_layout.addWidget(self.show_password_button)
        
        layout.addLayout(password_layout)
        return section_widget
    
    def create_button_section(self):
        """버튼 섹션 생성"""
        section_widget = QWidget()
        layout = QVBoxLayout(section_widget)
        layout.setSpacing(16)
        
        # 메인 액션 버튼들
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(12)
        
        # 자동화 토글 버튼
        self.toggle_button = PrimaryPushButton("🎆 자동화 시작")
        self.toggle_button.setIcon(MaterialIcon('play_arrow'))
        self.toggle_button.clicked.connect(self.toggle_monitoring)
        self.toggle_button.setMinimumHeight(56)  # 더 큰 버튼
        self.toggle_button.setStyleSheet("""
            PrimaryPushButton {
                font-size: 16px;
                font-weight: 700;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #2E7D32);
                border: none;
                border-radius: 28px;
                color: white;
                padding: 16px 32px;
            }
            PrimaryPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #66BB6A, stop:1 #388E3C);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            }
            PrimaryPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2E7D32, stop:1 #1B5E20);
                transform: translateY(0px);
            }
        """)
        
        # 수동 처리 버튼 - 2025 스타일 적용
        self.manual_process_button = PushButton("📁 작업폴더 처리")
        self.manual_process_button.setIcon(MaterialIcon('folder_special'))
        self.manual_process_button.clicked.connect(self.manual_process)
        self.manual_process_button.setMinimumHeight(56)
        self.manual_process_button.setStyleSheet("""
            PushButton {
                font-size: 16px;
                font-weight: 600;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF9800, stop:1 #F57C00);
                border: none;
                border-radius: 28px;
                color: white;
                padding: 16px 32px;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFB74D, stop:1 #FB8C00);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F57C00, stop:1 #E65100);
                transform: translateY(0px);
            }
        """)
        
        main_buttons_layout.addWidget(self.toggle_button, 2)
        main_buttons_layout.addWidget(self.manual_process_button, 1)
        
        layout.addLayout(main_buttons_layout)
        
        # 관리 버튼들
        management_buttons_layout = QHBoxLayout()
        
        self.reward_button = PushButton("💰 리워드 관리")
        self.reward_button.setIcon(MaterialIcon('card_giftcard'))
        self.reward_button.clicked.connect(self.open_reward_manager)
        self.reward_button.setStyleSheet("""
            PushButton {
                font-size: 14px;
                font-weight: 600;
                padding: 12px 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE0B2, stop:1 #FFCC02);
                border: 2px solid #FFA000;
                border-radius: 8px;
                color: #E65100;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFD54F, stop:1 #FFC107);
                transform: translateY(-1px);
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFA000, stop:1 #FF8F00);
                transform: translateY(1px);
            }
        """)
        
        self.purchase_button = PushButton("🛒 가구매 관리") 
        self.purchase_button.setIcon(MaterialIcon('shopping_cart'))
        self.purchase_button.clicked.connect(self.open_purchase_manager)
        self.purchase_button.setStyleSheet("""
            PushButton {
                font-size: 14px;
                font-weight: 600;
                padding: 12px 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E1F5FE, stop:1 #81D4FA);
                border: 2px solid #03A9F4;
                border-radius: 8px;
                color: #01579B;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #B3E5FC, stop:1 #4FC3F7);
                transform: translateY(-1px);
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0288D1, stop:1 #0277BD);
                transform: translateY(1px);
            }
        """)
        
        management_buttons_layout.addWidget(self.reward_button)
        management_buttons_layout.addWidget(self.purchase_button)
        management_buttons_layout.addStretch()
        
        layout.addLayout(management_buttons_layout)
        return section_widget
    
    def setup_statistics(self, layout):
        """통계 섹션 설정"""
        self.stats_widget = RealTimeStatsWidget(self)
        layout.addWidget(self.stats_widget)
    
    def setup_log_section(self, layout):
        """로그 섹션 설정"""
        log_card = ElevatedCardWidget()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(24, 20, 24, 20)
        log_layout.setSpacing(12)
        
        # 로그 헤더
        log_header_layout = QHBoxLayout()
        
        # 로그 토글 버튼 (2025 스타일)
        self.log_toggle_button = PushButton("📋 실행 로그 보기")
        self.log_toggle_button.setIcon(MaterialIcon('description'))
        self.log_toggle_button.clicked.connect(self.toggle_log_display)
        self.log_toggle_button.setStyleSheet("""
            PushButton {
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E8F5E8, stop:1 #C8E6C9);
                border: 2px solid #4CAF50;
                border-radius: 8px;
                color: #2E7D32;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A5D6A7, stop:1 #81C784);
                transform: translateY(-1px);
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66BB6A, stop:1 #4CAF50);
                transform: translateY(1px);
            }
        """)
        
        log_header_layout.addWidget(self.log_toggle_button)
        log_header_layout.addStretch()
        
        # 로그 지우기 버튼 (처음엔 숨김) - 2025 스타일
        self.log_clear_button = PushButton("🗑️ 지우기")
        self.log_clear_button.setIcon(MaterialIcon('delete'))
        self.log_clear_button.clicked.connect(self.clear_log)
        self.log_clear_button.setVisible(False)
        self.log_clear_button.setStyleSheet("""
            PushButton {
                font-size: 12px;
                font-weight: 600;
                padding: 8px 16px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFEBEE, stop:1 #FFCDD2);
                border: 2px solid #F44336;
                border-radius: 6px;
                color: #C62828;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #EF9A9A, stop:1 #E57373);
                transform: translateY(-1px);
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E57373, stop:1 #F44336);
                transform: translateY(1px);
            }
        """)
        log_header_layout.addWidget(self.log_clear_button)
        
        log_layout.addLayout(log_header_layout)
        
        # 로그 출력 영역 (2025 스타일 TextEdit)
        self.log_output = TextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setVisible(False)  # 초기에는 숨김
        self.log_output.setMaximumHeight(280)  # 조금 더 높게
        self.log_output.setStyleSheet("""
            TextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FAFAFA, stop:1 #F5F5F5);
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
                color: #212121;
            }
            TextEdit:focus {
                border: 2px solid #2196F3;
                background: white;
            }
        """)
        log_layout.addWidget(self.log_output)
        
        # 로그 표시 상태 변수
        self.log_visible = False
        
        layout.addWidget(log_card)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "다운로드 폴더 선택")
        if folder:
            self.download_folder_path = folder
            self.folder_path_input.setText(folder)
            self.update_log(f"[INFO] 다운로드 폴더 설정: {folder}")

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        if not self.download_folder_path:
            self.update_log("[ERROR] 다운로드 폴더를 먼저 선택해주세요.")
            return

        self.log_output.clear()
        
        # 통계 리셋
        if hasattr(self, 'stats_widget'):
            self.stats_widget.reset_daily_stats()
        
        if os.path.exists(self.stop_flag_path):
            os.remove(self.stop_flag_path)

        self.is_monitoring = True
        self.toggle_button.setText("⏹️ 자동화 중지")
        self.toggle_button.setObjectName("stopButton")
        self.setStyleSheet(self.styleSheet()) # Refresh stylesheet for ID
        self.browse_button.setEnabled(False)
        self.password_input.setEnabled(False)
        
        # 상태 업데이트
        self.status_label.setText("실행 중")
        self.status_label.setStyleSheet("color: #28a745; font-size: 16px; font-weight: bold;")

        # 암호 값 가져오기
        password = self.password_input.text().strip() if self.password_input.text().strip() else "1234"
        
        self.worker = Worker(self.download_folder_path, password)
        self.worker.output_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.on_monitoring_finished)
        self.worker.start()

    def stop_monitoring(self):
        if not self.is_monitoring:
            return
        self.update_log("[INFO] 자동화 중지를 요청합니다...")
        
        # Worker 스레드에 중지 신호 전송
        try:
            with open(self.stop_flag_path, 'w') as f:
                f.write('stop')
        except Exception as e:
            self.update_log(f"[ERROR] 중지 신호 전송 실패: {e}")
        
        self.toggle_button.setEnabled(False)
        
        # 상태 업데이트
        self.status_label.setText("중지 중")
        self.status_label.setStyleSheet("color: #ffc107; font-size: 16px; font-weight: bold;")
        
        # 타임아웃과 함께 Worker 종료 대기 (안전한 방식)
        if self.worker and self.worker.isRunning():
            # 스레드가 5초 안에 정상적으로 종료되기를 기다림
            if not self.worker.wait(5000):  
                self.update_log("[WARNING] 자동화 스레드가 5초 내에 정상적으로 종료되지 않았습니다. 강제 종료를 시도합니다.")
                self.worker.terminate()
                # 강제 종료 후, on_monitoring_finished가 호출되지 않을 수 있으므로 수동 호출
                QTimer.singleShot(1000, self.on_monitoring_finished)
            else:
                self.update_log("[INFO] 자동화 스레드가 정상적으로 중지되었습니다.")
                # 정상 종료 시 finished_signal이 on_monitoring_finished를 호출하지만,
                # 만약을 위해 상태를 확인하고 직접 호출
                if self.is_monitoring:
                    self.on_monitoring_finished()

    

    def update_log(self, text):
        self.log_output.append(text)
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())
        
        # 실시간 통계 업데이트
        if hasattr(self, 'stats_widget'):
            self.stats_widget.parse_log_message(text)
    
    def toggle_log_display(self):
        """로그 표시/숨기기 토글 (Material Design)"""
        self.log_visible = not self.log_visible
        
        if self.log_visible:
            # 로그 보이기
            self.log_output.setVisible(True)
            self.log_clear_button.setVisible(True)
            self.log_toggle_button.setText("📋 실행 로그 숨기기")
            self.log_toggle_button.setIcon(MaterialIcon('expand_less'))
        else:
            # 로그 숨기기
            self.log_output.setVisible(False)
            self.log_clear_button.setVisible(False)
            self.log_toggle_button.setText("📋 실행 로그 보기")
            self.log_toggle_button.setIcon(MaterialIcon('expand_more'))
    
    def clear_log(self):
        """로그 지우기"""
        reply = QMessageBox.question(
            self, 
            "로그 지우기", 
            "모든 로그를 지우시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log_output.clear()
            self.update_log("[INFO] 로그가 지워졌습니다.")


    def on_monitoring_finished(self):
        self.update_log("[INFO] 자동화 프로세스가 종료되었습니다.")
        self.is_monitoring = False
        
        # Worker 정리
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
        self.toggle_button.setText("🎆 자동화 시작")
        self.toggle_button.setObjectName("")
        self.setStyleSheet(self.styleSheet()) # Refresh stylesheet
        self.toggle_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.password_input.setEnabled(True)
        
        # 상태 업데이트
        self.status_label.setText("대기 중")
        self.status_label.setStyleSheet("color: #666; font-size: 16px; font-weight: bold;")
        
        if os.path.exists(self.stop_flag_path):
            os.remove(self.stop_flag_path)
    
    def toggle_password_visibility(self):
        """암호 표시/숨기기 토글 (Material Design)"""
        if self.password_input.echoMode() == LineEdit.Password:
            self.password_input.setEchoMode(LineEdit.Normal)
            self.show_password_button.setIcon(MaterialIcon('visibility_off'))
            self.show_password_button.setToolTip("암호 숨기기")
        else:
            self.password_input.setEchoMode(LineEdit.Password)
            self.show_password_button.setIcon(MaterialIcon('visibility'))
            self.show_password_button.setToolTip("암호 표시")

    def manual_process(self):
        """작업폴더의 미완료 파일들을 수동으로 처리 또는 중지"""
        if self.is_manual_processing:
            # 수동 처리 중지
            self.stop_manual_process()
            return
        
        if not self.download_folder_path:
            self.update_log("[ERROR] 다운로드 폴더를 먼저 선택해주세요.")
            return
        
        if self.is_monitoring:
            self.update_log("[WARNING] 자동화 실행 중에는 수동 처리를 할 수 없습니다.")
            return
        
        # 수동 처리 시작
        self.start_manual_process()
    
    def start_manual_process(self):
        """수동 처리 시작"""
        self.log_output.clear()
        
        # 통계 리셋
        if hasattr(self, 'stats_widget'):
            self.stats_widget.reset_daily_stats()
        
        if os.path.exists(self.stop_flag_path):
            os.remove(self.stop_flag_path)
        
        self.is_manual_processing = True
        self.manual_process_button.setText("⏹️ 처리 중지")
        self.manual_process_button.setStyleSheet("""
            PushButton {
                font-size: 16px;
                font-weight: 700;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F44336, stop:1 #C62828);
                border: none;
                border-radius: 28px;
                color: white;
                padding: 16px 32px;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EF5350, stop:1 #D32F2F);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
            }
        """)  # 2025 스타일 빨간색
        self.toggle_button.setEnabled(False)  # 자동화 버튼 비활성화
        self.reward_button.setEnabled(False)  # 리워드 버튼 비활성화
        
        # 상태 업데이트
        self.status_label.setText("수동 처리 중")
        self.status_label.setStyleSheet("color: #ffc107; font-size: 16px; font-weight: bold;")
        
        self.update_log("[INFO] 작업폴더의 미완료 파일들을 수동 처리합니다...")
        
        # Worker 스레드로 수동 처리 실행
        self.manual_worker = ManualProcessWorker(self.download_folder_path, self.password_input.text().strip() or "1234")
        self.manual_worker.output_signal.connect(self.update_log)
        self.manual_worker.finished_signal.connect(self.on_manual_process_finished)
        self.manual_worker.start()
    
    def stop_manual_process(self):
        """수동 처리 중지"""
        if not self.is_manual_processing:
            return
        
        self.update_log("[INFO] 수동 처리 중지를 요청합니다...")
        
        # Worker 스레드에 중지 신호 전송
        try:
            with open(self.stop_flag_path, 'w') as f:
                f.write('stop')
        except Exception as e:
            self.update_log(f"[ERROR] 중지 신호 전송 실패: {e}")
        
        self.manual_process_button.setEnabled(False)
        self.manual_process_button.setText("⏳ 중지 중...")
        
        # 상태 업데이트
        self.status_label.setText("중지 중")
        self.status_label.setStyleSheet("color: #ffc107; font-size: 16px; font-weight: bold;")
        
        # 타임아웃과 함께 Worker 종료 대기 (안전한 방식)
        if hasattr(self, 'manual_worker') and self.manual_worker and self.manual_worker.isRunning():
            if not self.manual_worker.wait(5000): # 5초 대기
                self.update_log("[WARNING] 수동 처리 스레드가 5초 내에 정상적으로 종료되지 않았습니다. 강제 종료를 시도합니다.")
                self.manual_worker.terminate()
                QTimer.singleShot(1000, self.on_manual_process_finished) # 강제 종료 후 정리
            else:
                self.update_log("[INFO] 수동 처리 스레드가 정상적으로 중지되었습니다.")
                if self.is_manual_processing:
                    self.on_manual_process_finished()

    
    
    def on_manual_process_finished(self):
        """수동 처리 완료 시 호출"""
        # ManualProcessWorker 정리
        if hasattr(self, 'manual_worker') and self.manual_worker:
            self.manual_worker.deleteLater()
            self.manual_worker = None
        
        # 상태 초기화
        self.is_manual_processing = False
        
        # 버튼 및 UI 복원
        self.manual_process_button.setEnabled(True)
        self.manual_process_button.setText("📁 작업폴더 처리")
        self.manual_process_button.setStyleSheet("""
            PushButton {
                font-size: 16px;
                font-weight: 600;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF9800, stop:1 #F57C00);
                border: none;
                border-radius: 28px;
                color: white;
                padding: 16px 32px;
            }
            PushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFB74D, stop:1 #FB8C00);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
            }
            PushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F57C00, stop:1 #E65100);
                transform: translateY(0px);
            }
        """)  # 2025 스타일 원래 색상 복원
        self.toggle_button.setEnabled(True)  # 자동화 버튼 활성화
        self.reward_button.setEnabled(True)  # 리워드 버튼 활성화
        
        # 상태 업데이트
        self.status_label.setText("대기 중")
        self.status_label.setStyleSheet("color: #666; font-size: 16px; font-weight: bold;")
        
        # stop.flag 파일 정리
        if os.path.exists(self.stop_flag_path):
            os.remove(self.stop_flag_path)
        
        self.update_log("[INFO] 수동 처리가 완료되었습니다.")

    def open_reward_manager(self):
        """리워드 관리 팝업창 열기"""
        if self.is_monitoring:
            self.update_log("[WARNING] 자동화 실행 중에는 리워드 설정을 할 수 없습니다.")
            return
        
        if self.is_manual_processing:
            self.update_log("[WARNING] 수동 처리 중에는 리워드 설정을 할 수 없습니다.")
            return
        
        try:
            dialog = RewardManagerDialog(self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.update_log("[INFO] 리워드 설정이 저장되었습니다.")
            
        except Exception as e:
            self.update_log(f"[ERROR] 리워드 관리 창을 여는 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", f"리워드 관리 창을 여는 중 오류가 발생했습니다:\n{e}")

    def open_purchase_manager(self):
        """가구매 관리 팝업창 열기"""
        if self.is_monitoring:
            self.update_log("[WARNING] 자동화 실행 중에는 가구매 설정을 할 수 없습니다.")
            return
        
        if self.is_manual_processing:
            self.update_log("[WARNING] 수동 처리 중에는 가구매 설정을 할 수 없습니다.")
            return
        
        try:
            dialog = PurchaseManagerDialog(self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                self.update_log("[INFO] 가구매 설정이 저장되었습니다.")
            
        except Exception as e:
            self.update_log(f"[ERROR] 가구매 관리 창을 여는 중 오류 발생: {e}")
            QMessageBox.critical(self, "오류", f"가구매 관리 창을 여는 중 오류가 발생했습니다:\n{e}")

    def closeEvent(self, event):
        if self.is_monitoring or self.is_manual_processing:
            self.update_log("[INFO] 프로그램 종료 중...")
            
            # 자동화 중지
            if self.is_monitoring:
                self.stop_monitoring()
                if self.worker and self.worker.isRunning():
                    if not self.worker.wait(2000):  # 2초 타임아웃
                        self.worker.terminate()
                        if not self.worker.wait(1000):  # 1초 추가 대기
                            self.worker.kill()  # 완전 강제 종료
            
            # 수동 처리 중지
            if self.is_manual_processing:
                self.stop_manual_process()
                if hasattr(self, 'manual_worker') and self.manual_worker and self.manual_worker.isRunning():
                    if not self.manual_worker.wait(2000):  # 2초 타임아웃
                        self.manual_worker.terminate()
                        if not self.manual_worker.wait(1000):  # 1초 추가 대기
                            self.manual_worker.kill()  # 완전 강제 종료
        
        # stop.flag 파일 정리
        if os.path.exists(self.stop_flag_path):
            try:
                os.remove(self.stop_flag_path)
            except:
                pass  # 파일 삭제 실패해도 프로그램 종료 진행
                
        event.accept()

if __name__ == '__main__':
    # This is important for multiprocessing support in frozen apps
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    ex = DesktopApp()
    ex.show()
    sys.exit(app.exec_())
