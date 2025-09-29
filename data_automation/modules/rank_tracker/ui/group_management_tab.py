"""
그룹 관리 탭 - PySide6 Qt UI
상품을 그룹으로 관리하고 배치 순위 검색 지원
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QTextEdit, QFrame, QSplitter,
    QHeaderView, QAbstractItemView, QCheckBox, QProgressBar,
    QMessageBox, QInputDialog, QMenu, QScrollArea,
    QGroupBox, QTabWidget, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import (
    Qt, Signal, QThread, QObject, QTimer, Signal,
    QSize, QModelIndex
)
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QAction

# 기존 모듈 임포트 시도
try:
    from ..core.unified_rank_engine import UnifiedRankEngine, RankSearchResult
except ImportError:
    # 개발 시간 임포트 오류 방지
    UnifiedRankEngine = None
    RankSearchResult = None


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


class ProductGroup:
    """상품 그룹 데이터 클래스"""
    def __init__(self, group_id: str, name: str, description: str = ""):
        self.group_id = group_id
        self.name = name
        self.description = description
        self.products = []  # List[Dict] - url과 기타 메타데이터
        self.created_at = datetime.now(timezone(timedelta(hours=9)))
        self.last_checked = None

    def to_dict(self):
        return {
            'group_id': self.group_id,
            'name': self.name,
            'description': self.description,
            'products': self.products,
            'created_at': self.created_at.isoformat(),
            'last_checked': self.last_checked.isoformat() if self.last_checked else None
        }

    @classmethod
    def from_dict(cls, data: Dict):
        group = cls(data['group_id'], data['name'], data.get('description', ''))
        group.products = data.get('products', [])
        if 'created_at' in data:
            group.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('last_checked'):
            group.last_checked = datetime.fromisoformat(data['last_checked'])
        return group


class ProductCard(QFrame):
    """개별 상품 카드 UI"""
    remove_requested = Signal(str)  # product_url

    def __init__(self, product_data: Dict, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.init_ui()

    def init_ui(self):
        """카드 UI 초기화"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            ProductCard {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }}
            ProductCard:hover {{
                background-color: {MaterialColors.PRIMARY_CONTAINER};
                border-color: {MaterialColors.PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 상단: URL과 제거 버튼
        header_layout = QHBoxLayout()

        url_label = QLabel(self.product_data.get('url', ''))
        url_label.setFont(QFont('', 9, QFont.Bold))
        url_label.setWordWrap(True)
        url_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE};")

        remove_btn = QPushButton("❌")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setToolTip("이 상품을 그룹에서 제거")
        remove_btn.clicked.connect(self.request_remove)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.ERROR};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
        """)

        header_layout.addWidget(url_label, 1)
        header_layout.addWidget(remove_btn)

        # 하단: 메타데이터 정보
        meta_layout = QVBoxLayout()

        if 'added_at' in self.product_data:
            added_label = QLabel(f"📅 추가: {self.product_data['added_at'][:16]}")
            added_label.setFont(QFont('', 8))
            added_label.setStyleSheet(f"color: {MaterialColors.SECONDARY};")
            meta_layout.addWidget(added_label)

        if 'last_rank' in self.product_data:
            rank_info = self.product_data['last_rank']
            if rank_info:
                rank_label = QLabel(f"🏆 최근 순위: {rank_info.get('rank', 'N/A')}위")
                rank_label.setFont(QFont('', 8))
                rank_label.setStyleSheet(f"color: {MaterialColors.SUCCESS};")
                meta_layout.addWidget(rank_label)

        layout.addLayout(header_layout)
        layout.addLayout(meta_layout)

    def request_remove(self):
        """상품 제거 요청"""
        self.remove_requested.emit(self.product_data.get('url', ''))


class BatchSearchWorker(QObject):
    """배치 순위 검색 워커"""
    progress = Signal(int, str)  # percentage, message
    result = Signal(str, dict)  # group_id, results
    finished = Signal(str)  # group_id
    error = Signal(str, str)  # group_id, error_message

    def __init__(self, group_id: str, keyword: str, products: List[Dict]):
        super().__init__()
        self.group_id = group_id
        self.keyword = keyword
        self.products = products
        self.should_stop = False
        self.engine = None

    def set_engine(self, engine):
        """순위 엔진 설정"""
        self.engine = engine

    def stop(self):
        """작업 중지 요청"""
        self.should_stop = True

    def run(self):
        """배치 순위 검색 실행"""
        if not self.engine:
            self.error.emit(self.group_id, "순위 엔진이 설정되지 않았습니다")
            return

        total_products = len(self.products)
        results = {}

        try:
            for i, product in enumerate(self.products):
                if self.should_stop:
                    break

                url = product.get('url', '')
                progress_percent = int((i / total_products) * 100)
                self.progress.emit(progress_percent, f"검색 중: {url[:50]}...")

                try:
                    # 통합 순위 엔진으로 검색
                    result = self.engine.search_instant_rank(self.keyword, url)
                    results[url] = asdict(result) if result else None

                except Exception as e:
                    logging.error(f"상품 {url} 순위 검색 실패: {e}")
                    results[url] = {'error': str(e)}

            # 완료
            self.progress.emit(100, "검색 완료!")
            self.result.emit(self.group_id, results)

        except Exception as e:
            self.error.emit(self.group_id, f"배치 검색 실패: {str(e)}")
        finally:
            self.finished.emit(self.group_id)


class GroupManagementTab(QWidget):
    """그룹 관리 탭 메인 UI"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 데이터 저장 경로
        self.groups_file = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'product_groups.json'
        )

        # 상태 관리
        self.groups = {}  # Dict[str, ProductGroup]
        self.current_group = None
        self.search_workers = {}  # Dict[str, QThread]

        # UI 초기화
        self.init_ui()
        self.load_groups()

    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 좌측: 그룹 목록 및 관리
        left_panel = self.create_left_panel()

        # 우측: 선택된 그룹의 상품 목록 및 검색
        right_panel = self.create_right_panel()

        # 스플리터로 크기 조절 가능
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

    def create_left_panel(self):
        """좌측 그룹 목록 패널 생성"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(panel)

        # 헤더
        header_label = QLabel("📁 상품 그룹 관리")
        header_label.setFont(QFont('', 14, QFont.Bold))
        header_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE}; margin-bottom: 16px;")
        layout.addWidget(header_label)

        # 새 그룹 생성
        new_group_btn = QPushButton("➕ 새 그룹 생성")
        new_group_btn.clicked.connect(self.create_new_group)
        new_group_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5A47A0;
            }}
        """)
        layout.addWidget(new_group_btn)

        # 그룹 목록
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabels(["그룹명", "상품 수", "마지막 확인"])
        self.groups_tree.itemClicked.connect(self.on_group_selected)
        self.groups_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.groups_tree.customContextMenuRequested.connect(self.show_group_context_menu)
        layout.addWidget(self.groups_tree)

        return panel

    def create_right_panel(self):
        """우측 상품 목록 패널 생성"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(panel)

        # 선택된 그룹 정보 헤더
        self.group_info_label = QLabel("그룹을 선택하세요")
        self.group_info_label.setFont(QFont('', 14, QFont.Bold))
        self.group_info_label.setStyleSheet(f"color: {MaterialColors.ON_SURFACE}; margin-bottom: 16px;")
        layout.addWidget(self.group_info_label)

        # 상품 추가 섹션
        add_section = self.create_add_product_section()
        layout.addWidget(add_section)

        # 배치 검색 섹션
        search_section = self.create_batch_search_section()
        layout.addWidget(search_section)

        # 상품 목록 (스크롤 가능)
        self.products_scroll = QScrollArea()
        self.products_container = QWidget()
        self.products_layout = QVBoxLayout(self.products_container)
        self.products_layout.setAlignment(Qt.AlignTop)

        self.products_scroll.setWidget(self.products_container)
        self.products_scroll.setWidgetResizable(True)
        self.products_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 8px;
                background-color: {MaterialColors.SURFACE_VARIANT};
            }}
        """)
        layout.addWidget(self.products_scroll, 1)  # 확장 가능

        return panel

    def create_add_product_section(self):
        """상품 추가 섹션 생성"""
        section = QGroupBox("📦 상품 추가")
        section.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {MaterialColors.ON_SURFACE};
                border: 2px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }}
        """)

        layout = QVBoxLayout(section)

        # URL 입력
        url_layout = QHBoxLayout()
        url_label = QLabel("상품 URL:")
        url_label.setMinimumWidth(80)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("네이버 스마트스토어/카탈로그 URL 입력...")
        self.url_input.returnPressed.connect(self.add_product_to_current_group)

        add_btn = QPushButton("➕ 추가")
        add_btn.clicked.connect(self.add_product_to_current_group)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #45A049;
            }}
        """)

        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input, 1)
        url_layout.addWidget(add_btn)

        layout.addLayout(url_layout)

        return section

    def create_batch_search_section(self):
        """배치 순위 검색 섹션 생성"""
        section = QGroupBox("🔍 배치 순위 검색")
        section.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {MaterialColors.ON_SURFACE};
                border: 2px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }}
        """)

        layout = QVBoxLayout(section)

        # 키워드 입력
        keyword_layout = QHBoxLayout()
        keyword_label = QLabel("검색 키워드:")
        keyword_label.setMinimumWidth(80)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("순위를 확인할 키워드 입력...")

        search_btn = QPushButton("🔍 검색 시작")
        search_btn.clicked.connect(self.start_batch_search)
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5A47A0;
            }}
        """)

        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keyword_input, 1)
        keyword_layout.addWidget(search_btn)

        # 진행 상태
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        self.search_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {MaterialColors.SURFACE_VARIANT};
                border-radius: 8px;
                background-color: {MaterialColors.SURFACE_VARIANT};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {MaterialColors.PRIMARY};
                border-radius: 6px;
            }}
        """)

        self.search_status = QLabel()
        self.search_status.setVisible(False)
        self.search_status.setStyleSheet(f"color: {MaterialColors.SECONDARY}; font-size: 10px;")

        layout.addLayout(keyword_layout)
        layout.addWidget(self.search_progress)
        layout.addWidget(self.search_status)

        return section

    def load_groups(self):
        """저장된 그룹 데이터 로드"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for group_data in data.get('groups', []):
                        group = ProductGroup.from_dict(group_data)
                        self.groups[group.group_id] = group

                logging.info(f"그룹 {len(self.groups)}개 로드 완료")
            else:
                logging.info("그룹 파일이 없습니다. 새로 시작합니다.")
        except Exception as e:
            logging.error(f"그룹 로드 실패: {e}")
            QMessageBox.warning(self, "오류", f"그룹 데이터 로드에 실패했습니다:\n{str(e)}")

        self.refresh_groups_tree()

    def save_groups(self):
        """그룹 데이터 저장"""
        try:
            data = {
                'groups': [group.to_dict() for group in self.groups.values()],
                'saved_at': datetime.now(timezone(timedelta(hours=9))).isoformat()
            }

            os.makedirs(os.path.dirname(self.groups_file), exist_ok=True)
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logging.info(f"그룹 {len(self.groups)}개 저장 완료")
        except Exception as e:
            logging.error(f"그룹 저장 실패: {e}")
            QMessageBox.warning(self, "오류", f"그룹 데이터 저장에 실패했습니다:\n{str(e)}")

    def refresh_groups_tree(self):
        """그룹 목록 트리 새로고침"""
        self.groups_tree.clear()

        for group in self.groups.values():
            item = QTreeWidgetItem([
                group.name,
                str(len(group.products)),
                group.last_checked.strftime("%m-%d %H:%M") if group.last_checked else "없음"
            ])
            item.setData(0, Qt.UserRole, group.group_id)
            self.groups_tree.addTopLevelItem(item)

        # 컬럼 크기 조정
        for i in range(3):
            self.groups_tree.resizeColumnToContents(i)

    def create_new_group(self):
        """새 그룹 생성 다이얼로그"""
        name, ok = QInputDialog.getText(self, "새 그룹 생성", "그룹명을 입력하세요:")
        if ok and name.strip():
            group_id = f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            new_group = ProductGroup(group_id, name.strip())
            self.groups[group_id] = new_group

            self.save_groups()
            self.refresh_groups_tree()

            logging.info(f"새 그룹 생성: {name}")

    def on_group_selected(self, item, column):
        """그룹 선택 시 처리"""
        group_id = item.data(0, Qt.UserRole)
        if group_id in self.groups:
            self.current_group = self.groups[group_id]
            self.update_group_info()
            self.refresh_products_list()

    def update_group_info(self):
        """선택된 그룹 정보 업데이트"""
        if self.current_group:
            info_text = f"📁 {self.current_group.name} ({len(self.current_group.products)}개 상품)"
            if self.current_group.description:
                info_text += f"\n💬 {self.current_group.description}"
            self.group_info_label.setText(info_text)
        else:
            self.group_info_label.setText("그룹을 선택하세요")

    def refresh_products_list(self):
        """상품 목록 새로고침"""
        # 기존 위젯들 제거
        for i in reversed(range(self.products_layout.count())):
            child = self.products_layout.takeAt(i).widget()
            if child:
                child.deleteLater()

        if not self.current_group:
            empty_label = QLabel("선택된 그룹이 없습니다")
            empty_label.setStyleSheet(f"color: {MaterialColors.SECONDARY}; text-align: center; padding: 40px;")
            self.products_layout.addWidget(empty_label)
            return

        if not self.current_group.products:
            empty_label = QLabel("이 그룹에 상품이 없습니다")
            empty_label.setStyleSheet(f"color: {MaterialColors.SECONDARY}; text-align: center; padding: 40px;")
            self.products_layout.addWidget(empty_label)
            return

        # 상품 카드들 생성
        for product in self.current_group.products:
            card = ProductCard(product)
            card.remove_requested.connect(self.remove_product_from_group)
            self.products_layout.addWidget(card)

    def add_product_to_current_group(self):
        """현재 그룹에 상품 추가"""
        if not self.current_group:
            QMessageBox.warning(self, "경고", "먼저 그룹을 선택하세요.")
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "경고", "상품 URL을 입력하세요.")
            return

        # 중복 확인
        for product in self.current_group.products:
            if product.get('url') == url:
                QMessageBox.warning(self, "경고", "이미 추가된 상품입니다.")
                return

        # 상품 추가
        product_data = {
            'url': url,
            'added_at': datetime.now(timezone(timedelta(hours=9))).isoformat(),
            'last_rank': None
        }

        self.current_group.products.append(product_data)
        self.save_groups()
        self.refresh_groups_tree()
        self.refresh_products_list()

        # 입력 필드 초기화
        self.url_input.clear()

        logging.info(f"상품 추가: {url} → {self.current_group.name}")

    def remove_product_from_group(self, url: str):
        """그룹에서 상품 제거"""
        if not self.current_group:
            return

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self, "상품 제거",
            f"다음 상품을 그룹에서 제거하시겠습니까?\n\n{url}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 상품 제거
            self.current_group.products = [
                p for p in self.current_group.products if p.get('url') != url
            ]

            self.save_groups()
            self.refresh_groups_tree()
            self.refresh_products_list()

            logging.info(f"상품 제거: {url} ← {self.current_group.name}")

    def show_group_context_menu(self, position):
        """그룹 우클릭 컨텍스트 메뉴"""
        item = self.groups_tree.itemAt(position)
        if not item:
            return

        group_id = item.data(0, Qt.UserRole)
        if group_id not in self.groups:
            return

        menu = QMenu(self)

        # 그룹 이름 변경
        rename_action = QAction("📝 이름 변경", self)
        rename_action.triggered.connect(lambda: self.rename_group(group_id))
        menu.addAction(rename_action)

        # 그룹 삭제
        delete_action = QAction("🗑️ 그룹 삭제", self)
        delete_action.triggered.connect(lambda: self.delete_group(group_id))
        menu.addAction(delete_action)

        menu.exec_(self.groups_tree.mapToGlobal(position))

    def rename_group(self, group_id: str):
        """그룹 이름 변경"""
        group = self.groups[group_id]
        new_name, ok = QInputDialog.getText(
            self, "그룹 이름 변경", f"새 그룹명:", text=group.name
        )

        if ok and new_name.strip() and new_name.strip() != group.name:
            group.name = new_name.strip()
            self.save_groups()
            self.refresh_groups_tree()
            self.update_group_info()

            logging.info(f"그룹 이름 변경: {group_id} → {new_name}")

    def delete_group(self, group_id: str):
        """그룹 삭제"""
        group = self.groups[group_id]
        reply = QMessageBox.question(
            self, "그룹 삭제",
            f"'{group.name}' 그룹을 삭제하시겠습니까?\n\n"
            f"그룹에 포함된 {len(group.products)}개 상품 정보도 함께 삭제됩니다.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.groups[group_id]
            self.save_groups()
            self.refresh_groups_tree()

            # 현재 선택된 그룹이었다면 초기화
            if self.current_group and self.current_group.group_id == group_id:
                self.current_group = None
                self.update_group_info()
                self.refresh_products_list()

            logging.info(f"그룹 삭제: {group.name}")

    def start_batch_search(self):
        """배치 순위 검색 시작"""
        if not self.current_group:
            QMessageBox.warning(self, "경고", "먼저 그룹을 선택하세요.")
            return

        if not self.current_group.products:
            QMessageBox.warning(self, "경고", "그룹에 상품이 없습니다.")
            return

        keyword = self.keyword_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "경고", "검색 키워드를 입력하세요.")
            return

        # 이미 검색 중인지 확인
        if self.current_group.group_id in self.search_workers:
            QMessageBox.information(self, "알림", "이미 이 그룹의 검색이 진행 중입니다.")
            return

        # UI 상태 업데이트
        self.search_progress.setVisible(True)
        self.search_progress.setValue(0)
        self.search_status.setVisible(True)
        self.search_status.setText("검색 준비 중...")

        # 워커 스레드 생성 및 시작
        thread = QThread()
        worker = BatchSearchWorker(
            self.current_group.group_id, keyword, self.current_group.products
        )

        # 순위 엔진 설정 (실제 환경에서는 부모에서 전달받아야 함)
        try:
            if UnifiedRankEngine:
                engine = UnifiedRankEngine()
                worker.set_engine(engine)
        except Exception as e:
            logging.error(f"순위 엔진 초기화 실패: {e}")

        worker.moveToThread(thread)

        # 시그널 연결
        thread.started.connect(worker.run)
        worker.progress.connect(self.on_search_progress)
        worker.result.connect(self.on_search_result)
        worker.error.connect(self.on_search_error)
        worker.finished.connect(lambda group_id: self.on_search_finished(group_id, thread, worker))

        # 스레드 저장 및 시작
        self.search_workers[self.current_group.group_id] = thread
        thread.start()

        logging.info(f"배치 검색 시작: {keyword} - {len(self.current_group.products)}개 상품")

    def on_search_progress(self, percentage: int, message: str):
        """검색 진행 상황 업데이트"""
        self.search_progress.setValue(percentage)
        self.search_status.setText(message)

    def on_search_result(self, group_id: str, results: Dict):
        """검색 결과 처리"""
        if group_id in self.groups:
            group = self.groups[group_id]
            group.last_checked = datetime.now(timezone(timedelta(hours=9)))

            # 각 상품의 last_rank 업데이트
            for product in group.products:
                url = product.get('url')
                if url in results and results[url]:
                    product['last_rank'] = results[url]

            self.save_groups()
            self.refresh_groups_tree()
            self.refresh_products_list()

            logging.info(f"배치 검색 완료: {group.name}")

    def on_search_error(self, group_id: str, error_message: str):
        """검색 오류 처리"""
        QMessageBox.critical(self, "검색 오류", f"배치 검색 중 오류가 발생했습니다:\n\n{error_message}")
        logging.error(f"배치 검색 오류: {group_id} - {error_message}")

    def on_search_finished(self, group_id: str, thread: QThread, worker: BatchSearchWorker):
        """검색 완료 후 정리"""
        # UI 상태 초기화
        self.search_progress.setVisible(False)
        self.search_status.setVisible(False)

        # 스레드 정리
        if group_id in self.search_workers:
            del self.search_workers[group_id]

        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()

        logging.info(f"검색 스레드 정리 완료: {group_id}")

    def closeEvent(self, event):
        """탭 종료 시 리소스 정리"""
        # 실행 중인 검색 작업들 중지
        for thread in self.search_workers.values():
            if thread.isRunning():
                thread.quit()
                thread.wait(3000)  # 3초 대기

        self.save_groups()
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

    widget = GroupManagementTab()
    widget.show()

    sys.exit(app.exec())