# -*- coding: utf-8 -*-
"""
사용자 친화적 UI 컴포넌트 시스템
Context7 2025 모범 사례: 타입 안전성, 재사용성, 접근성
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QProgressBar, QFrame, QGraphicsDropShadowEffect, QApplication,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect,
    QParallelAnimationGroup, Signal, QPoint
)
from PySide6.QtGui import QFont, QPalette, QPixmap, QPainter, QIcon

from .logger import get_logger

logger = get_logger("UIComponents")


class NotificationType(Enum):
    """알림 타입 정의"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class WorkflowStep(Enum):
    """워크플로우 단계 정의"""
    FOLDER_SETUP = "folder_setup"
    AUTOMATION_START = "automation_start"
    MONITORING = "monitoring"  # 모니터링 단계 추가
    RESULT_CHECK = "result_check"
    ADVANCED_FEATURES = "advanced_features"


@dataclass
class NotificationConfig:
    """알림 설정"""
    title: str
    message: str
    notification_type: NotificationType
    duration_ms: int = 3000
    auto_hide: bool = True
    action_text: Optional[str] = None
    action_callback: Optional[Callable] = None


@dataclass
class StepGuideConfig:
    """단계 가이드 설정"""
    current_step: WorkflowStep
    total_steps: int
    title: str
    description: str
    next_action: Optional[str] = None
    show_progress: bool = True


