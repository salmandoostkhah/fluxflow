from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QProgressBar, QFrame, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

def create_test_tab(parent):
    test_tab = QWidget()
    layout = QVBoxLayout(test_tab)
    layout.setSpacing(20)
    layout.setContentsMargins(30, 30, 30, 30)

    # عنوان
    title = QLabel("FluxFlow Network Speed Tester")
    title.setAccessibleName("title")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, 180))
    title.setGraphicsEffect(shadow)

    # دکمه شروع تست
    btn_layout = QHBoxLayout()
    parent.start_btn = QPushButton("Start Test")
    parent.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_layout.addStretch()
    btn_layout.addWidget(parent.start_btn)
    btn_layout.addStretch()
    layout.addLayout(btn_layout)

    # اتصال کلیک دکمه — این خط خیلی مهمه!
    parent.start_btn.clicked.connect(parent.start_test)

    # Progress Bar
    parent.progress_bar = QProgressBar()
    parent.progress_bar.setRange(0, 100)
    parent.progress_bar.setVisible(False)
    layout.addWidget(parent.progress_bar)

    # کادر خروجی
    frame = QFrame()
    frame.setStyleSheet("background: rgba(30, 30, 30, 0.7); border-radius: 20px; border: 1px solid #42a5f5;")
    frame_layout = QVBoxLayout(frame)
    parent.text_area = QTextEdit()
    parent.text_area.setReadOnly(True)
    frame_layout.addWidget(parent.text_area)
    layout.addWidget(frame)

    # سایه برای دکمه
    btn_shadow = QGraphicsDropShadowEffect()
    btn_shadow.setBlurRadius(25)
    btn_shadow.setXOffset(0)
    btn_shadow.setYOffset(8)
    btn_shadow.setColor(QColor(0, 0, 0, 160))
    parent.start_btn.setGraphicsEffect(btn_shadow)

    return test_tab