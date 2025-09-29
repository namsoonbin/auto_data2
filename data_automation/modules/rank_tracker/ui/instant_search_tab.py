"""
즉시 검색 탭 UI
URL + 키워드 입력 → 실시간 순위 결과 표시
"""

import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QTextEdit, QProgressBar, QGroupBox, QSpacerItem, QSizePolicy,
    QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot
from PySide6.QtGui import QPixmap, QFont
from typing import Optional, Dict, Any
import logging

try:
    from ..core.unified_rank_engine import UnifiedRankEngine, RankSearchResult
except ImportError:
    # 개발 중 import 오류 대비
    pass


class InstantSearchWorker(QObject):
    """즉시 검색 워커 - 백그라운드 검색 처리"""

    search_started = Signal()
    search_progress = Signal(str)  # 진행 상황
    search_completed = Signal(object)  # RankSearchResult
    search_error = Signal(str)  # 에러 메시지

    def __init__(self, engine: 'UnifiedRankEngine'):
        super().__init__()
        self.engine = engine
        self.logger = logging.getLogger(__name__)

    @Slot(str, str, str, str, list)
    def search_rank(self, keyword: str, url: str, sort: str = "sim",
                   include_filter: str = None, exclude_types: list = None):
        """순위 검색 실행 - Enhanced 파라미터 지원"""
        try:
            self.search_started.emit()
            self.search_progress.emit("Enhanced 검색 시작...")

            # None 값 처리
            filter_param = include_filter if include_filter and include_filter != "없음" else None
            exclude_param = exclude_types if exclude_types else None

            result = self.engine.search_instant_rank(
                keyword=keyword,
                url_or_id=url,
                sort=sort,
                include_filter=filter_param,
                exclude_types=exclude_param
            )

            if result.success:
                if result.rank:
                    self.search_progress.emit(f"순위 발견: {result.rank}위")
                else:
                    self.search_progress.emit("순위권 밖")
            else:
                self.search_progress.emit("검색 실패")

            self.search_completed.emit(result)

        except Exception as e:
            self.logger.error(f"검색 중 오류: {e}")
            self.search_error.emit(f"검색 오류: {str(e)}")


