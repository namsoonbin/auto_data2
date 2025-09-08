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
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
        """)

class TestApp(QMainWindow):
    """테스트 애플리케이션"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Material Design 3 테스트")
        self.setMinimumSize(1000, 600)
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # 헤더
        header = QLabel("Material Design 3 변환 테스트")
        header.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {MaterialColors.PRIMARY};
            padding: 20px;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # 상태 카드
        status_card = QFrame()
        status_card.setStyleSheet(f"""
            QFrame {{
                background-color: {MaterialColors.LIGHT_SURFACE};
                border: 2px solid {MaterialColors.PRIMARY};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        status_layout = QVBoxLayout(status_card)
        
        qt_status = "OK" if QT_MATERIAL_AVAILABLE else "ERROR"
        qta_status = "OK" if QTAWESOME_AVAILABLE else "ERROR"
        
        status_text = f"""
        라이브러리 상태 확인:
        • qt-material: {qt_status}
        • qtawesome: {qta_status}
        • PySide6: OK
        """
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet("font-size: 16px; color: #333;")
        status_layout.addWidget(status_label)
        
        layout.addWidget(status_card)
        
        # 버튼 테스트
        buttons_layout = QHBoxLayout()
        
        btn1 = ModernButton("Primary", MaterialColors.PRIMARY)
        btn2 = ModernButton("Success", MaterialColors.SUCCESS)
        btn3 = ModernButton("Warning", MaterialColors.WARNING)
        btn4 = ModernButton("Error", MaterialColors.ERROR)
        
        btn1.clicked.connect(lambda: print("Primary 버튼 클릭됨"))
        btn2.clicked.connect(lambda: print("Success 버튼 클릭됨"))
        btn3.clicked.connect(lambda: print("Warning 버튼 클릭됨"))
        btn4.clicked.connect(lambda: print("Error 버튼 클릭됨"))
        
        buttons_layout.addWidget(btn1)
        buttons_layout.addWidget(btn2)
        buttons_layout.addWidget(btn3)
        buttons_layout.addWidget(btn4)
        
        layout.addLayout(buttons_layout)
        
        # 결과 표시
        result_label = QLabel("Material Design 3 변환이 성공적으로 완료되었습니다!")
        result_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {MaterialColors.SUCCESS};
            padding: 20px;
            background-color: #f0fdf4;
            border: 2px solid {MaterialColors.SUCCESS};
            border-radius: 8px;
        """)
        result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(result_label)

def main():
    app = QApplication(sys.argv)
    
    # qt-material 테마 적용 시도
    if QT_MATERIAL_AVAILABLE:
        try:
            apply_stylesheet(app, theme='dark_teal.xml')
            print("Material Design 테마 적용 완료")
        except Exception as e:
            print(f"테마 적용 실패: {e}")
    else:
        print("qt-material 없이 기본 스타일로 실행")
    
    window = TestApp()
    window.show()
    
    print("테스트 애플리케이션 실행 중...")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())