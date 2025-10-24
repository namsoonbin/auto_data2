"""
즉시 검색 탭 UI
URL + 키워드 입력 → 실시간 순위 결과 표시
"""

import requests
import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QTextEdit, QProgressBar, QGroupBox, QSpacerItem, QSizePolicy,
    QComboBox, QCheckBox, QDialog, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot
from PySide6.QtGui import QPixmap, QFont
from typing import Optional, Dict, Any
import logging

try:
    from ..core.unified_rank_engine import UnifiedRankEngine, RankSearchResult
    from ..core.product_group import ProductGroup, GroupItem, ProductGroupManager
except ImportError:
    # 개발 중 import 오류 대비
    UnifiedRankEngine = None
    RankSearchResult = None
    ProductGroup = None
    GroupItem = None
    ProductGroupManager = None


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

    # 시그널 정의
    group_added = Signal()  # 그룹이 추가되었을 때

    def __init__(self, parent_tab=None):
        super().__init__()
        self.parent_tab = parent_tab  # 부모 탭 참조 저장
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

        # 버튼 이벤트 연결
        self.add_to_group_btn.clicked.connect(self.show_add_to_group_dialog)
        self.view_detail_btn.clicked.connect(self.show_detail_dialog)

        # 검색 결과 저장용
        self.current_result = None

    def update_result(self, result: 'RankSearchResult'):
        """검색 결과로 카드 업데이트"""
        self.current_result = result  # 결과 저장

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

    def show_add_to_group_dialog(self):
        """그룹에 추가 다이얼로그 표시 - 새로운 URL+키워드 구조"""
        if not self.current_result or not self.current_result.success:
            QMessageBox.warning(self, "경고", "먼저 상품을 검색해주세요.")
            return

        if not ProductGroupManager:
            QMessageBox.critical(self, "오류", "ProductGroupManager를 로드할 수 없습니다.")
            return

        # ✅ Phase 10: ProductGroupManager만 사용 (하드코딩 경로 제거)
        group_manager = ProductGroupManager()
        groups = {group.group_id: group.name for group in group_manager.get_all_groups()}

        # 그룹 선택 다이얼로그
        items = list(groups.values()) + ["+ 새 그룹 만들기"]
        if not items:
            items = ["+ 새 그룹 만들기"]

        item, ok = QInputDialog.getItem(
            self, "그룹 선택", "상품을 추가할 그룹을 선택하세요:", items, 0, False
        )

        if ok and item:
            if item == "+ 새 그룹 만들기":
                # 새 그룹 생성
                group_name, ok = QInputDialog.getText(
                    self, "새 그룹 생성", "그룹명을 입력하세요:"
                )
                if ok and group_name.strip():
                    self._add_to_new_group(group_manager, group_name.strip())
            else:
                # 기존 그룹에 추가
                selected_group_id = None
                for group_id, name in groups.items():
                    if name == item:
                        selected_group_id = group_id
                        break
                if selected_group_id:
                    self._add_to_existing_group(group_manager, selected_group_id, item)

    def _add_to_new_group(self, group_manager, group_name: str):
        """새 그룹에 URL+키워드 아이템 추가"""
        try:
            # 키워드 입력 받기
            keyword, ok = QInputDialog.getText(
                self, "키워드 입력",
                f"상품 '{self.current_result.product_info.title if self.current_result.product_info else 'Unknown'}'의 검색 키워드를 입력하세요:",
                text=self.current_result.search_keyword  # 기본값으로 검색했던 키워드 사용
            )

            if not ok or not keyword.strip():
                return

            # 새 그룹 생성
            group_id = group_manager.create_group(group_name)
            group = group_manager.get_group(group_id)

            if group:
                # 아이템 추가
                title = self.current_result.product_info.title if self.current_result.product_info else "Unknown Product"
                item_id = group.add_item(
                    url=self.current_result.input_url,
                    keyword=keyword.strip(),
                    title=title,
                    product_id=self.current_result.effective_product_id
                )

                # 데이터 저장
                group_manager.save_groups()

                # 그룹 추가 시그널 전송
                logging.info(f"ProductResultCard: group_added 시그널 emit (새 그룹: {group_name})")
                self.group_added.emit()

                QMessageBox.information(
                    self, "성공",
                    f"새 그룹 '{group_name}'이 생성되고 상품이 추가되었습니다."
                )
            else:
                QMessageBox.critical(self, "오류", "그룹 생성에 실패했습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"새 그룹 생성 실패: {e}")

    def _add_to_existing_group(self, group_manager, group_id: str, group_name: str):
        """기존 그룹에 URL+키워드 아이템 추가"""
        try:
            # 키워드 입력 받기
            keyword, ok = QInputDialog.getText(
                self, "키워드 입력",
                f"상품 '{self.current_result.product_info.title if self.current_result.product_info else 'Unknown'}'의 검색 키워드를 입력하세요:",
                text=self.current_result.search_keyword  # 기본값으로 검색했던 키워드 사용
            )

            if not ok or not keyword.strip():
                return

            group = group_manager.get_group(group_id)
            if group:
                # 아이템 추가
                title = self.current_result.product_info.title if self.current_result.product_info else "Unknown Product"
                item_id = group.add_item(
                    url=self.current_result.input_url,
                    keyword=keyword.strip(),
                    title=title,
                    product_id=self.current_result.effective_product_id
                )

                # 데이터 저장
                group_manager.save_groups()

                # 그룹 추가 시그널 전송
                logging.info(f"ProductResultCard: group_added 시그널 emit (기존 그룹: {group_name})")
                self.group_added.emit()

                QMessageBox.information(
                    self, "성공",
                    f"'{group_name}' 그룹에 상품이 추가되었습니다."
                )
            else:
                QMessageBox.critical(self, "오류", "그룹을 찾을 수 없습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"그룹 추가 실패: {e}")
            if os.path.exists(groups_file):
                with open(groups_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                    # 새 형식과 구 형식 모두 지원
                    if "groups" in file_data:
                        # 구 형식을 새 형식으로 변환
                        for group in file_data["groups"]:
                            groups_data[group["group_id"]] = {
                                "name": group["name"],
                                "products": {},
                                "created_at": group.get("created_at"),
                                "last_checked": group.get("last_checked")
                            }

                    # 직접 객체 형식 로드
                    for key, value in file_data.items():
                        if key != "groups" and key != "saved_at" and isinstance(value, dict) and "name" in value:
                            groups_data[key] = value

            # 새 그룹 생성
            if group_id is None:
                group_id = f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                groups_data[group_id] = {
                    "name": group_name,
                    "products": {},
                    "created_at": datetime.now().isoformat(),
                    "last_checked": None
                }

            # 상품 정보 추가
            product_id = self.current_result.effective_product_id
            product_data = {
                "url": self.current_result.input_url,
                "title": self.current_result.product_info.title if self.current_result.product_info else "제목 없음",
                "added_at": datetime.now().isoformat()
            }

            groups_data[group_id]["products"][product_id] = product_data

            # 파일 저장
            with open(groups_file, 'w', encoding='utf-8') as f:
                json.dump(groups_data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(
                self, "성공", f"'{group_name}' 그룹에 상품이 추가되었습니다."
            )

        except Exception as e:
            QMessageBox.critical(self, "오류", f"그룹 추가 실패: {e}")

    def show_detail_dialog(self):
        """상세보기 다이얼로그 표시"""
        if not self.current_result or not self.current_result.success:
            QMessageBox.warning(self, "경고", "먼저 상품을 검색해주세요.")
            return

        # 상세보기 다이얼로그 생성
        dialog = ProductDetailDialog(self.current_result, self)
        dialog.exec()


class InstantSearchTab(QWidget):
    """즉시 검색 탭 메인 위젯"""

    # 시그널 정의
    group_added = Signal()  # 그룹이 추가되었을 때

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

        # 결과 카드 생성 및 표시 (부모 탭 참조 전달)
        result_card = ProductResultCard(parent_tab=self)
        result_card.update_result(result)

        # 카드의 group_added 시그널을 탭의 시그널로 전달
        result_card.group_added.connect(self.group_added.emit)
        logging.info("InstantSearchTab: ProductResultCard의 group_added 시그널 연결 완료")

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


class ProductDetailDialog(QDialog):
    """상품 상세보기 다이얼로그"""

    def __init__(self, result: 'RankSearchResult', parent=None):
        super().__init__(parent)
        self.result = result
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("상품 상세 정보")
        self.setFixedSize(500, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("📦 상품 상세 정보")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        if self.result.success and self.result.product_info:
            info = self.result.product_info

            # 상품 이미지
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setFixedSize(200, 200)
            image_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    background-color: #f5f5f5;
                }
            """)

            if info.image_url:
                try:
                    import requests
                    response = requests.get(info.image_url, timeout=5)
                    if response.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(response.content)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(
                                180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                            image_label.setPixmap(scaled_pixmap)
                        else:
                            image_label.setText("이미지 로드 실패")
                    else:
                        image_label.setText("이미지 없음")
                except Exception:
                    image_label.setText("이미지 로드 실패")
            else:
                image_label.setText("이미지 없음")

            content_layout.addWidget(image_label)

            # 상품 정보 테이블
            info_frame = QFrame()
            info_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 8px;
                }
            """)
            info_layout = QVBoxLayout(info_frame)

            # 순위 정보
            rank_text = f"🏆 순위: {self.result.rank}위" if self.result.rank else "🏆 순위: 순위권 밖"
            rank_label = QLabel(rank_text)
            rank_label.setFont(QFont('', 12, QFont.Bold))
            rank_label.setStyleSheet("color: #2196F3; margin-bottom: 8px;")
            info_layout.addWidget(rank_label)

            # 상품명
            title_label = QLabel(f"📝 상품명: {info.title}")
            title_label.setWordWrap(True)
            title_label.setFont(QFont('', 10, QFont.Bold))
            info_layout.addWidget(title_label)

            # 스토어명
            store_label = QLabel(f"🏪 스토어: {info.store_name}")
            info_layout.addWidget(store_label)

            # 가격
            if info.price_low:
                price_label = QLabel(f"💰 가격: {info.price_low}원")
            else:
                price_label = QLabel("💰 가격: 정보 없음")
            info_layout.addWidget(price_label)

            # 브랜드
            brand_label = QLabel(f"🏷️ 브랜드: {info.brand or '정보 없음'}")
            info_layout.addWidget(brand_label)

            # 카테고리
            category_label = QLabel(f"📂 카테고리: {info.category or '정보 없음'}")
            info_layout.addWidget(category_label)

            # 상품 ID
            id_label = QLabel(f"🔍 상품 ID: {self.result.effective_product_id}")
            info_layout.addWidget(id_label)

            # 검색 키워드
            keyword_label = QLabel(f"🔎 검색 키워드: {self.result.search_keyword}")
            info_layout.addWidget(keyword_label)

            # 검색 시간
            search_time_label = QLabel(f"🕒 검색 시간: {self.result.search_time.strftime('%Y-%m-%d %H:%M:%S')}")
            info_layout.addWidget(search_time_label)

            content_layout.addWidget(info_frame)

            # 상품 링크 버튼
            if info.link:
                link_btn = QPushButton("🌐 상품 페이지로 이동")
                link_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 12px;
                        border-radius: 6px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                link_btn.clicked.connect(lambda: self.open_product_link(info.link))
                content_layout.addWidget(link_btn)

        else:
            # 검색 실패 시
            error_label = QLabel("❌ 상품 정보를 가져올 수 없습니다")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: #f44336; font-size: 14px; margin: 20px;")
            content_layout.addWidget(error_label)

            if self.result.error_message:
                error_detail = QLabel(f"오류: {self.result.error_message}")
                error_detail.setWordWrap(True)
                error_detail.setAlignment(Qt.AlignCenter)
                error_detail.setStyleSheet("color: #666; margin: 10px;")
                content_layout.addWidget(error_detail)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def open_product_link(self, link: str):
        """상품 링크 열기"""
        try:
            import webbrowser
            webbrowser.open(link)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"링크를 열 수 없습니다: {e}")