class ModernToastNotification(QFrame):
    """
    Context7 모범 사례 적용 토스트 알림
    - 타입 안전성
    - 애니메이션 최적화
    - 접근성 지원
    """

    # 클래스 레벨 스타일 상수
    STYLES = {
        NotificationType.SUCCESS: {
            "background": "#059669",
            "border": "#047857",
            "icon": "✅"
        },
        NotificationType.WARNING: {
            "background": "#d97706",
            "border": "#b45309",
            "icon": "⚠️"
        },
        NotificationType.ERROR: {
            "background": "#dc2626",
            "border": "#b91c1c",
            "icon": "❌"
        },
        NotificationType.INFO: {
            "background": "#2563eb",
            "border": "#1d4ed8",
            "icon": "ℹ️"
        }
    }

    def __init__(self, config: NotificationConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.setup_animations()

        # 자동 숨김 타이머
        if config.auto_hide:
            QTimer.singleShot(config.duration_ms, self.hide_with_animation)

    def setup_ui(self) -> None:
        """UI 구성"""
        self.setFixedSize(400, 80)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 메인 레이아웃
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 아이콘
        style = self.STYLES[self.config.notification_type]
        icon_label = QLabel(style["icon"])
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)

        # 텍스트 컨테이너
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        # 제목
        title_label = QLabel(self.config.title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: white;
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        """)

        # 메시지
        message_label = QLabel(self.config.message)
        message_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.9);
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        """)
        message_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(message_label)

        # 액션 버튼 (옵션)
        if self.config.action_text and self.config.action_callback:
            action_btn = QPushButton(self.config.action_text)
            action_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    color: white;
                    font-size: 11px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
            """)
            action_btn.clicked.connect(self.config.action_callback)
            layout.addWidget(action_btn)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)

        # 스타일 적용
        self.setStyleSheet(f"""
            ModernToastNotification {{
                background-color: {style["background"]};
                border: 2px solid {style["border"]};
                border-radius: 8px;
            }}
        """)

        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(Qt.black)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def setup_animations(self) -> None:
        """애니메이션 설정"""
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.slide_animation.setDuration(300)

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.setDuration(200)

    def show_at_position(self, parent_widget: QWidget) -> None:
        """지정된 위치에 표시"""
        if not parent_widget:
            return

        # 부모 위젯의 우상단에 표시
        parent_rect = parent_widget.geometry()
        start_pos = QPoint(
            parent_rect.right() - self.width() - 20,
            parent_rect.top() + 20
        )
        end_pos = start_pos

        # 시작 위치 (화면 밖)
        start_rect = QRect(start_pos.x() + 100, start_pos.y(), self.width(), self.height())
        end_rect = QRect(end_pos.x(), end_pos.y(), self.width(), self.height())

        self.setGeometry(start_rect)
        self.show()

        # 슬라이드 인 애니메이션
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        self.slide_animation.start()

    def hide_with_animation(self) -> None:
        """애니메이션과 함께 숨김"""
        def on_finished():
            self.hide()
            self.deleteLater()

        self.fade_animation.finished.connect(on_finished)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()


class WorkflowProgressGuide(QFrame):
    """
    Context7 모범 사례 적용 워크플로우 가이드
    - 명확한 진행 상태
    - 접근성 지원
    - 반응형 디자인
    """

    # Signal 정의
    step_completed = Signal(WorkflowStep)
    next_action_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_config: Optional[StepGuideConfig] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """UI 구성"""
        self.setFixedHeight(100)
        self.setStyleSheet("""
            WorkflowProgressGuide {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f1f5f9);
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin: 4px;
            }
        """)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(8)

        # 진행률 표시
        self.progress_container = QHBoxLayout()
        self.progress_container.setSpacing(8)
        main_layout.addLayout(self.progress_container)

        # 설명 텍스트
        text_layout = QHBoxLayout()
        text_layout.setSpacing(12)

        self.step_label = QLabel()
        self.step_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
        """)

        self.description_label = QLabel()
        self.description_label.setStyleSheet("""
            font-size: 13px;
            color: #1e293b;
            font-weight: 500;
        """)

        # 다음 액션 버튼
        self.action_button = QPushButton()
        self.action_button.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
        """)
        self.action_button.clicked.connect(self._on_action_clicked)
        self.action_button.hide()

        text_layout.addWidget(self.step_label, 0)
        text_layout.addWidget(self.description_label, 1)
        text_layout.addWidget(self.action_button, 0)

        main_layout.addLayout(text_layout)

    def update_step(self, config: StepGuideConfig) -> None:
        """단계 업데이트"""
        self.current_config = config

        # 진행률 표시 업데이트
        self._update_progress_indicators(config)

        # 텍스트 업데이트
        self.step_label.setText(config.title)
        self.description_label.setText(config.description)

        # 액션 버튼 업데이트
        if config.next_action:
            self.action_button.setText(config.next_action)
            self.action_button.show()
        else:
            self.action_button.hide()

        logger.info("워크플로우 단계 업데이트",
                   step=config.current_step.value,
                   title=config.title)

    def _update_progress_indicators(self, config: StepGuideConfig) -> None:
        """진행률 표시기 업데이트"""
        # 기존 인디케이터 제거
        self._clear_layout(self.progress_container)

        if not config.show_progress:
            return

        # 각 단계별 인디케이터 생성
        steps = list(WorkflowStep)
        current_index = steps.index(config.current_step)

        for i, step in enumerate(steps):
            # 원형 인디케이터
            indicator = QLabel()
            indicator.setFixedSize(24, 24)
            indicator.setAlignment(Qt.AlignCenter)

            if i < current_index:
                # 완료된 단계
                indicator.setStyleSheet("""
                    background: #10b981;
                    color: white;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                """)
                indicator.setText("✓")
            elif i == current_index:
                # 현재 단계
                indicator.setStyleSheet("""
                    background: #3b82f6;
                    color: white;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: 600;
                """)
                indicator.setText(str(i + 1))
            else:
                # 대기 단계
                indicator.setStyleSheet("""
                    background: #e2e8f0;
                    color: #94a3b8;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: 600;
                """)
                indicator.setText(str(i + 1))

            self.progress_container.addWidget(indicator)

            # 연결선 (마지막 단계 제외)
            if i < len(steps) - 1:
                line = QFrame()
                line.setFixedSize(30, 2)
                line.setStyleSheet(f"""
                    background: {'#10b981' if i < current_index else '#e2e8f0'};
                    border: none;
                """)
                self.progress_container.addWidget(line)

        # 오른쪽 여백
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.progress_container.addItem(spacer)

    def _clear_layout(self, layout: QHBoxLayout) -> None:
        """레이아웃 내용 지우기"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.spacerItem():
                del child

    def _on_action_clicked(self) -> None:
        """액션 버튼 클릭 처리"""
        if self.current_config and self.current_config.next_action:
            self.next_action_requested.emit(self.current_config.next_action)

    def mark_step_completed(self, step: WorkflowStep) -> None:
        """단계 완료 표시"""
        self.step_completed.emit(step)
        logger.info("워크플로우 단계 완료", step=step.value)


