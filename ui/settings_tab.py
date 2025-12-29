from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout,
    QPushButton, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt

def create_settings_tab(parent):
    settings_tab = QWidget()
    settings_layout = QVBoxLayout(settings_tab)
    settings_layout.setContentsMargins(30, 30, 30, 30)
    settings_layout.setSpacing(20)

    title = QLabel("Settings | تنظیمات تست")
    title.setStyleSheet("font-size: 22px; font-weight: bold; color: #4fc3f7;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    settings_layout.addWidget(title)

    # چک‌باکس‌ها
    parent.download_cb = QCheckBox("Download Speed Test | تست سرعت دانلود")
    parent.upload_cb = QCheckBox("Upload Speed Test | تست سرعت آپلود")
    parent.jitter_cb = QCheckBox("Jitter Test | تست جتر")
    parent.ping_cb = QCheckBox("Ping & Packet Loss | پینگ و از دست رفتن پکت")
    parent.dns_cb = QCheckBox("DNS Response Time | زمان پاسخ DNS")
    parent.location_cb = QCheckBox("Location & ISP Detection | تشخیص کشور و ISP")

    for cb in [parent.download_cb, parent.upload_cb, parent.jitter_cb,
               parent.ping_cb, parent.dns_cb, parent.location_cb]:
        cb.setChecked(True)
        cb.setStyleSheet("font-size: 14px;")
        settings_layout.addWidget(cb)

    # Jitter Samples
    jitter_layout = QHBoxLayout()
    jitter_label = QLabel("Jitter Samples | تعداد نمونه‌های جتر:")
    parent.jitter_samples_slider = QSlider(Qt.Orientation.Horizontal)
    parent.jitter_samples_slider.setRange(5, 30)
    parent.jitter_samples_slider.setValue(10)
    parent.jitter_value_label = QLabel("10")
    parent.jitter_samples_slider.valueChanged.connect(lambda v: parent.jitter_value_label.setText(str(v)))

    jitter_layout.addWidget(jitter_label)
    jitter_layout.addWidget(parent.jitter_samples_slider)
    jitter_layout.addWidget(parent.jitter_value_label)
    settings_layout.addLayout(jitter_layout)

    # دکمه اعمال تنظیمات
    apply_btn = QPushButton("Apply Settings | اعمال تنظیمات")
    apply_btn.clicked.connect(parent.apply_settings)
    apply_btn.setStyleSheet("""
        QPushButton { padding: 14px; font-size: 16px; background-color: #42a5f7; color: white; border-radius: 12px; }
        QPushButton:hover { background-color: #2196f3; }
    """)
    settings_layout.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    settings_layout.addSpacing(25)

    # دکمه چک آپدیت
    update_btn = QPushButton("Check for Updates | چک کردن آپدیت جدید")
    update_btn.setStyleSheet("""
        QPushButton { padding: 16px; font-size: 16px; font-weight: bold; background-color: #42a5f7; color: white; border-radius: 14px; min-width: 350px; }
        QPushButton:hover { background-color: #2196f3; }
        QPushButton:pressed { background-color: #1976d2; }
    """)
    update_btn.clicked.connect(lambda: parent.check_for_updates(silent=False))
    settings_layout.addWidget(update_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    settings_layout.addStretch()

    return settings_tab