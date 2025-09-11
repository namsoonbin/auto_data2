# -*- coding: utf-8 -*-
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
    QGraphicsDropShadowEffect, QSizePolicy, QDialogButtonBox
)
from PySide6.QtCore import QThread, Signal, Qt, QDate, QTimer, QSettings
from PySide6.QtGui import QColor, QIcon, QCursor

# Try to import qtawesome for icons
QTAWESOME_AVAILABLE = False
try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    pass

# Import the existing modules
from modules import config, file_handler, report_generator, weekly_reporter

# --- UI Styling Classes ---

class MaterialColors:
    PRIMARY = "#2563eb"
    SUCCESS = "#059669"
    WARNING = "#ea580c"
    ERROR = "#dc2626"
    DARK_BG = "#1a1a1a"
    DARK_TEXT = "#ffffff"

class AppleStyleButton(QPushButton):
    def __init__(self, text, icon_name=None, color=MaterialColors.PRIMARY, parent=None):
        super().__init__(text, parent)
        if icon_name and QTAWESOME_AVAILABLE:
            try:
                icon = qta.icon(icon_name, color='white')
                self.setIcon(icon)
            except Exception:
                pass

        self.setMinimumSize(100, 38)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        c = QColor(color)
        self.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: white; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {c.lighter(110).name()}; }}
            QPushButton:pressed {{ background-color: {c.darker(110).name()}; }}
            QPushButton:disabled {{ background-color: #E0E0E0; color: #999999; }}
        """)

class ModernLogViewer(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(200)
        self.setStyleSheet(f'''
            QTextEdit {{ background-color: {MaterialColors.DARK_BG}; color: {MaterialColors.DARK_TEXT}; font-family: 'Consolas', monospace; font-size: 12px; border: 1px solid #374151; border-radius: 8px; padding: 12px; }}
        ''')

class ModernDataCard(QFrame):
    def __init__(self, title, value, icon_name, color=MaterialColors.PRIMARY, tooltip=""):
        super().__init__()
        self.color = color
        self.setMinimumHeight(160)
        self.setMaximumHeight(200)
        if tooltip:
            self.setToolTip(tooltip)

        # 확실하게 보이는 스타일 적용
        self.setStyleSheet(f"""
            ModernDataCard {{
                background-color: #FFFFFF;
                border: 3px solid #DDDDDD;
                border-radius: 10px;
                padding: 15px;
            }}
            ModernDataCard:hover {{
                border-color: {self.color};
                background-color: #F5F5F5;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 헤더 (아이콘 + 제목)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # 크고 명확한 이모지 아이콘
        icon_map = {
            "fa5s.file-alt": "📄",
            "fa5s.dollar-sign": "💰", 
            "fa5s.chart-line": "📈",
            "fa5s.exclamation-triangle": "⚠️"
        }
        icon_text = icon_map.get(icon_name, "📊")
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("""
            font-size: 24px;
            padding: 0;
            margin: 0;
        """)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: #333333;
            margin: 0;
            padding: 0;
            background-color: transparent;
        """)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 값 표시 - 매우 명확하게
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #000000;
            margin: 0;
            padding: 8px 0;
            background-color: transparent;
        """)
        self.value_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def update_value(self, new_value):
        self.value_label.setText(str(new_value))

# --- Worker Threads ---

class ModernWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)
    stats_signal = Signal(dict)  # 통계 업데이트 시그널 추가

    def __init__(self, download_folder, password="1234"):
        super().__init__()
        self.download_folder = download_folder
        self.password = password

    def run(self):
        try:
            config.DOWNLOAD_DIR = self.download_folder
            config.ORDER_FILE_PASSWORD = self.password
            self.output_signal.emit("[INFO] 자동화 시작!")
            file_handler.start_monitoring()
            
            # 모니터링이 완료되면 통계 수집
            self.collect_and_send_stats()
            
        except Exception as e:
            self.error_signal.emit(f"[ERROR] 모니터링 중 오류: {str(e)}")
        finally:
            self.finished_signal.emit()

    def collect_and_send_stats(self):
        """통계 정보를 수집해서 시그널로 전송"""
        try:
            import glob
            import pandas as pd
            
            # 처리된 리포트 파일들 찾기 (보관함에서)
            archive_dir = config.get_report_archive_dir()
            if not os.path.exists(archive_dir):
                return
                
            report_files = glob.glob(os.path.join(archive_dir, '*_통합_리포트_*.xlsx'))
            
            total_files = len(report_files)
            total_sales = 0
            total_profit = 0
            
            # 최근 파일들만 읽어서 통계 계산 (성능을 위해 최근 10개만)
            recent_files = sorted(report_files, key=os.path.getmtime, reverse=True)[:10]
            
            for report_file in recent_files:
                try:
                    df = pd.read_excel(report_file, sheet_name='정리된 데이터')
                    if '매출' in df.columns:
                        total_sales += df['매출'].sum()
                    if '순이익' in df.columns:
                        total_profit += df['순이익'].sum()
                except Exception:
                    continue
            
            # 통계 정보 전송
            stats = {
                'files': f"{total_files}개",
                'sales': f"₩{total_sales:,.0f}",
                'profit': f"₩{total_profit:,.0f}"
            }
            self.stats_signal.emit(stats)
            
        except Exception as e:
            self.output_signal.emit(f"[DEBUG] 통계 수집 중 오류: {e}")

class ModernManualWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)  # 오류 전용 시그널 추가
    stats_signal = Signal(dict)  # 통계 업데이트 시그널 추가
    
    def __init__(self, download_folder, password="1234"):
        super().__init__()
        self.download_folder = download_folder
        self.password = password

    def run(self):
        try:
            config.DOWNLOAD_DIR = self.download_folder
            config.ORDER_FILE_PASSWORD = self.password
            self.output_signal.emit("[INFO] 🔄 작업폴더 수동 처리 시작...")
            
            # 1단계: 작업폴더에 있는 파일들로 개별 리포트 생성
            self.output_signal.emit("[INFO] 📊 1단계: 작업폴더 파일들로 개별 리포트 생성 중...")
            from modules import report_generator
            processed_groups = report_generator.generate_individual_reports()
            
            if processed_groups:
                self.output_signal.emit(f"[INFO] ✅ 1단계 완료: {len(processed_groups)}개 그룹 처리됨")
            else:
                self.output_signal.emit("[INFO] ⚠️ 1단계: 처리할 파일이 없거나 리포트 생성 실패")
            
            # 2단계: 최종 통합 처리 (일일/주간 리포트 생성 및 파일 정리)
            self.output_signal.emit("[INFO] 🏁 2단계: 최종 통합 처리 중...")
            file_handler.finalize_all_processing()
            self.output_signal.emit("[INFO] ✅ 2단계: 최종 통합 처리 완료")
            
            self.output_signal.emit("[INFO] 🎯 작업폴더 처리 완료!")
            
            # 통계 정보 수집 및 전송
            self.collect_and_send_stats()
            
        except Exception as e:
            error_msg = f"[ERROR] 수동 처리 중 오류: {str(e)}"
            self.output_signal.emit(error_msg)
            self.error_signal.emit(error_msg)  # 오류 시그널 발생
            import traceback
            self.output_signal.emit(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        finally:
            self.finished_signal.emit()

    def collect_and_send_stats(self):
        """통계 정보를 수집해서 시그널로 전송"""
        try:
            import glob
            import pandas as pd
            
            # 처리된 리포트 파일들 찾기
            processing_dir = config.get_processing_dir()
            report_files = glob.glob(os.path.join(processing_dir, '*_통합_리포트_*.xlsx'))
            
            total_files = len(report_files)
            total_sales = 0
            total_profit = 0
            
            # 각 리포트 파일에서 통계 추출
            for report_file in report_files:
                try:
                    df = pd.read_excel(report_file, sheet_name='정리된 데이터')
                    if '매출' in df.columns:
                        total_sales += df['매출'].sum()
                    if '순이익' in df.columns:
                        total_profit += df['순이익'].sum()
                except Exception:
                    continue
            
            # 통계 정보 전송
            stats = {
                'files': f"{total_files}개",
                'sales': f"₩{total_sales:,.0f}",
                'profit': f"₩{total_profit:,.0f}"
            }
            self.stats_signal.emit(stats)
            
        except Exception as e:
            self.output_signal.emit(f"[DEBUG] 통계 수집 중 오류: {e}")

class WeeklyWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)  # 오류 전용 시그널 추가
    stats_signal = Signal(dict)  # 통계 업데이트 시그널 추가

    def __init__(self, start_date, end_date, download_folder):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.download_folder = download_folder

    def run(self):
        try:
            self.output_signal.emit(f"[INFO] 📅 주간 리포트 생성 시작...")
            
            # config 전역 상태 변경 대신 매개변수로 전달
            success = weekly_reporter.create_weekly_report(
                self.start_date, 
                self.end_date, 
                self.download_folder
            )
            
            if success:
                self.output_signal.emit("[INFO] ✅ 주간 리포트 생성 완료!")
            else:
                error_msg = "[ERROR] 주간 리포트 생성 실패 - 로그를 확인해주세요."
                self.output_signal.emit(error_msg)
                self.error_signal.emit(error_msg)  # 오류 시그널 발생
                
        except Exception as e:
            error_msg = f"[ERROR] 주간 리포트 생성 중 예외 발생: {str(e)}"
            self.output_signal.emit(error_msg)
            self.error_signal.emit(error_msg)  # 오류 시그널 발생
        finally:
            self.finished_signal.emit()

# --- Dialog Classes ---

class WeeklyReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 주간 리포트 생성")
        self.setFixedSize(400, 200)
        layout = QVBoxLayout(self)
        
        # 설명 레이블 추가
        info_label = QLabel("생성할 주간 리포트의 날짜 범위를 선택하세요.")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        form_layout = QGridLayout()
        
        # 날짜 선택기 설정
        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setMaximumDate(QDate.currentDate())
        
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setMaximumDate(QDate.currentDate())
        
        # 날짜 변경 시 검증
        self.start_date_edit.dateChanged.connect(self.validate_date_range)
        self.end_date_edit.dateChanged.connect(self.validate_date_range)
        
        form_layout.addWidget(QLabel("시작 날짜:"), 0, 0)
        form_layout.addWidget(self.start_date_edit, 0, 1)
        form_layout.addWidget(QLabel("종료 날짜:"), 1, 0)
        form_layout.addWidget(self.end_date_edit, 1, 1)
        layout.addLayout(form_layout)
        
        # 경고 메시지 레이블
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-size: 11px; margin: 5px 0px;")
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        # 버튼
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # 초기 검증
        self.validate_date_range()

    def validate_date_range(self):
        """날짜 범위 검증"""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        if start_date > end_date:
            self.warning_label.setText("⚠️ 시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
            self.warning_label.setStyleSheet("color: red; font-size: 11px; margin: 5px 0px;")
            self.warning_label.show()
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            return False
        elif start_date == end_date:
            self.warning_label.setText("💡 동일한 날짜로 설정되었습니다. 해당 날짜의 리포트만 생성됩니다.")
            self.warning_label.setStyleSheet("color: #ff8800; font-size: 11px; margin: 5px 0px;")
            self.warning_label.show()
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            return True
        else:
            days_diff = start_date.daysTo(end_date) + 1
            if days_diff > 31:
                self.warning_label.setText(f"⚠️ 너무 긴 기간입니다 ({days_diff}일). 31일 이하로 설정해주세요.")
                self.warning_label.setStyleSheet("color: red; font-size: 11px; margin: 5px 0px;")
                self.warning_label.show()
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                return False
            else:
                self.warning_label.hide()
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                return True

    def validate_and_accept(self):
        """확인 버튼 클릭 시 최종 검증"""
        if self.validate_date_range():
            self.accept()

    def get_dates(self):
        """검증된 날짜 반환"""
        if self.validate_date_range():
            return (
                self.start_date_edit.date().toString("yyyy-MM-dd"), 
                self.end_date_edit.date().toString("yyyy-MM-dd")
            )
        else:
            return None, None

class ErrorDetailsDialog(QDialog):
    def __init__(self, error_messages, parent=None):
        super().__init__(parent)
        self.error_messages = error_messages
        self.setWindowTitle("🚨 오류 상세 정보")
        self.setFixedSize(800, 600)
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 헤더 정보
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"총 {len(self.error_messages)}개의 오류가 발생했습니다")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #dc3545; margin: 10px 0px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 클리어 버튼
        clear_btn = QPushButton("오류 기록 지우기")
        clear_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; font-weight: bold; padding: 6px 12px; border: none; border-radius: 4px; } QPushButton:hover { background-color: #545b62; }")
        clear_btn.clicked.connect(self.clear_errors)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # 오류 테이블
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(3)
        self.error_table.setHorizontalHeaderLabels(['시간', '유형', '오류 메시지'])
        
        # 테이블 스타일링
        self.error_table.setAlternatingRowColors(True)
        self.error_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 컬럼 크기 조정
        header = self.error_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 유형
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # 메시지
        
        self.populate_table()
        layout.addWidget(self.error_table)
        
        # 통계 정보
        stats_layout = QHBoxLayout()
        error_types = {}
        for error in self.error_messages:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        stats_text = " | ".join([f"{error_type}: {count}개" for error_type, count in error_types.items()])
        stats_label = QLabel(f"오류 유형별 통계: {stats_text}")
        stats_label.setStyleSheet("font-size: 12px; color: #666; padding: 8px;")
        stats_layout.addWidget(stats_label)
        layout.addLayout(stats_layout)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; font-weight: bold; padding: 10px 20px; border: none; border-radius: 6px; min-width: 80px; } QPushButton:hover { background-color: #0056b3; }")
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def populate_table(self):
        """테이블에 오류 데이터 채우기"""
        self.error_table.setRowCount(len(self.error_messages))
        
        for row, error in enumerate(reversed(self.error_messages)):  # 최신 오류가 위에 오도록
            # 시간
            time_item = QTableWidgetItem(error['timestamp'])
            time_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.error_table.setItem(row, 0, time_item)
            
            # 유형 (색상으로 구분)
            type_item = QTableWidgetItem(error['type'])
            type_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            
            # 유형별 색상 설정
            if error['type'] == '파일 오류':
                type_item.setBackground(QColor("#fff3cd"))
            elif error['type'] == '권한 오류':
                type_item.setBackground(QColor("#f8d7da"))
            elif error['type'] == '메모리 오류':
                type_item.setBackground(QColor("#d1ecf1"))
            elif error['type'] == '네트워크 오류':
                type_item.setBackground(QColor("#d4edda"))
            else:
                type_item.setBackground(QColor("#e2e3e5"))
            
            self.error_table.setItem(row, 1, type_item)
            
            # 메시지
            message_item = QTableWidgetItem(error['message'])
            message_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            message_item.setToolTip(error['message'])  # 툴팁으로 전체 메시지 보기
            self.error_table.setItem(row, 2, message_item)
    
    def clear_errors(self):
        """오류 기록 삭제 확인"""
        reply = QMessageBox.question(
            self, 
            "오류 기록 삭제", 
            "모든 오류 기록을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 부모 앱의 오류 기록 삭제
            if self.parent():
                self.parent().error_messages.clear()
                self.parent().error_count = 0
                self.parent().error_card.update_value("0개")
            
            self.accept()
            QMessageBox.information(self, "삭제 완료", "모든 오류 기록이 삭제되었습니다.")

class ModernRewardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('💰 일일 리워드 관리')
        self.setFixedSize(950, 750)
        self.setModal(True)
        
        self.reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
        self.margin_file = config.MARGIN_FILE
        self.all_rewards_data = {'rewards': []}
        self.products_df = pd.DataFrame()

        # 초기화 완료 플래그
        self._initialization_complete = False

        self.initUI()
        self.load_data_sources()
        # 초기화 완료 플래그 설정
        self._initialization_complete = True
        # 초기 데이터 로드
        self.load_initial_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 최소화된 헤더 섹션
        header_widget = QWidget()
        header_widget.setStyleSheet("background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 8px;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title_label = QLabel("일일 리워드 설정")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #E65100; margin: 0;")
        subtitle_label = QLabel("상품별 리워드 금액을 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("font-size: 12px; color: #6c757d; margin-top: 4px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_widget)
        
        # 스크롤 가능한 컨텐츠 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 날짜 선택 및 복사
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit(QDate.currentDate()); self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_rewards_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit(QDate.currentDate().addDays(-1)); self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        self.copy_button = QPushButton("설정 불러오기"); self.copy_button.clicked.connect(self.copy_rewards)
        date_layout.addWidget(self.copy_button, 1, 2)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # 검색 및 일괄 설정
        control_group = QGroupBox("검색 및 일괄 설정")
        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("검색:"), 0, 0)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("상품명으로 검색...")
        self.search_box.textChanged.connect(self.filter_products)
        control_layout.addWidget(self.search_box, 0, 1, 1, 2)
        self.select_all_checkbox = QCheckBox("전체 선택/해제"); self.select_all_checkbox.clicked.connect(self.toggle_all_selection)
        control_layout.addWidget(self.select_all_checkbox, 1, 0)
        self.selected_count_label = QLabel("선택됨: 0개")
        control_layout.addWidget(self.selected_count_label, 1, 1)
        control_layout.addWidget(QLabel("선택된 항목에 적용:"), 2, 0)
        bulk_layout = QHBoxLayout()
        self.bulk_reward = QSpinBox()
        self.bulk_reward.setRange(0, 999999)
        self.bulk_reward.setSingleStep(1000)  # 1000원 단위로 증감
        self.bulk_reward.setSuffix(" 원")
        # 기본 스타일만 적용 (가구매 관리처럼)
        self.bulk_reward.setMinimumHeight(32)
        bulk_layout.addWidget(self.bulk_reward)
        
        # 빠른 설정 버튼들
        quick_buttons = [("0원", 0), ("3000원", 3000), ("6000원", 6000), ("9000원", 9000)]
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda checked, v=value: self.bulk_reward.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        self.apply_selected_button = QPushButton("선택된 항목에 적용"); self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 상품 테이블
        self.reward_table = QTableWidget()
        self.reward_table.setColumnCount(5)
        self.reward_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '옵션정보', '리워드 금액'])
        self.reward_table.setMinimumHeight(350)  # 높이 약간 줄여서 버튼 공간 확보
        header = self.reward_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 옵션정보
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 리워드 금액
        layout.addWidget(self.reward_table)
        
        # 스크롤 영역 설정 (버튼들은 제외)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 하단 고정 버튼들 (스크롤 영역 밖에 배치)
        button_widget = QWidget()
        button_widget.setStyleSheet("background: #f8f9fa; border-top: 1px solid #dee2e6; padding: 10px;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        self.save_button = QPushButton("💾 저장")
        self.save_button.clicked.connect(self.save_rewards)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # 하단 고정 버튼 위젯을 메인 레이아웃에 추가
        main_layout.addWidget(button_widget)
    
    def load_initial_data(self):
        """UI 완성 후 초기 데이터 로드"""
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            self.load_rewards_for_date(QDate.currentDate())

    def load_data_sources(self):
        try:
            if os.path.exists(self.margin_file):
                df = pd.read_excel(self.margin_file, engine='openpyxl')
                df = df.rename(columns={'상품번호': '상품ID'})
                if '대표옵션' in df.columns:
                    df['대표옵션'] = df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                    df = df[df['대표옵션'] == True]
                # 옵션정보 컬럼도 포함하여 products_df 생성
                columns_to_keep = ['상품ID', '상품명']
                if '옵션정보' in df.columns:
                    columns_to_keep.append('옵션정보')
                self.products_df = df[columns_to_keep].drop_duplicates().sort_values(by='상품명')
            if os.path.exists(self.reward_file):
                with open(self.reward_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.all_rewards_data = json.loads(content) if content else {'rewards': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스 로드 오류: {e}")

    def normalize_product_id(self, product_id):
        """product_id 정규화 (.0 제거)"""
        product_id_str = str(product_id)
        if product_id_str.endswith('.0'):
            return product_id_str[:-2]
        return product_id_str
    
    def safe_get_option_info(self, product):
        """상품 데이터에서 옵션정보를 안전하게 가져오기"""
        import pandas as pd
        option_info = product.get('옵션정보', '')
        
        # pandas NA 값 처리
        if pd.isna(option_info):
            return ''
        
        # 문자열로 변환하고 공백 제거
        return str(option_info).strip()
    
    def find_reward_value(self, product_id, reward_map, option_info=''):
        """product_id와 옵션정보에 대한 리워드 값 찾기"""
        clean_id = self.normalize_product_id(product_id)
        dotted_id = clean_id + '.0'
        
        # 3-tuple 키로 옵션별 설정 확인
        option_key = (clean_id, option_info)
        dotted_option_key = (dotted_id, option_info)
        
        # 옵션별 설정이 있으면 우선 사용
        if option_key in reward_map:
            return reward_map[option_key]
        if dotted_option_key in reward_map:
            return reward_map[dotted_option_key]
        
        # 기존 방식 (하위 호환성)
        return reward_map.get(clean_id, reward_map.get(dotted_id, 0))
    
    def clear_table_widgets(self):
        """테이블 위젯들을 안전하게 정리"""
        try:
            for row in range(self.reward_table.rowCount()):
                # 체크박스 정리
                checkbox = self.reward_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.deleteLater()
                # 스핀박스 정리
                spinbox = self.reward_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.deleteLater()
            
            # 테이블 내용 클리어
            self.reward_table.clearContents()
        except Exception as e:
            import logging
            logging.error(f"리워드 테이블 위젯 정리 중 오류: {e}")

    def load_rewards_for_date(self, q_date):
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        # 기존 위젯들 정리
        self.clear_table_widgets()
        
        # 모든 형식의 product_id를 포함하는 reward_map 생성
        reward_map = {}
        for e in self.all_rewards_data.get('rewards', []):
            if e.get('start_date') == target_date_str:
                product_id = str(e['product_id'])
                option_info = e.get('option_info', '')
                
                # 옵션별 설정이 있으면 3-tuple 키로 저장
                if option_info:
                    reward_map[(product_id, option_info)] = e['reward']
                else:
                    # 기존 방식 (하위 호환성)
                    reward_map[product_id] = e['reward']
        
        self.reward_table.setRowCount(len(self.products_df))
        
        for row, (_, product) in enumerate(self.products_df.iterrows()):
            product_id = str(product['상품ID'])
            option_info = self.safe_get_option_info(product)
            
            # 체크박스 생성 및 이벤트 연결
            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_selected_count)
            self.reward_table.setCellWidget(row, 0, checkbox)
            
            self.reward_table.setItem(row, 1, QTableWidgetItem(product_id))
            self.reward_table.setItem(row, 2, QTableWidgetItem(str(product['상품명'])))
            self.reward_table.setItem(row, 3, QTableWidgetItem(option_info))
            
            # 스핀박스 생성 (1000원 단위, 개선된 UI)
            spinbox = QSpinBox()
            spinbox.setRange(0, 999999)
            spinbox.setSingleStep(1000)  # 1000원 단위로 증감
            spinbox.setSuffix(" 원")
            # 호환성을 위해 두 형식 모두 확인
            reward_value = self.find_reward_value(product_id, reward_map, option_info)
            spinbox.setValue(reward_value)
            # 기본 스타일만 적용 (가구매 관리처럼)
            spinbox.setMinimumHeight(28)
            self.reward_table.setCellWidget(row, 4, spinbox)
        
        self.filter_products()
        self.update_selected_count()

    def copy_rewards(self):
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        reward_map = {}
        
        # 리워드 데이터에서 해당 날짜 설정 찾기
        for entry in self.all_rewards_data.get('rewards', []):
            if entry.get('start_date') == source_date_str:
                product_id = str(entry['product_id'])
                reward_map[product_id] = entry['reward']
        
        if not reward_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 리워드 설정이 없습니다.")
            return
            
        # 현재 테이블에 적용
        applied_count = 0
        for row in range(self.reward_table.rowCount()):
            product_id_item = self.reward_table.item(row, 1)
            spinbox = self.reward_table.cellWidget(row, 3)
            if product_id_item and spinbox:
                product_id = product_id_item.text()
                # 호환성을 위해 두 형식 모두 확인
                reward_value = self.find_reward_value(product_id, reward_map)
                if reward_value > 0:  # 리워드 값이 있는 경우만 적용
                    spinbox.setValue(reward_value)
                    applied_count += 1
        
        QMessageBox.information(self, "복사 완료", f"{applied_count}개 상품의 리워드 설정을 복사했습니다.")

    def toggle_all_selection(self):
        is_checked = self.select_all_checkbox.isChecked()
        for row in range(self.reward_table.rowCount()):
            if not self.reward_table.isRowHidden(row):
                checkbox = self.reward_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(is_checked)
        self.update_selected_count()

    def apply_to_selected(self):
        """선택된 항목에 일괄 적용 (예외 처리 강화)"""
        try:
            bulk_value = self.bulk_reward.value()
            applied_count = 0
            for row in range(self.reward_table.rowCount()):
                checkbox = self.reward_table.cellWidget(row, 0)
                spinbox = self.reward_table.cellWidget(row, 4)
                if checkbox and checkbox.isChecked() and spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
            
            if applied_count > 0:
                QMessageBox.information(self, "적용 완료", f"{applied_count}개 상품에 {bulk_value}원 리워드를 적용했습니다.")
            else:
                QMessageBox.warning(self, "선택 없음", "적용할 상품을 먼저 선택해주세요.")
        except Exception as e:
            import logging
            logging.error(f"리워드 일괄 적용 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"일괄 적용 중 오류가 발생했습니다:\n{str(e)}")

    def update_selected_count(self):
        """선택된 항목 수 업데이트 (예외 처리 강화)"""
        try:
            selected_count = 0
            for row in range(self.reward_table.rowCount()):
                if not self.reward_table.isRowHidden(row):
                    checkbox = self.reward_table.cellWidget(row, 0)
                    if checkbox and checkbox.isChecked():
                        selected_count += 1
            
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText(f"선택됨: {selected_count}개")
            
            if hasattr(self, 'apply_selected_button'):
                self.apply_selected_button.setEnabled(selected_count > 0)
        except Exception as e:
            import logging
            logging.error(f"리워드 선택 개수 업데이트 중 오류: {e}")
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText("선택됨: 오류")

    def filter_products(self):
        search_text = self.search_box.text().lower()
        for row in range(self.reward_table.rowCount()):
            product_name = self.reward_table.item(row, 2).text().lower()
            self.reward_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()

    def add_reward(self):
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        product_id = self.product_id.text().strip()
        if not product_id:
            QMessageBox.warning(self, "입력 오류", "상품 ID를 입력해주세요.")
            return
        row = self.reward_table.rowCount()
        self.reward_table.insertRow(row)
        self.reward_table.setItem(row, 0, QTableWidgetItem(start_date))
        self.reward_table.setItem(row, 1, QTableWidgetItem(end_date))
        self.reward_table.setItem(row, 2, QTableWidgetItem(product_id))
        self.reward_table.setItem(row, 3, QTableWidgetItem(f"{self.reward_amount.value():,}원"))
        delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
        delete_btn.clicked.connect(lambda: self.delete_reward(row))
        self.reward_table.setCellWidget(row, 4, delete_btn)
        self.product_id.clear(); self.reward_amount.setValue(0)

    def delete_reward(self, row):
        self.reward_table.removeRow(row)
        self.refresh_table_buttons()

    def refresh_table_buttons(self):
        for row in range(self.reward_table.rowCount()):
            delete_btn = AppleStyleButton("삭제", "fa5s.trash", MaterialColors.ERROR)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_reward(r))
            self.reward_table.setCellWidget(row, 4, delete_btn)

    def load_rewards(self):
        try:
            reward_file = os.path.join(config.BASE_DIR, '리워드설정.json')
            if not os.path.exists(reward_file): return
            with open(reward_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for reward in data.get('rewards', []):
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
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            other_days_rewards = [e for e in self.all_rewards_data.get('rewards', []) if e.get('start_date') != target_date_str]
            new_rewards = []
            for row in range(self.reward_table.rowCount()):
                reward_entry = {
                    'start_date': target_date_str, 'end_date': target_date_str,
                    'product_id': self.reward_table.item(row, 1).text(),
                    'reward': self.reward_table.cellWidget(row, 4).value()
                }
                # 옵션정보가 있으면 추가
                option_info = self.reward_table.item(row, 3).text()
                if option_info:
                    reward_entry['option_info'] = option_info
                new_rewards.append(reward_entry)
            self.all_rewards_data['rewards'] = other_days_rewards + new_rewards
            with open(self.reward_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_rewards_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "완료", f"{target_date_str}의 리워드 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"리워드 설정 저장 중 오류가 발생했습니다:\n{str(e)}")

class PurchaseManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🛒 일일 가구매 개수 관리')
        self.setFixedSize(950, 750)
        self.setModal(True)
        
        self.purchase_file = os.path.join(config.BASE_DIR, '가구매설정.json')
        self.margin_file = config.MARGIN_FILE
        self.all_purchases_data = {'purchases': []}
        self.products_df = pd.DataFrame()

        # 초기화 완료 플래그
        self._initialization_complete = False

        self.initUI()
        self.load_data_sources()
        # 초기화 완료 플래그 설정
        self._initialization_complete = True
        # 초기 데이터 로드
        self.load_initial_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 최소화된 헤더 섹션
        header_widget = QWidget()
        header_widget.setStyleSheet("background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 8px;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title_label = QLabel("일일 가구매 개수 설정")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #01579B; margin: 0;")
        subtitle_label = QLabel("상품별 가구매 개수를 날짜별로 설정하세요")
        subtitle_label.setStyleSheet("font-size: 12px; color: #6c757d; margin-top: 4px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_widget)
        
        # 스크롤 가능한 컨텐츠 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        date_group = QGroupBox("날짜 선택 및 설정 복사")
        date_layout = QGridLayout()
        date_layout.addWidget(QLabel("<b>수정할 날짜:</b>"), 0, 0)
        self.target_date_edit = QDateEdit(QDate.currentDate()); self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.dateChanged.connect(self.load_purchases_for_date)
        date_layout.addWidget(self.target_date_edit, 0, 1)
        date_layout.addWidget(QLabel("<b>설정 복사:</b>"), 1, 0)
        self.source_date_edit = QDateEdit(QDate.currentDate().addDays(-1)); self.source_date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.source_date_edit, 1, 1)
        self.copy_button = QPushButton("의 설정 불러오기"); self.copy_button.clicked.connect(self.copy_purchases)
        date_layout.addWidget(self.copy_button, 1, 2)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        control_group = QGroupBox("검색 및 일괄 설정")
        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("검색:"), 0, 0)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("상품명으로 검색...")
        self.search_box.textChanged.connect(self.filter_products)
        control_layout.addWidget(self.search_box, 0, 1, 1, 2)
        self.select_all_checkbox = QCheckBox("전체 선택/해제"); self.select_all_checkbox.clicked.connect(self.toggle_all_selection)
        control_layout.addWidget(self.select_all_checkbox, 1, 0)
        self.selected_count_label = QLabel("선택됨: 0개")
        control_layout.addWidget(self.selected_count_label, 1, 1)
        control_layout.addWidget(QLabel("선택된 항목에 적용:"), 2, 0)
        bulk_layout = QHBoxLayout()
        self.bulk_purchase = QSpinBox(); self.bulk_purchase.setRange(0, 9999); self.bulk_purchase.setSuffix(" 개")
        bulk_layout.addWidget(self.bulk_purchase)
        
        # 빠른 설정 버튼들
        quick_buttons = [("0개", 0), ("1개", 1), ("3개", 3), ("5개", 5), ("10개", 10)]
        for text, value in quick_buttons:
            btn = QPushButton(text)
            btn.setMaximumWidth(50)
            btn.clicked.connect(lambda checked, v=value: self.bulk_purchase.setValue(v))
            btn.setStyleSheet("font-size: 11px; padding: 4px;")
            bulk_layout.addWidget(btn)
        
        bulk_layout.addStretch()
        control_layout.addLayout(bulk_layout, 2, 1, 1, 2)
        self.apply_selected_button = QPushButton("선택된 항목에 적용"); self.apply_selected_button.clicked.connect(self.apply_to_selected)
        self.apply_selected_button.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        control_layout.addWidget(self.apply_selected_button, 3, 0, 1, 3)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 상품 테이블
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(['선택', '상품ID', '상품명', '옵션정보', '가구매 개수'])
        self.product_table.setMinimumHeight(350)  # 높이 설정하여 버튼 공간 확보
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 상품ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 상품명
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 옵션정보
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 가구매 개수
        layout.addWidget(self.product_table)
        
        # 스크롤 영역 설정 (버튼들은 제외)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 하단 고정 버튼들 (스크롤 영역 밖에 배치)
        button_widget = QWidget()
        button_widget.setStyleSheet("background: #f8f9fa; border-top: 1px solid #dee2e6; padding: 10px;")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        self.save_button = QPushButton("💾 저장")
        self.save_button.clicked.connect(self.save_purchases)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # 하단 고정 버튼 위젯을 메인 레이아웃에 추가
        main_layout.addWidget(button_widget)
    
    def load_initial_data(self):
        """UI 완성 후 초기 데이터 로드"""
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            self.load_purchases_for_date(QDate.currentDate())

    def load_data_sources(self):
        try:
            if os.path.exists(self.margin_file):
                df = pd.read_excel(self.margin_file, engine='openpyxl')
                df = df.rename(columns={'상품번호': '상품ID'})
                if '대표옵션' in df.columns:
                    df['대표옵션'] = df['대표옵션'].astype(str).str.upper().isin(['O', 'Y', 'TRUE'])
                    df = df[df['대표옵션'] == True]
                # 옵션정보 컬럼도 포함하여 products_df 생성
                columns_to_keep = ['상품ID', '상품명']
                if '옵션정보' in df.columns:
                    columns_to_keep.append('옵션정보')
                self.products_df = df[columns_to_keep].drop_duplicates().sort_values(by='상품명')
            if os.path.exists(self.purchase_file):
                with open(self.purchase_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.all_purchases_data = json.loads(content) if content else {'purchases': []}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 소스 로드 오류: {e}")

    def normalize_product_id(self, product_id):
        """product_id 정규화 (.0 제거)"""
        product_id_str = str(product_id)
        if product_id_str.endswith('.0'):
            return product_id_str[:-2]
        return product_id_str

    def safe_get_option_info(self, product):
        """상품 데이터에서 옵션정보를 안전하게 가져오기"""
        import pandas as pd
        option_info = product.get('옵션정보', '')
        
        # pandas NA 값 처리
        if pd.isna(option_info):
            return ''
        
        # 문자열로 변환하고 공백 제거
        return str(option_info).strip()

    def find_purchase_value(self, product_id, purchase_map, option_info=''):
        """product_id와 옵션정보에 대한 가구매 값 찾기"""
        clean_id = self.normalize_product_id(product_id)
        dotted_id = clean_id + '.0'
        
        # 3-tuple 키로 옵션별 설정 확인
        option_key = (clean_id, option_info)
        dotted_option_key = (dotted_id, option_info)
        
        # 옵션별 설정이 있으면 우선 사용
        if option_key in purchase_map:
            return purchase_map[option_key]
        if dotted_option_key in purchase_map:
            return purchase_map[dotted_option_key]
        
        # 기존 방식 (하위 호환성)
        return purchase_map.get(clean_id, purchase_map.get(dotted_id, 0))
    
    def clear_table_widgets(self):
        """테이블 위젯들을 안전하게 정리"""
        try:
            for row in range(self.product_table.rowCount()):
                # 체크박스 정리
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.deleteLater()
                # 스핀박스 정리
                spinbox = self.product_table.cellWidget(row, 3)
                if spinbox:
                    spinbox.deleteLater()
            
            # 테이블 내용 클리어
            self.product_table.clearContents()
        except Exception as e:
            import logging
            logging.error(f"가구매 테이블 위젯 정리 중 오류: {e}")

    def load_purchases_for_date(self, q_date):
        target_date_str = q_date.toString("yyyy-MM-dd")
        
        # 기존 위젯들 정리
        self.clear_table_widgets()
        
        # 모든 형식의 product_id를 포함하는 purchase_map 생성
        purchase_map = {}
        for e in self.all_purchases_data.get('purchases', []):
            if e.get('start_date') == target_date_str:
                product_id = str(e['product_id'])
                option_info = e.get('option_info', '')
                
                # 옵션별 설정이 있으면 3-tuple 키로 저장
                if option_info:
                    purchase_map[(product_id, option_info)] = e['purchase_count']
                else:
                    # 기존 방식 (하위 호환성)
                    purchase_map[product_id] = e['purchase_count']
        
        self.product_table.setRowCount(len(self.products_df))
        
        for row, (_, product) in enumerate(self.products_df.iterrows()):
            product_id = str(product['상품ID'])
            option_info = self.safe_get_option_info(product)
            
            # 체크박스 생성 및 이벤트 연결
            checkbox = QCheckBox()
            checkbox.clicked.connect(self.update_selected_count)
            self.product_table.setCellWidget(row, 0, checkbox)
            
            self.product_table.setItem(row, 1, QTableWidgetItem(product_id))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product['상품명'])))
            self.product_table.setItem(row, 3, QTableWidgetItem(option_info))
            
            # 스핀박스 생성
            spinbox = QSpinBox()
            spinbox.setRange(0, 9999)
            spinbox.setSuffix(" 개")
            # 호환성을 위해 두 형식 모두 확인
            purchase_value = self.find_purchase_value(product_id, purchase_map, option_info)
            spinbox.setValue(purchase_value)
            self.product_table.setCellWidget(row, 4, spinbox)
        
        self.filter_products()
        self.update_selected_count()  # 초기 상태 업데이트

    def copy_purchases(self):
        source_date_str = self.source_date_edit.date().toString("yyyy-MM-dd")
        purchase_map = {}
        
        # 가구매 데이터에서 해당 날짜 설정 찾기
        for entry in self.all_purchases_data.get('purchases', []):
            if entry.get('start_date') == source_date_str:
                product_id = str(entry['product_id'])
                purchase_map[product_id] = entry['purchase_count']
        
        if not purchase_map:
            QMessageBox.information(self, "알림", f"{source_date_str}에 저장된 가구매 설정이 없습니다.")
            return
            
        # 현재 테이블에 적용
        applied_count = 0
        for row in range(self.product_table.rowCount()):
            product_id_item = self.product_table.item(row, 1)
            spinbox = self.product_table.cellWidget(row, 3)
            if product_id_item and spinbox:
                product_id = product_id_item.text()
                # 호환성을 위해 두 형식 모두 확인
                purchase_value = self.find_purchase_value(product_id, purchase_map)
                if purchase_value > 0:  # 가구매 값이 있는 경우만 적용
                    spinbox.setValue(purchase_value)
                    applied_count += 1
        
        QMessageBox.information(self, "복사 완료", f"{applied_count}개 상품의 가구매 설정을 복사했습니다.")

    def toggle_all_selection(self):
        is_checked = self.select_all_checkbox.isChecked()
        for row in range(self.product_table.rowCount()):
            if not self.product_table.isRowHidden(row):
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(is_checked)
        self.update_selected_count()

    def apply_to_selected(self):
        """선택된 항목에 일괄 적용 (예외 처리 강화)"""
        try:
            bulk_value = self.bulk_purchase.value()
            applied_count = 0
            for row in range(self.product_table.rowCount()):
                checkbox = self.product_table.cellWidget(row, 0)
                spinbox = self.product_table.cellWidget(row, 4)
                if checkbox and checkbox.isChecked() and spinbox:
                    spinbox.setValue(bulk_value)
                    applied_count += 1
            
            if applied_count > 0:
                QMessageBox.information(self, "적용 완료", f"{applied_count}개 상품에 {bulk_value}개 가구매를 적용했습니다.")
            else:
                QMessageBox.warning(self, "선택 없음", "적용할 상품을 먼저 선택해주세요.")
        except Exception as e:
            import logging
            logging.error(f"가구매 일괄 적용 중 오류: {e}")
            QMessageBox.critical(self, "오류", f"일괄 적용 중 오류가 발생했습니다:\n{str(e)}")

    def update_selected_count(self):
        """선택된 항목 수 업데이트 (예외 처리 강화)"""
        try:
            selected_count = 0
            total_visible = 0
            
            for row in range(self.product_table.rowCount()):
                if not self.product_table.isRowHidden(row):
                    total_visible += 1
                    checkbox = self.product_table.cellWidget(row, 0)
                    if checkbox and checkbox.isChecked():
                        selected_count += 1
            
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText(f"선택됨: {selected_count}개")
            
            # 적용 버튼 활성화 상태 업데이트
            if hasattr(self, 'apply_selected_button'):
                self.apply_selected_button.setEnabled(selected_count > 0)
        except Exception as e:
            import logging
            logging.error(f"가구매 선택 개수 업데이트 중 오류: {e}")
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText("선택됨: 오류")

    def filter_products(self):
        search_text = self.search_box.text().lower()
        for row in range(self.product_table.rowCount()):
            product_name = self.product_table.item(row, 2).text().lower()
            self.product_table.setRowHidden(row, search_text not in product_name)
        self.update_selected_count()  # 필터링 후 선택 수 업데이트

    def save_purchases(self):
        try:
            target_date_str = self.target_date_edit.date().toString("yyyy-MM-dd")
            other_days_purchases = [e for e in self.all_purchases_data.get('purchases', []) if e.get('start_date') != target_date_str]
            new_purchases = []
            for row in range(self.product_table.rowCount()):
                purchase_entry = {
                    'start_date': target_date_str, 'end_date': target_date_str,
                    'product_id': self.product_table.item(row, 1).text(),
                    'purchase_count': self.product_table.cellWidget(row, 4).value()
                }
                # 옵션정보가 있으면 추가
                option_info = self.product_table.item(row, 3).text()
                if option_info:
                    purchase_entry['option_info'] = option_info
                new_purchases.append(purchase_entry)
            self.all_purchases_data['purchases'] = other_days_purchases + new_purchases
            with open(self.purchase_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_purchases_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "완료", f"{target_date_str}의 가구매 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"가구매 설정 저장 중 오류가 발생했습니다:\n{str(e)}")

class ModernSalesAutomationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_folder_path = ""
        self.password = "1234"
        self.worker = None
        self.manual_worker = None
        self.weekly_worker = None
        
        # 오류 추적 시스템
        self.error_messages = []  # 오류 메시지 리스트
        self.error_count = 0      # 오류 카운터
        
        self.init_ui()
        self.setup_logging()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("📊 판매 데이터 자동화")
        self.setMinimumSize(1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        main_layout.addLayout(self.create_header())
        main_layout.addWidget(self.create_settings_section())
        main_layout.addWidget(self.create_stats_section())
        main_layout.addWidget(self.create_log_section())
        self.statusBar().showMessage("✅ 준비됨")

    def create_header(self):
        header_layout = QHBoxLayout()
        icon_label = QLabel("📊"); title_label = QLabel("판매 데이터 자동화")
        title_label.setStyleSheet("font-size: 28px; font-weight: 700;")
        header_layout.addWidget(icon_label); header_layout.addWidget(title_label); header_layout.addStretch()
        return header_layout

    def create_settings_section(self):
        settings_card = QGroupBox("⚙️ 설정")
        layout = QVBoxLayout(settings_card)
        form_layout = QGridLayout()
        self.folder_label = QLabel("폴더를 선택해주세요..."); self.folder_label.setStyleSheet("color: #666; font-style: italic;")
        folder_btn = AppleStyleButton("📁 폴더 선택", "fa5s.folder-open", color="#555")
        folder_btn.clicked.connect(self.select_folder)
        folder_layout = QHBoxLayout(); folder_layout.addWidget(self.folder_label, 1); folder_layout.addWidget(folder_btn)
        form_layout.addWidget(QLabel("다운로드 폴더:"), 0, 0); form_layout.addLayout(folder_layout, 0, 1)
        self.password_input = QLineEdit("1234"); self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.update_password)
        form_layout.addWidget(QLabel("주문조회 파일 암호:"), 1, 0); form_layout.addWidget(self.password_input, 1, 1)
        layout.addLayout(form_layout)
        
        control_layout = QHBoxLayout()
        self.start_btn = AppleStyleButton("🚀 자동화 시작", "fa5s.play", MaterialColors.SUCCESS); self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn = AppleStyleButton("⏹️ 중지", "fa5s.stop", MaterialColors.ERROR); self.stop_btn.clicked.connect(self.stop_monitoring); self.stop_btn.setEnabled(False)
        self.manual_btn = AppleStyleButton("🔄 작업폴더 처리", "fa5s.cog", MaterialColors.WARNING); self.manual_btn.clicked.connect(self.manual_process)
        self.reward_btn = AppleStyleButton("💰 리워드 관리", "fa5s.gift", "#8b5cf6"); self.reward_btn.clicked.connect(self.show_reward_dialog)
        self.purchase_btn = AppleStyleButton("🛒 가구매 관리", "fa5s.shopping-cart", "#f59e0b"); self.purchase_btn.clicked.connect(self.show_purchase_dialog)
        self.weekly_report_btn = AppleStyleButton("📅 주간 리포트", "fa5s.calendar-week", "#10b981"); self.weekly_report_btn.clicked.connect(self.show_weekly_report_dialog)
        
        control_layout.addWidget(self.start_btn); control_layout.addWidget(self.stop_btn); control_layout.addWidget(self.manual_btn)
        control_layout.addWidget(self.reward_btn); control_layout.addWidget(self.purchase_btn); control_layout.addWidget(self.weekly_report_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        return settings_card

    def create_stats_section(self):
        stats_card = QGroupBox("📈 실시간 통계")
        kpi_layout = QGridLayout(stats_card)
        
        # 그리드 레이아웃 여백 설정
        kpi_layout.setContentsMargins(20, 20, 20, 20)
        kpi_layout.setSpacing(15)
        
        self.files_card = ModernDataCard("처리된 파일", "0개", "fa5s.file-alt", MaterialColors.SUCCESS)
        self.sales_card = ModernDataCard("총 매출", "₩0", "fa5s.dollar-sign", MaterialColors.PRIMARY)
        self.margin_card = ModernDataCard("순이익", "₩0", "fa5s.chart-line", MaterialColors.WARNING)
        self.error_card = ModernDataCard("에러", "0개", "fa5s.exclamation-triangle", MaterialColors.ERROR)
        
        # 에러 카드를 클릭 가능하게 만들기
        self.error_card.setCursor(Qt.PointingHandCursor)
        self.error_card.mousePressEvent = self.show_error_details
        
        # 그리드에 카드 추가 (여백 있게)
        kpi_layout.addWidget(self.files_card, 0, 0)
        kpi_layout.addWidget(self.sales_card, 0, 1)
        kpi_layout.addWidget(self.margin_card, 0, 2)
        kpi_layout.addWidget(self.error_card, 0, 3)
        
        # 컬럼별 균등 크기 설정
        kpi_layout.setColumnStretch(0, 1)
        kpi_layout.setColumnStretch(1, 1)
        kpi_layout.setColumnStretch(2, 1)
        kpi_layout.setColumnStretch(3, 1)
        
        return stats_card

    def create_log_section(self):
        log_card = QGroupBox("📋 처리 로그")
        layout = QVBoxLayout(log_card)
        self.log_output = ModernLogViewer()
        self.log_output.append("[INFO] 💡 애플리케이션이 준비되었습니다.")
        layout.addWidget(self.log_output)
        log_controls = QHBoxLayout()
        clear_btn = AppleStyleButton("🗑️ 로그 지우기", "fa5s.trash", MaterialColors.ERROR); clear_btn.clicked.connect(self.log_output.clear)
        log_controls.addWidget(clear_btn); log_controls.addStretch()
        layout.addLayout(log_controls)
        return log_card

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('sales_automation.log', encoding='utf-8'), logging.StreamHandler()])

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "다운로드 폴더 선택")
        if folder:
            self.download_folder_path = folder
            self.folder_label.setText(f"📁 {folder}")
            self.update_log(f"[INFO] 다운로드 폴더 설정: {folder}")

    def update_password(self):
        self.password = self.password_input.text()

    def start_monitoring(self):
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return
        
        stop_flag_path = os.path.join(config.BASE_DIR, 'stop.flag')
        if os.path.exists(stop_flag_path):
            try:
                os.remove(stop_flag_path)
                self.update_log("[INFO] 이전 중지 플래그 파일을 삭제했습니다.")
            except Exception as e:
                self.update_log(f"[ERROR] 중지 플래그 파일 삭제 실패: {e}")

        self.set_controls_enabled(False)
        self.worker = ModernWorker(self.download_folder_path, self.password)
        self.worker.output_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.on_monitoring_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.stats_signal.connect(self.update_stats)  # 통계 시그널 연결
        self.worker.start()

    def stop_monitoring(self):
        self.update_log("[INFO] ⏹️ 자동화 중지를 요청합니다...")
        try:
            stop_flag_path = os.path.join(config.BASE_DIR, 'stop.flag')
            with open(stop_flag_path, 'w') as f:
                f.write('stop')
            self.update_log("[INFO] 'stop.flag' 파일 생성 완료. 현재 작업 완료 후 모니터링이 종료됩니다.")
            self.stop_btn.setEnabled(False)
        except Exception as e:
            self.update_log(f"[ERROR] 중지 신호 파일 생성 실패: {e}")

    def manual_process(self):
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return
        self.set_controls_enabled(False)
        self.manual_worker = ModernManualWorker(self.download_folder_path, self.password)
        self.manual_worker.output_signal.connect(self.update_log)
        self.manual_worker.error_signal.connect(self.on_error)  # 오류 시그널 연결
        self.manual_worker.finished_signal.connect(self.on_manual_finished)
        self.manual_worker.stats_signal.connect(self.update_stats)  # 통계 시그널 연결
        self.manual_worker.start()

    def show_reward_dialog(self):
        dialog = ModernRewardDialog(self)
        dialog.exec()

    def show_purchase_dialog(self):
        dialog = PurchaseManagerDialog(self)
        dialog.exec()

    def show_weekly_report_dialog(self):
        if not self.download_folder_path:
            QMessageBox.warning(self, "설정 오류", "다운로드 폴더를 먼저 선택해주세요.")
            return
        dialog = WeeklyReportDialog(self)
        if dialog.exec():
            start_date, end_date = dialog.get_dates()
            if start_date and end_date:  # 날짜 검증 통과한 경우만 실행
                self.run_weekly_report_creation(start_date, end_date)
            else:
                QMessageBox.warning(self, "날짜 오류", "올바른 날짜 범위를 선택해주세요.")

    def run_weekly_report_creation(self, start_date, end_date):
        self.set_controls_enabled(False)
        self.weekly_worker = WeeklyWorker(start_date, end_date, self.download_folder_path)
        self.weekly_worker.output_signal.connect(self.update_log)
        self.weekly_worker.error_signal.connect(self.on_error)  # 오류 시그널 연결
        self.weekly_worker.finished_signal.connect(self.on_weekly_report_finished)
        self.weekly_worker.start()

    def on_monitoring_finished(self):
        self.set_controls_enabled(True)
        self.update_log("[INFO] ⏹️ 모니터링이 중지되었습니다.")

    def on_manual_finished(self):
        self.set_controls_enabled(True)

    def on_weekly_report_finished(self):
        self.set_controls_enabled(True)
        self.update_log("[INFO] ✅ 주간 리포트 생성이 완료되었습니다.")

    def update_stats(self, stats_dict):
        """통계 카드들을 업데이트"""
        try:
            if 'files' in stats_dict:
                self.files_card.update_value(stats_dict['files'])
            if 'sales' in stats_dict:
                self.sales_card.update_value(stats_dict['sales'])
            if 'profit' in stats_dict:
                self.margin_card.update_value(stats_dict['profit'])
        except Exception as e:
            self.update_log(f"[DEBUG] 통계 업데이트 중 오류: {e}")

    def on_error(self, msg):
        self.update_log(msg)
        
        # 오류 메시지 추가 (시간과 함께 저장)
        error_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'message': msg,
            'type': self.classify_error(msg)
        }
        self.error_messages.append(error_entry)
        
        # 오류 카운터 업데이트
        self.error_count += 1
        self.error_card.update_value(f"{self.error_count}개")
        
        # 최근 100개 오류만 유지 (메모리 관리)
        if len(self.error_messages) > 100:
            self.error_messages = self.error_messages[-100:]

    def classify_error(self, msg):
        """오류 메시지를 분류하여 타입 반환"""
        msg_lower = msg.lower()
        if 'file' in msg_lower or '파일' in msg:
            return '파일 오류'
        elif 'permission' in msg_lower or '권한' in msg:
            return '권한 오류'
        elif 'memory' in msg_lower or '메모리' in msg:
            return '메모리 오류'
        elif 'network' in msg_lower or '네트워크' in msg:
            return '네트워크 오류'
        elif 'validation' in msg_lower or '검증' in msg:
            return '검증 오류'
        else:
            return '일반 오류'

    def show_error_details(self, event):
        """오류 상세 정보를 팝업으로 표시"""
        if self.error_count == 0:
            QMessageBox.information(self, "오류 없음", "현재까지 발생한 오류가 없습니다.")
            return
        
        dialog = ErrorDetailsDialog(self.error_messages, self)
        dialog.exec()

    def update_log(self, message):
        self.log_output.append(f"[{datetime.now().strftime("%H:%M:%S")}] {message}")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def set_controls_enabled(self, enabled):
        self.start_btn.setEnabled(enabled)
        self.manual_btn.setEnabled(enabled)
        self.weekly_report_btn.setEnabled(enabled)
        self.reward_btn.setEnabled(enabled)
        self.purchase_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
    
    def load_settings(self):
        """애플리케이션 설정 로드"""
        try:
            settings = QSettings("SalesAutomation", "ModernSalesApp")
            
            # 창 위치 및 크기 복원
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            # 다운로드 폴더 경로 복원
            folder_path = settings.value("download_folder", "")
            if folder_path and os.path.exists(folder_path):
                self.download_folder_path = folder_path
                self.folder_label.setText(f"📁 {folder_path}")
            
            # 패스워드 복원 (보안상 저장하지 않음)
            
        except Exception as e:
            import logging
            logging.error(f"설정 로드 중 오류: {e}")
    
    def save_settings(self):
        """애플리케이션 설정 저장"""
        try:
            settings = QSettings("SalesAutomation", "ModernSalesApp")
            
            # 창 위치 및 크기 저장
            settings.setValue("geometry", self.saveGeometry())
            
            # 다운로드 폴더 경로 저장
            if self.download_folder_path:
                settings.setValue("download_folder", self.download_folder_path)
            
        except Exception as e:
            import logging
            logging.error(f"설정 저장 중 오류: {e}")
    
    def cleanup_workers(self):
        """모든 워커 스레드 안전 정리"""
        workers = [
            ('worker', self.worker),
            ('manual_worker', self.manual_worker), 
            ('weekly_worker', self.weekly_worker)
        ]
        
        for name, worker in workers:
            if worker and worker.isRunning():
                try:
                    self.update_log(f"[INFO] {name} 스레드 종료 중...")
                    worker.quit()
                    if not worker.wait(3000):  # 3초 대기
                        self.update_log(f"[WARNING] {name} 스레드 강제 종료")
                        worker.terminate()
                        worker.wait(1000)
                    else:
                        self.update_log(f"[INFO] {name} 스레드 정상 종료")
                except Exception as e:
                    self.update_log(f"[ERROR] {name} 스레드 정리 중 오류: {e}")
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 정리 작업"""
        try:
            # 실행 중인 작업이 있는지 확인
            running_workers = []
            if self.worker and self.worker.isRunning():
                running_workers.append("자동 모니터링")
            if self.manual_worker and self.manual_worker.isRunning():
                running_workers.append("수동 처리")
            if self.weekly_worker and self.weekly_worker.isRunning():
                running_workers.append("주간 리포트")
            
            if running_workers:
                reply = QMessageBox.question(
                    self, 
                    "작업 진행 중",
                    f"다음 작업이 진행 중입니다:\n{', '.join(running_workers)}\n\n정말 종료하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    event.ignore()
                    return
            
            # 설정 저장
            self.save_settings()
            
            # 워커 스레드 정리
            self.cleanup_workers()
            
            # 부모 클래스의 closeEvent 호출
            super().closeEvent(event)
            
        except Exception as e:
            import logging
            logging.error(f"애플리케이션 종료 중 오류: {e}")
            # 오류가 있어도 종료 진행
            super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    window = ModernSalesAutomationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
