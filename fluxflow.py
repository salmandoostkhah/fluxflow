import sys
import os
import re
from pathlib import Path
import json
import random
import statistics
import tempfile
import platform
import subprocess
from datetime import datetime

import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dns import resolver

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit,
    QHBoxLayout, QLabel, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QDateEdit, QTimeEdit, QLineEdit, QHeaderView, QProgressBar, QCheckBox, QSpinBox,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate, QTime
from PyQt6.QtGui import QPixmap, QColor

# تنظیمات
DB_PATH = 'fluxflow_tests.db'
SETTINGS_PATH = 'settings.json'

# پرچم کشورها
FLAG_EMOJIS = {
    'Iran': '🇮🇷',
    'United States': '🇺🇸',
    'Germany': '🇩🇪',
    'United Kingdom': '🇬🇧',
    'France': '🇫🇷',
    'India': '🇮🇳',
    'China': '🇨🇳',
    'Japan': '🇯🇵',
    'Brazil': '🇧🇷',
    'Canada': '🇨🇦',
    'Australia': '🇦🇺',
    'Russia': '🇷🇺',
    'Italy': '🇮🇹',
    'Spain': '🇪🇸',
    'Unknown': '🌍'
}

# --- مسیرها با pathlib ---
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "fluxflow_tests.db"
SETTINGS_PATH = BASE_DIR / "settings.json"
GRAPH_TEMP_PATH = Path(tempfile.gettempdir()) / "fluxflow_graph.png"