class ProductResultCard(QFrame):
    """상품 검색 결과 카드"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                margin: 8px;
            }
            QFrame:hover {
                border-color: #2196F3;
            }
        """)

        layout = QVBoxLayout(self)

        # 상단: 순위 표시
        self.rank_label = QLabel("순위 없음")
        self.rank_label.setAlignment(Qt.AlignCenter)
        rank_font = QFont()
        rank_font.setPointSize(24)
        rank_font.setBold(True)
        self.rank_label.setFont(rank_font)
        self.rank_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: #f5f5f5;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
            }
        """)
        layout.addWidget(self.rank_label)

        # 중간: 상품 정보 섹션
        info_layout = QHBoxLayout()

        # 왼쪽: 상품 이미지
        self.image_label = QLabel()
        self.image_label.setFixedSize(120, 120)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
        self.image_label.setText("이미지\n로딩중...")
        info_layout.addWidget(self.image_label)

        # 오른쪽: 상품 상세 정보
        details_layout = QVBoxLayout()

        self.title_label = QLabel("상품명")
        self.title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        details_layout.addWidget(self.title_label)

        self.store_label = QLabel("스토어명")
        store_font = QFont()
        store_font.setPointSize(10)
        self.store_label.setFont(store_font)
        self.store_label.setStyleSheet("color: #666;")
        details_layout.addWidget(self.store_label)

        self.price_label = QLabel("가격 정보")
        price_font = QFont()
        price_font.setPointSize(11)
        price_font.setBold(True)
        self.price_label.setFont(price_font)
        self.price_label.setStyleSheet("color: #f44336;")
        details_layout.addWidget(self.price_label)

        self.brand_label = QLabel("브랜드")
        brand_font = QFont()
        brand_font.setPointSize(9)
        self.brand_label.setFont(brand_font)
        self.brand_label.setStyleSheet("color: #888;")
        details_layout.addWidget(self.brand_label)

        # 스페이서 추가
        details_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        info_layout.addLayout(details_layout)
        layout.addLayout(info_layout)

        # 하단: 액션 버튼들
        action_layout = QHBoxLayout()

        self.add_to_group_btn = QPushButton("그룹에 추가")
        self.add_to_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        action_layout.addWidget(self.add_to_group_btn)

        self.view_detail_btn = QPushButton("상세 보기")
        self.view_detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        action_layout.addWidget(self.view_detail_btn)

        action_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(action_layout)

    def update_result(self, result: 'RankSearchResult'):
        """검색 결과로 카드 업데이트"""
        if not result.success:
            self.rank_label.setText("검색 실패")
            self.rank_label.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    background-color: #ffebee;
                    border: 2px solid #f44336;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 16px;
                }
            """)
            self.title_label.setText(result.error_message or "알 수 없는 오류")
            return

        # 순위 업데이트
        if result.rank:
            self.rank_label.setText(f"{result.rank}위")
            self.rank_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    background-color: #f1f8e9;
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 16px;
                }
            """)
        else:
            self.rank_label.setText("순위권 밖")
            self.rank_label.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    background-color: #fff8e1;
                    border: 2px solid #FF9800;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 16px;
                }
            """)

        # 상품 정보 업데이트
        if result.product_info:
            info = result.product_info
            self.title_label.setText(info.title or "상품명 없음")
            self.store_label.setText(f"🏪 {info.store_name}" if info.store_name else "스토어명 없음")

            # 가격 정보
            if info.price_low and info.price_high:
                self.price_label.setText(f"💰 {info.price_low}원 ~ {info.price_high}원")
            elif info.price_low:
                self.price_label.setText(f"💰 {info.price_low}원")
            else:
                self.price_label.setText("가격 정보 없음")

            self.brand_label.setText(f"🏷️ {info.brand}" if info.brand else "브랜드 정보 없음")

            # 이미지 로드
            if info.image_url:
                self.load_product_image(info.image_url)
            else:
                self.image_label.setText("이미지\n없음")
        else:
            self.title_label.setText("상품 정보를 가져올 수 없습니다")

    def load_product_image(self, image_url: str):
        """상품 이미지 비동기 로드"""
        try:
            response = requests.get(image_url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    # 이미지 크기 조정
                    scaled_pixmap = pixmap.scaled(
                        120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_label.setText("이미지\n로드 실패")
            else:
                self.image_label.setText("이미지\n없음")
        except Exception:
            self.image_label.setText("이미지\n로드 실패")


class InstantSearchTab(QWidget):
    """즉시 검색 탭 메인 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.worker = None
        self.worker_thread = None
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("🔍 즉시 순위 검색")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 검색 입력 섹션
        search_group = QGroupBox("검색 정보 입력")
        search_layout = QFormLayout(search_group)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("예: 무선청소기")
        self.keyword_input.returnPressed.connect(self.search_rank)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("상품 URL 또는 상품 ID")
        self.url_input.returnPressed.connect(self.search_rank)

        # 고급 검색 옵션
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["정확도순 (sim)", "날짜순 (date)", "가격낮은순 (asc)", "가격높은순 (dsc)"])
        self.sort_combo.setCurrentIndex(0)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["필터 없음", "네이버페이만 (naverpay)"])
        self.filter_combo.setCurrentIndex(0)

        # 제외 옵션 (체크박스들)
        exclude_frame = QFrame()
        exclude_layout = QHBoxLayout(exclude_frame)
        exclude_layout.setContentsMargins(0, 0, 0, 0)

        self.exclude_used = QCheckBox("중고 제외")
        self.exclude_rental = QCheckBox("렌탈 제외")
        self.exclude_cbshop = QCheckBox("해외직구 제외")

        exclude_layout.addWidget(self.exclude_used)
        exclude_layout.addWidget(self.exclude_rental)
        exclude_layout.addWidget(self.exclude_cbshop)
        exclude_layout.addStretch()

        search_layout.addRow("검색 키워드:", self.keyword_input)
        search_layout.addRow("상품 URL/ID:", self.url_input)
        search_layout.addRow("정렬 방식:", self.sort_combo)
        search_layout.addRow("필터 옵션:", self.filter_combo)
        search_layout.addRow("제외 옵션:", exclude_frame)

        # 검색 버튼
        self.search_btn = QPushButton("🔍 순위 검색")
        self.search_btn.clicked.connect(self.search_rank)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        search_layout.addRow("", self.search_btn)

        layout.addWidget(search_group)

        # 진행 상황 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 결과 표시 영역
        self.result_scroll = QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.result_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 결과 컨테이너
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_scroll.setWidget(self.result_container)

        layout.addWidget(self.result_scroll)

        # 빈 상태 메시지
        self.show_empty_state()

    def show_empty_state(self):
        """빈 상태 메시지 표시"""
        empty_label = QLabel("위에 키워드와 상품 URL을 입력하고 검색 버튼을 클릭하세요")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 40px;
            }
        """)
        self.result_layout.addWidget(empty_label)

    def set_engine(self, engine: 'UnifiedRankEngine'):
        """순위 엔진 설정"""
        self.engine = engine

    def search_rank(self):
        """순위 검색 실행 - Enhanced 옵션 포함"""
        if not self.engine:
            self.status_label.setText("❌ 순위 엔진이 초기화되지 않았습니다")
            return

        keyword = self.keyword_input.text().strip()
        url = self.url_input.text().strip()

        if not keyword or not url:
            self.status_label.setText("❌ 키워드와 URL을 모두 입력해주세요")
            return

        # 고급 옵션 추출
        sort_text = self.sort_combo.currentText()
        sort = sort_text.split('(')[1].split(')')[0]  # "(sim)" -> "sim"

        filter_text = self.filter_combo.currentText()
        include_filter = "naverpay" if "naverpay" in filter_text else None

        exclude_types = []
        if self.exclude_used.isChecked():
            exclude_types.append("used")
        if self.exclude_rental.isChecked():
            exclude_types.append("rental")
        if self.exclude_cbshop.isChecked():
            exclude_types.append("cbshop")

        # 기존 결과 지우기
        self.clear_results()

        # Enhanced 파라미터로 워커 스레드 시작
        self.start_search_worker(keyword, url, sort, include_filter, exclude_types)

    def clear_results(self):
        """기존 결과 지우기"""
        for i in reversed(range(self.result_layout.count())):
            child = self.result_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

    def start_search_worker(self, keyword: str, url: str, sort: str = "sim",
                          include_filter: str = None, exclude_types: list = None):
        """검색 워커 스레드 시작 - Enhanced 파라미터 지원"""
        if self.worker_thread and self.worker_thread.isRunning():
            return

        self.worker_thread = QThread()
        self.worker = InstantSearchWorker(self.engine)
        self.worker.moveToThread(self.worker_thread)

        # 시그널 연결
        self.worker.search_started.connect(self.on_search_started)
        self.worker.search_progress.connect(self.on_search_progress)
        self.worker.search_completed.connect(self.on_search_completed)
        self.worker.search_error.connect(self.on_search_error)

        # 스레드 시작 - Enhanced 파라미터 전달
        self.worker_thread.started.connect(
            lambda: self.worker.search_rank(keyword, url, sort, include_filter, exclude_types)
        )
        self.worker_thread.finished.connect(self.cleanup_worker)
        self.worker_thread.start()

    def cleanup_worker(self):
        """워커 정리"""
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None

    @Slot()
    def on_search_started(self):
        """검색 시작"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 무한 진행
        self.search_btn.setEnabled(False)
        self.status_label.setText("🔍 검색 중...")

    @Slot(str)
    def on_search_progress(self, message: str):
        """검색 진행 상황"""
        self.status_label.setText(message)

    @Slot(object)
    def on_search_completed(self, result):
        """검색 완료"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)

        # 결과 카드 생성 및 표시
        result_card = ProductResultCard()
        result_card.update_result(result)
        self.result_layout.addWidget(result_card)

        if result.success and result.rank:
            self.status_label.setText(f"✅ 검색 완료: {result.rank}위 발견")
        elif result.success:
            self.status_label.setText(f"✅ 검색 완료: {result.total_scanned}위권 밖")
        else:
            self.status_label.setText("❌ 검색 실패")

        # 워커 정리
        if self.worker_thread:
            self.worker_thread.quit()

    @Slot(str)
    def on_search_error(self, error_message: str):
        """검색 오류"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"❌ {error_message}")

        # 워커 정리
        if self.worker_thread:
            self.worker_thread.quit()