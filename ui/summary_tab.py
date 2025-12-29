from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QDateEdit, QTimeEdit, QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QTime
import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH, PAGE_SIZE, FLAG_EMOJIS, BASE_DIR

def create_summary_tab(parent):
    summary_tab = QWidget()
    s_layout = QVBoxLayout(summary_tab)
    s_layout.setContentsMargins(25, 25, 25, 25)

    # فیلترها
    filter_layout = QHBoxLayout()
    QLabel("From:").setStyleSheet("color: #d0d0d0;")
    parent.date_from = QDateEdit()
    parent.date_from.setDate(QDate(2000, 1, 1))
    parent.date_from.setCalendarPopup(True)
    parent.time_from = QTimeEdit()
    parent.time_from.setTime(QTime(0, 0))

    QLabel("To:").setStyleSheet("color: #d0d0d0;")
    parent.date_to = QDateEdit()
    parent.date_to.setDate(QDate.currentDate())
    parent.date_to.setCalendarPopup(True)
    parent.time_to = QTimeEdit()
    parent.time_to.setTime(QTime(23, 59))

    parent.search_edit = QLineEdit()
    parent.search_edit.setPlaceholderText("Search ISP/Country...")

    filter_btn = QPushButton("Filter")
    filter_btn.clicked.connect(parent.filter_summary)
    clear_btn = QPushButton("Clear")
    clear_btn.clicked.connect(parent.clear_filter)

    for w in [parent.date_from, parent.date_to, parent.time_from, parent.time_to, parent.search_edit]:
        filter_layout.addWidget(w)
    filter_layout.addWidget(filter_btn)
    filter_layout.addWidget(clear_btn)
    s_layout.addLayout(filter_layout)

    # جدول
    parent.summary_table = QTableWidget()
    parent.summary_table.setColumnCount(12)
    headers = ["ID", "Time", "Down", "Up", "Jitter", "Ping", "Loss", "ISP / Country", "IP", "DNS Server", "DNS Resp", "Actions"]
    parent.summary_table.setHorizontalHeaderLabels(headers)
    parent.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    s_layout.addWidget(parent.summary_table)

    # صفحه‌بندی
    page_layout = QHBoxLayout()
    parent.prev_page_btn = QPushButton("Previous")
    parent.prev_page_btn.clicked.connect(parent.prev_page)
    parent.page_label = QLabel("Page 1")
    parent.next_page_btn = QPushButton("Next")
    parent.next_page_btn.clicked.connect(parent.next_page)
    page_layout.addStretch()
    page_layout.addWidget(parent.prev_page_btn)
    page_layout.addWidget(parent.page_label)
    page_layout.addWidget(parent.next_page_btn)
    page_layout.addStretch()
    s_layout.addLayout(page_layout)

    # دکمه‌های اکسپورت و ایمپورت
    export_import_layout = QHBoxLayout()
    export_btn = QPushButton("Export to Excel")
    export_btn.clicked.connect(parent.export_to_excel)
    import_btn = QPushButton("Import from Excel")
    import_btn.clicked.connect(parent.import_from_excel)
    export_import_layout.addStretch()
    export_import_layout.addWidget(export_btn)
    export_import_layout.addWidget(import_btn)
    export_import_layout.addStretch()
    s_layout.addLayout(export_import_layout)

    parent.current_page = 0
    return summary_tab

# توابع load, filter, export, import رو در main_window.py می‌ذاریم چون به parent دسترسی دارن