class SmartTooltipManager:
    """
    Context7 모범 사례 적용 스마트 툴팁 관리자
    - 상황별 맞춤 도움말
    - 타입 안전성
    - 확장 가능한 구조
    """

    def __init__(self):
        self.tooltip_configs: Dict[str, Dict[str, str]] = {
            "folder_selection": {
                "empty": "📁 Excel 파일이 있는 다운로드 폴더를 선택해주세요",
                "selected": "✅ 폴더가 선택되었습니다. 이제 자동화를 시작할 수 있습니다",
                "invalid": "⚠️ 선택한 폴더에 Excel 파일이 없습니다"
            },
            "automation_button": {
                "ready": "🚀 자동화를 시작합니다. Excel 파일을 자동으로 처리합니다",
                "running": "⏸️ 자동화가 실행 중입니다. 중지하려면 클릭하세요",
                "disabled": "⚠️ 먼저 폴더를 선택해주세요"
            },
            "password_input": {
                "default": "🔒 주문조회 파일의 암호를 입력하세요 (기본: 1234)",
                "invalid": "❌ 잘못된 암호입니다. 파일을 열 수 없습니다"
            }
        }

    def get_tooltip(self, component: str, state: str) -> str:
        """상황별 툴팁 반환"""
        return self.tooltip_configs.get(component, {}).get(state, "")

    def update_tooltip(self, widget: QWidget, component: str, state: str) -> None:
        """위젯 툴팁 업데이트"""
        tooltip_text = self.get_tooltip(component, state)
        if tooltip_text:
            widget.setToolTip(tooltip_text)
            logger.debug("툴팁 업데이트", component=component, state=state)


class NotificationManager:
    """
    Context7 모범 사례 적용 알림 관리자
    - 중앙 집중식 알림 관리
    - 큐 기반 순차 표시
    - 메모리 효율성
    """

    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.active_notifications: List[ModernToastNotification] = []
        self.notification_queue: List[NotificationConfig] = []
        self.max_simultaneous = 3

    def show_notification(self, config: NotificationConfig) -> None:
        """알림 표시"""
        if len(self.active_notifications) >= self.max_simultaneous:
            self.notification_queue.append(config)
            return

        notification = ModernToastNotification(config, self.parent_widget)
        notification.show_at_position(self.parent_widget)

        self.active_notifications.append(notification)

        # 알림 종료 시 큐에서 다음 알림 표시
        def on_notification_finished():
            if notification in self.active_notifications:
                self.active_notifications.remove(notification)
            self._show_next_from_queue()

        notification.fade_animation.finished.connect(on_notification_finished)

        logger.info("알림 표시",
                   type=config.notification_type.value,
                   title=config.title)

    def _show_next_from_queue(self) -> None:
        """큐에서 다음 알림 표시"""
        if self.notification_queue and len(self.active_notifications) < self.max_simultaneous:
            next_config = self.notification_queue.pop(0)
            self.show_notification(next_config)

    def clear_all(self) -> None:
        """모든 알림 지우기"""
        for notification in self.active_notifications:
            notification.hide_with_animation()
        self.active_notifications.clear()
        self.notification_queue.clear()


# Context7 모범 사례: 팩토리 패턴
class UIComponentFactory:
    """UI 컴포넌트 팩토리"""

    @staticmethod
    def create_success_notification(title: str, message: str, **kwargs) -> NotificationConfig:
        """성공 알림 생성"""
        return NotificationConfig(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            **kwargs
        )

    @staticmethod
    def create_error_notification(title: str, message: str, **kwargs) -> NotificationConfig:
        """오류 알림 생성"""
        return NotificationConfig(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            auto_hide=False,  # 오류는 수동으로 닫기
            **kwargs
        )

    @staticmethod
    def create_step_guide(step: WorkflowStep, title: str, description: str, **kwargs) -> StepGuideConfig:
        """단계 가이드 생성"""
        return StepGuideConfig(
            current_step=step,
            total_steps=len(WorkflowStep),
            title=title,
            description=description,
            **kwargs
        )