# --- گرفتن DNS سرور سیستم ---
def get_system_dns():
    system = platform.system().lower()
    dns_servers = []

    try:
        if system == "windows":
            # بدون shell=True — امن
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True,
                text=True,
                encoding='cp1256',
                errors='ignore'
            )
            output = result.stdout
            for line in output.splitlines():
                if "DNS Servers" in line or "سرورهای DNS" in line:
                    ip_part = line.split(":", 1)[-1].strip()
                    ip = ip_part.split()[0] if ip_part else ""
                    if ip and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                        dns_servers.append(ip)

        elif system == "linux":
            resolv_path = "/etc/resolv.conf"
            if os.path.exists(resolv_path):
                with open(resolv_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("nameserver"):
                            ip = line.split(maxsplit=1)[1]
                            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                                dns_servers.append(ip)

        elif system == "darwin":  # macOS
            result = subprocess.run(
                ["scutil", "--dns"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            for line in result.stdout.splitlines():
                if "nameserver" in line.lower():
                    ip = line.split(":", 1)[-1].strip()
                    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                        dns_servers.append(ip)

    except Exception as e:
        print(f"[DNS Detection Error] {e}")

    # اولین DNS معتبر
    return dns_servers[0] if dns_servers else "Unknown"

# --- دیتابیس ---
def init_db():
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                download REAL, upload REAL, jitter REAL, ping REAL,
                packet_loss REAL, country TEXT, isp TEXT, ip_address TEXT,
                dns REAL, dns_server TEXT
            )
        ''')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON tests(timestamp)")
        conn.commit()
        conn.close()
        print("Database created successfully.")
    else:
        print("Database already exists. Using existing database.")

# --- کارگر تست ---
class Worker(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)
    results_signal = pyqtSignal(dict)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            self.output_signal.emit("Network connection verified.\n")
        except:
            self.error_signal.emit("No internet connection.")
            return

        results = {k: 0 for k in ['download', 'upload', 'jitter', 'ping', 'packet_loss', 'dns']}
        results.update({'country': 'Unknown', 'isp': 'Unknown', 'ip_address': 'Unknown', 'dns_server': 'Unknown'})

        total_steps = sum([25 if self.settings.get(k, False) else 0 for k in ['download_enabled', 'upload_enabled', 'jitter_enabled']])
        total_steps += 15 if self.settings.get('ping_enabled', False) else 0
        total_steps += 5 if self.settings.get('dns_enabled', False) else 0
        total_steps += 5 if self.settings.get('location_enabled', False) else 0
        if total_steps == 0:
            self.error_signal.emit("No tests selected.")
            return

        progress_scale = 100 / total_steps
        current_progress = 0

        try:
            # --- دانلود ---
            if self.settings.get('download_enabled'):
                current_progress += 25 * progress_scale
                self.progress_signal.emit(int(current_progress), "Starting download...")
                self.output_signal.emit("Testing download...\n")
                try:
                    url = "http://ipv4.download.thinkbroadband.com/5MB.zip"
                    start = time.time()
                    r = requests.get(url, stream=True, timeout=120)
                    r.raise_for_status()
                    downloaded = sum(len(chunk) for chunk in r.iter_content(1024))
                    duration = time.time() - start
                    if duration > 0:
                        speed = (downloaded * 8) / (duration * 1_000_000)
                        size_mb = downloaded / (1024 * 1024)
                        self.output_signal.emit(f"Download speed: {speed:.2f} Mbps ({size_mb:.2f} MB)\n")
                        results['download'] = speed
                except Exception as e:
                    self.error_signal.emit(f"Download failed: {e}")
                self.progress_signal.emit(int(current_progress), "Download complete.")

            # --- آپلود ---
            if self.settings.get('upload_enabled'):
                current_progress += 25 * progress_scale
                self.progress_signal.emit(int(current_progress), "Starting upload...")
                self.output_signal.emit("Testing upload...\n")
                try:
                    # حجم کمتر: 1 مگابایت
                    volume_mb = 1
                    data = bytes(random.randbytes(volume_mb * 1024 * 1024))

                    # سرورهای پایدار
                    urls = [
                        "https://httpbin.org/anything",  # پایدار
                        "https://postman-echo.com/post",
                        "https://httpbin.org/post"
                    ]

                    speed = 0
                    for url in urls:
                        try:
                            start = time.time()
                            r = requests.post(url, data=data, timeout=60)
                            if r.status_code in (200, 201):
                                duration = time.time() - start
                                if duration > 0:
                                    speed = (len(data) * 8) / (duration * 1_000_000)
                                    self.output_signal.emit(f"Upload speed: {speed:.2f} Mbps ({volume_mb} MB)\n")
                                    results['upload'] = speed
                                    break
                        except:
                            continue

                    if speed == 0:
                        self.output_signal.emit("Upload test failed on all servers. Setting to 0.\n")
                        results['upload'] = 0

                except Exception as e:
                    self.error_signal.emit(f"Upload failed: {e}")
                    results['upload'] = 0
                self.progress_signal.emit(int(current_progress), "Upload complete.")

            # --- جتر ---
            if self.settings.get('jitter_enabled'):
                current_progress += 25 * progress_scale
                self.progress_signal.emit(int(current_progress), "Computing jitter...")
                self.output_signal.emit("Testing jitter...\n")
                latencies = []
                for _ in range(self.settings.get('jitter_samples', 10)):
                    try:
                        start = time.time()
                        requests.get("https://api.ipify.org", timeout=20).raise_for_status()
                        latencies.append((time.time() - start) * 1000)
                    except:
                        pass
                if len(latencies) >= 2:
                    jitter = statistics.stdev(latencies)
                    self.output_signal.emit(f"Jitter: {jitter:.2f} ms\n")
                    results['jitter'] = jitter
                self.progress_signal.emit(int(current_progress), "Jitter computed.")

            # --- پینگ ---
            if self.settings.get('ping_enabled'):
                current_progress += 15 * progress_scale
                self.progress_signal.emit(int(current_progress), "Pinging...")
                self.output_signal.emit("Testing ping...\n")
                cmd = ["ping", "-n" if platform.system().lower() == "windows" else "-c", "4", "1.1.1.1"]
                try:
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=30, text=True, encoding='utf-8', errors='ignore')
        
                    # استخراج تعداد پکت‌ها با چک کردن None
                    sent_match = re.search(r'(\d+) packets? transmitted', output, re.I)
                    recv_match = re.search(r'(\d+) packets? received', output, re.I)
                    time_matches = re.findall(r'time[=<](\d+\.?\d*) ?ms', output, re.I)

                    sent = int(sent_match.group(1)) if sent_match else 4
                    recv = int(recv_match.group(1)) if recv_match else 0

                    if time_matches:
                        ping_times = [float(t) for t in time_matches]
                        results['ping'] = sum(ping_times) / len(ping_times)
                        self.output_signal.emit(f"Average ping: {results['ping']:.2f} ms\n")
                    else:
                        results['ping'] = 0
                        self.output_signal.emit("Ping: No response times found.\n")

                    results['packet_loss'] = ((sent - recv) / sent) * 100 if sent > 0 else 100
                    self.output_signal.emit(f"Packet Loss: {results['packet_loss']:.2f}%\n")

                except subprocess.TimeoutExpired:
                    self.error_signal.emit("Ping timeout: No response from 1.1.1.1")
                    results['ping'] = results['packet_loss'] = 0
                except Exception as e:
                    self.error_signal.emit(f"Ping failed: {e}")
                    results['ping'] = results['packet_loss'] = 0
                self.progress_signal.emit(int(current_progress), "Ping complete.")

            # --- DNS ---
            if self.settings.get('dns_enabled'):
                current_progress += 5 * progress_scale
                self.progress_signal.emit(int(current_progress), "Detecting DNS server...")
                self.output_signal.emit("Detecting your DNS server...\n")
                try:
                    dns_server_ip = get_system_dns()
                    results['dns_server'] = dns_server_ip

                    start = time.time()
                    res = resolver.Resolver()
                    res.nameservers = [dns_server_ip] if dns_server_ip != "Unknown" else ['1.1.1.1']
                    res.timeout = res.lifetime = 10
                    ip = res.resolve('google.com', 'A')[0].to_text()
                    dns_time = (time.time() - start) * 1000
                    results['dns'] = dns_time

                    self.output_signal.emit(f"DNS Server: {dns_server_ip}\n")
                    self.output_signal.emit(f"DNS Response Time: {dns_time:.2f} ms\n")
                except Exception as e:
                    self.error_signal.emit(f"DNS detection failed: {e}")
                    results['dns_server'] = "Unknown"
                    results['dns'] = 0
                self.progress_signal.emit(int(current_progress), "DNS detected.")

            # --- لوکیشن ---
            if self.settings.get('location_enabled'):
                current_progress += 5 * progress_scale
                self.progress_signal.emit(int(current_progress), "Detecting location...")
                self.output_signal.emit("Detecting location & ISP...\n")
                try:
                    data = requests.get("http://ip-api.com/json", timeout=15).json()
                    results.update({
                        'country': data.get('country', 'Unknown'),
                        'isp': data.get('isp', 'Unknown'),
                        'ip_address': data.get('query', 'Unknown')
                    })
                    flag = FLAG_EMOJIS.get(results['country'], 'Unknown')
                    self.output_signal.emit(f"Country: {results['country']} {flag}\n")
                    self.output_signal.emit(f"ISP: {results['isp']}\n")
                    self.output_signal.emit(f"IP Address: {results['ip_address']}\n")
                except Exception as e:
                    self.error_signal.emit(f"Location failed: {e}")
                self.progress_signal.emit(100, "All tests complete!")

            # --- ذخیره ---
            print(f"[DB] Saving: {results}")
            self.save_to_db(results)
            print("[DB] Saved!")

            self.results_signal.emit(results)
            self.output_signal.emit(f"Test completed at: {datetime.now().strftime('%H:%M:%S')}\n")

        except Exception as e:
            self.error_signal.emit(f"Unexpected error: {e}")

    def save_to_db(self, results):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    INSERT INTO tests (
                        timestamp, download, upload, jitter, ping,
                        packet_loss, country, isp, ip_address, dns, dns_server
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    round(results['download'], 3),
                    round(results['upload'], 3),
                    round(results['jitter'], 3),
                    round(results['ping'], 3),
                    round(results['packet_loss'], 3),
                    results['country'],
                    results['isp'],
                    results['ip_address'],
                    round(results['dns'], 3) if results['dns'] else None,
                    results.get('dns_server', 'Unknown')
                ))
        except Exception as e:
            print(f"[DB SAVE ERROR] {e}")

# --- پنجره اصلی ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FluxFlow - Network Speed Tester")
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet(self.get_charcoal_styles())

        self.settings = {
            'download_enabled': True, 'upload_enabled': True, 'jitter_enabled': True,
            'jitter_samples': 10, 'ping_enabled': True, 'dns_enabled': True,
            'location_enabled': True
        }
        self.PAGE_SIZE = 100
        self.current_page = 0

        self.setup_ui()
        self.apply_shadow_effects()

        self.start_btn.clicked.connect(self.start_test)

        self.worker = Worker(self.settings)
        self.worker.output_signal.connect(self.update_output)
        self.worker.error_signal.connect(self.update_error)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.results_signal.connect(self.on_results_ready)

        self.load_settings()
        self.load_summary_page()

    def get_charcoal_styles(self):
        return """
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1e1e, stop:1 #2d2d2d); color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #d0d0d0; font-size: 14px; font-weight: 500; }
            QLabel[accessibleName="title"] { font-size: 28px; font-weight: bold; color: #4fc3f7; margin: 20px; text-shadow: 0 2px 4px rgba(0,0,0,0.4); }
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1976d2); color: white; border: none; border-radius: 20px; padding: 14px 28px; font-size: 16px; font-weight: bold; min-width: 180px; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #64b5f6, stop:1 #42a5f5); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976d2, stop:1 #1565c0); }
            QTextEdit { background-color: rgba(30, 30, 30, 0.85); color: #81c784; border: 2px solid #42a5f5; border-radius: 18px; padding: 16px; font-family: 'Consolas', monospace; font-size: 13px; }
            QProgressBar { border: 2px solid #42a5f5; border-radius: 18px; text-align: center; background-color: #2d2d2d; color: white; font-weight: bold; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #42a5f5, stop:1 #81c784); border-radius: 15px; }
            QTableWidget { background-color: rgba(40, 40, 40, 0.9); color: #e0e0e0; gridline-color: #444; border: 1px solid #42a5f5; border-radius: 15px; }
            QHeaderView::section { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1976d2); color: white; padding: 12px; border: none; font-weight: bold; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #42a5f5; background-color: transparent; border-radius: 15px; }
            QTabBar::tab { background: rgba(66, 165, 245, 0.2); color: #e0e0e0; padding: 12px 24px; margin: 2px; border-top-left-radius: 12px; border-top-right-radius: 12px; min-width: 120px; }
            QTabBar::tab:selected { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1976d2); color: white; font-weight: bold; }
            QLineEdit, QDateEdit, QTimeEdit, QSpinBox { background-color: rgba(40, 40, 40, 0.8); color: #e0e0e0; border: 2px solid #42a5f5; border-radius: 10px; padding: 8px; font-size: 13px; }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus { border: 2px solid #64b5f6; }
            QCheckBox { color: #e0e0e0; font-size: 14px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 6px; border: 2px solid #42a5f5; }
            QCheckBox::indicator:checked { background-color: #42a5f5; }
        """

    def apply_shadow_effects(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.start_btn.setGraphicsEffect(shadow)

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- تب Test ---
        self.test_tab = QWidget()
        self.tabs.addTab(self.test_tab, "Test")
        layout = QVBoxLayout(self.test_tab)
        layout.setSpacing(20); layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("FluxFlow Network Speed Tester")
        title.setAccessibleName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Test")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100); self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        frame = QFrame()
        frame.setStyleSheet("background: rgba(30, 30, 30, 0.7); border-radius: 20px; border: 1px solid #42a5f5;")
        layout.addWidget(frame)
        text_layout = QVBoxLayout(frame)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        text_layout.addWidget(self.text_area)

        # --- تب Summary ---
        self.summary_tab = QWidget()
        self.tabs.addTab(self.summary_tab, "Summary")
        s_layout = QVBoxLayout(self.summary_tab)
        s_layout.setContentsMargins(25, 25, 25, 25)

        filter_layout = QHBoxLayout()
        self.date_from = QDateEdit(); self.date_from.setDate(QDate(2000, 1, 1)); self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(); self.date_to.setDate(QDate.currentDate()); self.date_to.setCalendarPopup(True)
        self.time_from = QTimeEdit(); self.time_from.setTime(QTime(0, 0))
        self.time_to = QTimeEdit(); self.time_to.setTime(QTime(23, 59))
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText("Search ISP/Country...")

        for w, label in [(self.date_from, "From:"), (self.date_to, "To:"),
                         (self.time_from, ""), (self.time_to, ""), (self.search_edit, "Search:")]:
            if label:
                filter_layout.addWidget(QLabel(label))
            filter_layout.addWidget(w)

        self.filter_btn = QPushButton("Filter"); self.filter_btn.clicked.connect(self.filter_summary)
        self.clear_filter_btn = QPushButton("Clear"); self.clear_filter_btn.clicked.connect(self.clear_filter)
        filter_layout.addWidget(self.filter_btn); filter_layout.addWidget(self.clear_filter_btn)
        s_layout.addLayout(filter_layout)

        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(12)
        self.summary_table.setHorizontalHeaderLabels([
            'ID', 'Time', 'Down', 'Up', 'Jitter', 'Ping',
            'Loss', 'ISP/Country', 'IP', 'DNS Server', 'Response Time', 'Actions'
        ])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        s_layout.addWidget(self.summary_table)

        pag_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton("Previous"); self.prev_page_btn.clicked.connect(self.prev_page); self.prev_page_btn.setEnabled(False)
        self.page_label = QLabel("Page 1")
        self.next_page_btn = QPushButton("Next"); self.next_page_btn.clicked.connect(self.next_page)
        pag_layout.addWidget(self.prev_page_btn); pag_layout.addWidget(self.page_label); pag_layout.addWidget(self.next_page_btn)
        s_layout.addLayout(pag_layout)

        # --- دکمه‌های اکسپورت و ایمپورت ---
        export_import_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_to_excel)

        self.import_btn = QPushButton("Import from Excel")
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.clicked.connect(self.import_from_excel)

        export_import_layout.addWidget(self.export_btn)
        export_import_layout.addWidget(self.import_btn)
        export_import_layout.addStretch()

        s_layout.insertLayout(1, export_import_layout)  # بعد از فیلترها

        # --- تب Settings ---
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Settings")
        set_layout = QVBoxLayout(self.settings_tab); set_layout.setContentsMargins(30, 30, 30, 30)

        self.download_cb = QCheckBox("Enable Download Test"); self.download_cb.setChecked(True)
        self.upload_cb = QCheckBox("Enable Upload Test"); self.upload_cb.setChecked(True)
        self.jitter_cb = QCheckBox("Enable Jitter Test"); self.jitter_cb.setChecked(True)
        jitter_layout = QHBoxLayout()
        self.jitter_samples_spin = QSpinBox(); self.jitter_samples_spin.setRange(3, 20); self.jitter_samples_spin.setValue(10)
        jitter_layout.addWidget(QLabel("Jitter Samples:")); jitter_layout.addWidget(self.jitter_samples_spin)
        self.ping_cb = QCheckBox("Enable Ping & Packet Loss"); self.ping_cb.setChecked(True)
        self.dns_cb = QCheckBox("Enable DNS Test"); self.dns_cb.setChecked(True)
        self.location_cb = QCheckBox("Enable Location/ISP"); self.location_cb.setChecked(True)

        for w in [self.download_cb, self.upload_cb, self.jitter_cb, jitter_layout,
                  self.ping_cb, self.dns_cb, self.location_cb]:
            set_layout.addWidget(w) if isinstance(w, QWidget) else set_layout.addLayout(w)

        apply_btn = QPushButton("Apply & Save Settings"); apply_btn.clicked.connect(self.apply_settings)
        set_layout.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- تب Graph ---
        self.graph_tab = QWidget()
        self.tabs.addTab(self.graph_tab, "Graph")
        g_layout = QVBoxLayout(self.graph_tab)
        g_layout.setContentsMargins(25, 25, 25, 25)
        self.graph_btn = QPushButton("Generate Speed & Performance Graph")
        self.graph_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.graph_btn.clicked.connect(self.generate_graph)
        self.graph_label = QLabel("Click 'Generate' to view the performance graph.")
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setStyleSheet("color: #b0b0b0; font-size: 14px;")
        g_layout.addWidget(self.graph_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        g_layout.addWidget(self.graph_label)

    def start_test(self):
        self.text_area.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.worker = Worker(self.settings)
        self.worker.output_signal.connect(self.update_output)
        self.worker.error_signal.connect(self.update_error)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.results_signal.connect(self.on_results_ready)
        self.worker.start()

    def update_output(self, text): self.text_area.append(text)
    def update_progress(self, value, msg): self.progress_bar.setValue(value); self.text_area.append(msg + "\n")
    def update_error(self, error): self.text_area.append(f"Error: {error}\n"); QMessageBox.critical(self, "Error", error)

    def on_results_ready(self, results):
        self.update_summary_page()
        flag = FLAG_EMOJIS.get(results['country'], 'Unknown')
        self.text_area.append(f"Country: {results['country']} {flag}\n")

    def load_summary_page(self):
        self.summary_table.setRowCount(0)
        offset = self.current_page * self.PAGE_SIZE
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT id, timestamp, download, upload, jitter, ping,
                           packet_loss, country, isp, ip_address, dns, dns_server
                    FROM tests ORDER BY timestamp DESC LIMIT ? OFFSET ?
                ''', (self.PAGE_SIZE + 1, offset))
                rows = cur.fetchall()

            for row in rows[:self.PAGE_SIZE]:
                r = self.summary_table.rowCount()
                self.summary_table.insertRow(r)

                # --- کشور + پرچم مستقیم ---
                country = row[7] or "Unknown"
                flag = FLAG_EMOJIS.get(country, "Unknown")
                country_with_flag = f"{country} {flag}"

                # --- ISP / Country ---
                isp = row[8] or ""
                isp_country = f"{isp} / {country_with_flag}".strip()
                if not isp_country.replace('/', '').strip():
                    isp_country = "Unknown"

                # --- زمان پاسخ DNS ---
                dns_time = f"{row[10]:.1f} ms" if row[10] else "—"

                # --- لیست آیتم‌ها ---
                items = [
                    str(row[0]),                          # ID
                    row[1][:19].replace('T', ' '),        # Time
                    f"{row[2]:.3f}",                      # Down
                    f"{row[3]:.3f}",                      # Up
                    f"{row[4]:.3f}",                      # Jitter
                    f"{row[5]:.1f}",                      # Ping
                    f"{row[6]:.1f}",                      # Loss
                    isp_country,                          # ISP / Country + Flag
                    row[9],                               # IP
                    row[11] or "—",                       # DNS Server
                    dns_time,                             # Response Time
                    ""                                    # Actions
                ]

                # --- اضافه کردن به جدول ---
                for i, txt in enumerate(items):
                    item = QTableWidgetItem(txt)
                    # اعداد وسط‌چین
                    if i in (2, 3, 4, 5, 6, 10):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.summary_table.setItem(r, i, item)

            # --- صفحه‌بندی ---
            has_next = len(rows) > self.PAGE_SIZE
            self.next_page_btn.setEnabled(has_next)
            self.prev_page_btn.setEnabled(self.current_page > 0)
            self.page_label.setText(f"Page {self.current_page + 1}")

        except Exception as e:
            self.update_error(f"DB Error: {e}")

    def next_page(self):
        self.current_page += 1
        self.load_summary_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_summary_page()
    
    def update_summary_page(self): self.load_summary_page()

    def filter_summary(self):
        self.current_page = 0
        from_dt = datetime.combine(self.date_from.date().toPyDate(), self.time_from.time().toPyTime()).isoformat()
        to_dt = datetime.combine(self.date_to.date().toPyDate(), self.time_to.time().toPyTime()).isoformat()
    
        # محدود کردن طول جستجو
        raw_search = self.search_edit.text().strip()
        search = raw_search[:50]
        if len(raw_search) > 50:
            self.update_error("Search term too long. Limited to 50 characters.")

        query = '''
            SELECT id, timestamp, download, upload, jitter, ping,
                   packet_loss, country, isp, ip_address, dns, dns_server
            FROM tests WHERE timestamp BETWEEN ? AND ?
        '''
        params = [from_dt, to_dt]
    
        if search:
            query += " AND (country LIKE ? OR isp LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
    
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([self.PAGE_SIZE + 1, 0])

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(query, params)
                rows = cur.fetchall()

            self.summary_table.setRowCount(0)
            for row in rows[:self.PAGE_SIZE]:
                r = self.summary_table.rowCount()
                self.summary_table.insertRow(r)

                country = row[7] or "Unknown"
                flag = FLAG_EMOJIS.get(country, "Unknown")
                country_with_flag = f"{country} {flag}"
                isp = row[8] or ""
                isp_country = f"{isp} / {country_with_flag}".strip() or "Unknown"
                dns_time = f"{row[10]:.1f} ms" if row[10] else "—"

                items = [
                    str(row[0]), row[1][:19].replace('T',' '),
                    f"{row[2]:.3f}", f"{row[3]:.3f}", f"{row[4]:.3f}",
                    f"{row[5]:.1f}", f"{row[6]:.1f}",
                    isp_country, row[9], row[11] or "—", dns_time, ""
                ]

                for i, txt in enumerate(items):
                    item = QTableWidgetItem(txt)
                    if i in (2,3,4,5,6,10):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.summary_table.setItem(r, i, item)

            self.next_page_btn.setEnabled(len(rows) > self.PAGE_SIZE)
            self.prev_page_btn.setEnabled(False)
            self.page_label.setText("Page 1")
        
        except Exception as e:
            self.update_error(f"Filter Error: {e}")

    def clear_filter(self):
        self.date_from.setDate(QDate(2000, 1, 1)); self.date_to.setDate(QDate.currentDate())
        self.time_from.setTime(QTime(0, 0)); self.time_to.setTime(QTime(23, 59))
        self.search_edit.clear(); self.current_page = 0; self.load_summary_page()

    def apply_settings(self):
        self.settings.update({
            'download_enabled': self.download_cb.isChecked(),
            'upload_enabled': self.upload_cb.isChecked(),
            'jitter_enabled': self.jitter_cb.isChecked(),
            'jitter_samples': self.jitter_samples_spin.value(),
            'ping_enabled': self.ping_cb.isChecked(),
            'dns_enabled': self.dns_cb.isChecked(),
            'location_enabled': self.location_cb.isChecked()
        })
        self.save_settings()
        QMessageBox.information(self, "Success", "Settings applied and saved!")

    def save_settings(self):
        try:
            SETTINGS_PATH.write_text(
                json.dumps(self.settings, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Save failed: {e}")

    def load_settings(self):
        if not SETTINGS_PATH.exists():
            return
        try:
            loaded = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
            for k, v in loaded.items():
                if k in self.settings:
                    self.settings[k] = v
            # اعمال به UI
            self.download_cb.setChecked(self.settings['download_enabled'])
            # ...
        except Exception as e:
            print(f"Load failed: {e}")

    def generate_graph(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT timestamp, download, upload, ping, jitter, packet_loss, dns, country, isp
                    FROM tests ORDER BY timestamp ASC
                ''')
                rows = cur.fetchall()

            if not rows:
                self.graph_label.setText("No data available for graph.")
                return

            # --- آماده‌سازی داده‌ها ---
            timestamps = [datetime.fromisoformat(row[0]).strftime('%H:%M') for row in rows]
            downloads = [row[1] or 0 for row in rows]
            uploads = [row[2] or 0 for row in rows]
            pings = [row[3] or 0 for row in rows]
            jitters = [row[4] or 0 for row in rows]
            packet_losses = [row[5] or 0 for row in rows]
            dns_times = [row[6] or 0 for row in rows]
            countries = [row[7] or "Unknown" for row in rows]
            isps = [row[8] or "Unknown" for row in rows]

            # --- ایجاد فیگور ---
            fig, ax1 = plt.subplots(figsize=(14, 8))
            fig.patch.set_facecolor('#1e1e1e')
            ax1.set_facecolor('#2d2d2d')

            # محور اول: سرعت (Mbps)
            ax1.set_xlabel('Time', color='white', fontsize=12)
            ax1.set_ylabel('Speed (Mbps)', color='#4fc3f7', fontsize=12)
            ax1.plot(timestamps, downloads, 'o-', label='Download', color='#42a5f5', linewidth=2.5, markersize=6)
            ax1.plot(timestamps, uploads, 's-', label='Upload', color='#81c784', linewidth=2.5, markersize=6)
            ax1.tick_params(axis='y', labelcolor='#4fc3f7')
            ax1.grid(True, alpha=0.3, color='#444')

            # محور دوم: لتنسی و لاس
            ax2 = ax1.twinx()
            ax2.set_ylabel('Latency (ms) / Loss (%)', color='#ff7043', fontsize=12)
            ax2.plot(timestamps, pings, '^-', label='Ping', color='#ff7043', linewidth=2, markersize=6)
            ax2.plot(timestamps, jitters, 'd-', label='Jitter', color='#ffd54f', linewidth=2, markersize=6)
            ax2.plot(timestamps, dns_times, 'x-', label='DNS Time', color='#ba68c8', linewidth=2, markersize=6)
            ax2.plot(timestamps, packet_losses, 'v-', label='Packet Loss %', color='#ef5350', linewidth=2, markersize=6)
            ax2.tick_params(axis='y', labelcolor='#ff7043')

            # لجند
            lines = ax1.get_lines() + ax2.get_lines()
            ax1.legend(lines, [l.get_label() for l in lines], loc='upper left',
                       facecolor='#2d2d2d', edgecolor='#42a5f5', labelcolor='white')

            # استایل
            plt.title('FluxFlow - Network Performance Over Time', color='white', fontsize=16, pad=20)
            ax1.tick_params(colors='white')
            ax2.tick_params(colors='white')
            plt.xticks(rotation=45, color='white')
            plt.tight_layout()

            # --- اضافه کردن پرچم به نقاط دانلود ---
            for i, country in enumerate(countries):
                flag = FLAG_EMOJIS.get(country, "Unknown")
                ax1.annotate(flag, (timestamps[i], downloads[i]),
                            xytext=(0, 10), textcoords='offset points',
                            fontsize=10, ha='center', color='yellow')

            # --- ذخیره با pathlib ---
            # پاک کردن فایل قبلی (جلوگیری از تداخل)
            if GRAPH_TEMP_PATH.exists():
                try:
                    GRAPH_TEMP_PATH.unlink()
                except:
                    pass

            plt.savefig(
                GRAPH_TEMP_PATH,
                dpi=150,
                bbox_inches='tight',
                facecolor='#1e1e1e',
                format='png'
            )
            plt.close(fig)

            # --- نمایش در UI ---
            if GRAPH_TEMP_PATH.exists():
                pixmap = QPixmap(str(GRAPH_TEMP_PATH))
                if not pixmap.isNull():
                    self.graph_label.setPixmap(
                        pixmap.scaled(900, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    )
                    self.graph_label.setText("")
                else:
                    self.graph_label.setText("Failed to load graph image.")
            else:
                self.graph_label.setText("Graph file not created.")

        except Exception as e:
            self.graph_label.setText(f"Graph Error: {e}")
            print(f"[Graph Debug] {e}")

    def export_to_excel(self):
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            import pandas as pd

            # --- مسیر پیشنهادی با pathlib ---
            default_path = BASE_DIR / "fluxflow_tests.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                str(default_path),
                "Excel Files (*.xlsx)"
            )
            if not file_path:
                return

            file_path = Path(file_path)  # تبدیل به Path

            # --- چک کردن وجود فایل و تأیید بازنویسی ---
            if file_path.exists():
                reply = QMessageBox.question(
                    self,
                    "File Exists",
                    f"File already exists:\n{file_path.name}\n\nOverwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # --- خواندن داده‌ها از دیتابیس ---
            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query('''
                    SELECT id, timestamp, download, upload, jitter, ping,
                           packet_loss, country, isp, ip_address, dns, dns_server
                    FROM tests ORDER BY timestamp DESC
                ''', conn)

            if df.empty:
                QMessageBox.warning(self, "No Data", "No test results to export.")
                return

            # --- تبدیل timestamp ---
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

            # --- اضافه کردن پرچم ---
            df['country_with_flag'] = df['country'].apply(
                lambda x: f"{x} {FLAG_EMOJIS.get(x, 'Unknown')}" if pd.notna(x) else "Unknown"
            )

            # --- ISP / Country ---
            df['ISP/Country'] = df['isp'].fillna('') + " / " + df['country_with_flag']
            df['ISP/Country'] = df['ISP/Country'].str.replace(r' \/ $', '', regex=True)

            # --- زمان پاسخ DNS ---
            df['DNS Response'] = df['dns'].apply(
                lambda x: f"{x:.1f} ms" if pd.notna(x) and x > 0 else "—"
            )

            # --- انتخاب و مرتب‌سازی ستون‌ها ---
            export_df = df[[
                'id', 'timestamp', 'download', 'upload', 'jitter', 'ping',
                'packet_loss', 'ISP/Country', 'ip_address', 'dns_server', 'DNS Response'
            ]].copy()

            # --- تغییر نام ستون‌ها ---
            export_df.columns = [
                'ID', 'Time', 'Down (Mbps)', 'Up (Mbps)', 'Jitter (ms)', 'Ping (ms)',
                'Loss (%)', 'ISP / Country', 'IP Address', 'DNS Server', 'DNS Response'
            ]

            # --- ذخیره به اکسل با pathlib ---
            try:
                export_df.to_excel(
                    file_path,
                    index=False,
                    engine='openpyxl'
                )
                QMessageBox.information(
                    self,
                    "Success",
                    f"Data exported successfully!\n\nFile: {file_path}\nRecords: {len(export_df)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{e}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred:\n{e}")
            print(f"[Export Debug] {e}")

    def import_from_excel(self):
        try:
            from PyQt6.QtWidgets import QFileDialog
            import pandas as pd

            file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
            if not file_path: return

            df = pd.read_excel(file_path, engine='openpyxl')
            required = ['ID', 'Time', 'Down', 'Up', 'Jitter', 'Ping', 'Loss', 'ISP/Country', 'IP', 'DNS Server', 'Response Time']
            if not all(col in df.columns for col in required):
                QMessageBox.warning(self, "Error", "Invalid format.")
                return

            records = []
            for _, row in df.iterrows():
                try:
                    isp_country = str(row['ISP/Country']).strip()
                    isp = country = ""
                    if " / " in isp_country:
                        isp, country_part = isp_country.split(" / ", 1)
                        country = country_part.split(" ", 1)[0] if " " in country_part else country_part
                    else:
                        country = isp_country.split(" ", 1)[0] if " " in isp_country else isp_country

                    dns_str = str(row['Response Time'])
                    dns = float(dns_str.replace(" ms", "")) if "ms" in dns_str and dns_str != "—" else None

                    records.append((
                        row['Time'], float(row['Down']) if pd.notna(row['Down']) else 0,
                        float(row['Up']) if pd.notna(row['Up']) else 0,
                        float(row['Jitter']) if pd.notna(row['Jitter']) else 0,
                        float(row['Ping']) if pd.notna(row['Ping']) else 0,
                        float(row['Loss']) if pd.notna(row['Loss']) else 0,
                        country, isp, row['IP'],
                        dns, row['DNS Server'] if pd.notna(row['DNS Server']) else "Unknown"
                    ))
                except: continue

            if not records:
                QMessageBox.warning(self, "Error", "No valid data.")
                return

            with sqlite3.connect(DB_PATH) as conn:
                conn.executemany('''
                    INSERT INTO tests (timestamp, download, upload, jitter, ping,
                        packet_loss, country, isp, ip_address, dns, dns_server)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', records)

            self.load_summary_page()
            QMessageBox.information(self, "Success", f"Imported {len(records)} records.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed:\n{e}")
# --- اجرا ---
if __name__ == "__main__":
    import time
    import sqlite3
    app = QApplication(sys.argv)
    init_db()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())