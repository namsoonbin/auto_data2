import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# qt-material 및 qtawesome import
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

# Material Design 3 Color System
class MaterialColors:
    PRIMARY = "#2563eb"
    SUCCESS = "#059669" 
    WARNING = "#ea580c"
    ERROR = "#dc2626"
    LIGHT_SURFACE = "#ffffff"
    LIGHT_TEXT = "#1f2937"

class ModernButton(QPushButton):
    """Material Design 스타일 버튼"""
    def __init__(self, text, color=MaterialColors.PRIMARY, parent=None):
        super().__init__(text, parent)
        
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
                background-color: #1d4ed8;
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
        """)

class ModernCard(QFrame):
    """Material Design 카드"""
    def __init__(self, title, content):
        super().__init__()
        self.setFixedHeight(150)
        
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
                padding: 20px;
            }}
            QFrame:hover {{
                border-color: {MaterialColors.PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {MaterialColors.PRIMARY};
            margin-bottom: 10px;
        """)
        
        content_label = QLabel(content)
        content_label.setStyleSheet(f"""
            font-size: 14px;
            color: {MaterialColors.LIGHT_TEXT};
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addStretch()

class TestApp(QMainWindow):
    """테스트 애플리케이션"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Material Design 3 테스트")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 헤더
        header = QLabel("🎨 Material Design 3 변환 테스트")
        header.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {MaterialColors.PRIMARY};
            padding: 20px;
            text-align: center;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # 상태 표시
        status_layout = QVBoxLayout()
        
        # 라이브러리 상태
        qt_status = "✅ qt-material 사용 가능" if QT_MATERIAL_AVAILABLE else "❌ qt-material 사용 불가"
        qta_status = "✅ qtawesome 사용 가능" if QTAWESOME_AVAILABLE else "❌ qtawesome 사용 불가"
        
        status_label = QLabel(f"""
        <div style='font-size: 16px; padding: 20px;'>
            <p><b>라이브러리 상태:</b></p>
            <p>{qt_status}</p>
            <p>{qta_status}</p>
            <p>✅ PySide6 사용 가능</p>
        </div>
        """)
        status_label.setStyleSheet(f"""
            background-color: {MaterialColors.LIGHT_SURFACE};
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            padding: 20px;
        """)
        
        status_layout.addWidget(status_label)
        layout.addLayout(status_layout)
        
        # 카드 테스트
        cards_layout = QHBoxLayout()
        
        card1 = ModernCard("테스트 카드 1", "Material Design 3 스타일 적용")
        card2 = ModernCard("테스트 카드 2", "현대적인 UI 컴포넌트")
        card3 = ModernCard("테스트 카드 3", "그림자 효과 및 호버 상태")
        
        cards_layout.addWidget(card1)
        cards_layout.addWidget(card2)
        cards_layout.addWidget(card3)
        
        layout.addLayout(cards_layout)
        
        # 버튼 테스트
        buttons_layout = QHBoxLayout()
        
        btn1 = ModernButton("Primary 버튼", MaterialColors.PRIMARY)
        btn2 = ModernButton("Success 버튼", MaterialColors.SUCCESS)
        btn3 = ModernButton("Warning 버튼", MaterialColors.WARNING)
        btn4 = ModernButton("Error 버튼", MaterialColors.ERROR)
        
        buttons_layout.addWidget(btn1)
        buttons_layout.addWidget(btn2)
        buttons_layout.addWidget(btn3)
        buttons_layout.addWidget(btn4)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # 결과 표시
        result_label = QLabel("🎉 Material Design 3 변환이 성공적으로 완료되었습니다!")
        result_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {MaterialColors.SUCCESS};
            padding: 20px;
            background-color: #f0fdf4;
            border: 2px solid {MaterialColors.SUCCESS};
            border-radius: 8px;
            text-align: center;
        """)
        result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(result_label)
        
        layout.addStretch()

def main():
    app = QApplication(sys.argv)
    
    # qt-material 테마 적용 시도
    if QT_MATERIAL_AVAILABLE:
        try:
            apply_stylesheet(app, theme='dark_teal.xml')
            print("✅ Material Design 테마 적용 완료")
        except Exception as e:
            print(f"⚠️ 테마 적용 실패: {e}")
    
    window = TestApp()
    window.show()
    
    print("🚀 테스트 애플리케이션 실행 중...")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())