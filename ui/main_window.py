from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QVBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QLineEdit, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, QDate, QTime  # <--- Qt و QTimer اینجا
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import QTimer, QDate, QTime  # QTimer اینجا اضافه شد
from PyQt6.QtCore import QDate, QTime
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
import json
from datetime import datetime
import sqlite3
import pandas as pd
from PyQt6.QtWidgets import QFileDialog
from config import (
    CHARCOAL_STYLESHEET, SETTINGS_PATH, DEFAULT_SETTINGS,
    DB_PATH, PAGE_SIZE, FLAG_EMOJIS, BASE_DIR
)
from worker import Worker
from utils.update_checker import check_for_updates
from .test_tab import create_test_tab
from .summary_tab import create_summary_tab
from .settings_tab import create_settings_tab
from .graph_tab import create_graph_tab, generate_graph

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FluxFlow - Network Speed Tester")
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet(CHARCOAL_STYLESHEET)

        self.settings = DEFAULT_SETTINGS.copy()
        self.current_page = 0
        self.PAGE_SIZE = PAGE_SIZE

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setup_tabs()
        self.load_settings()
        QTimer.singleShot(5000, lambda: check_for_updates(self, silent=True))
        self.load_summary_page()

    def setup_tabs(self):
        self.tabs.addTab(create_test_tab(self), "Test")
        self.tabs.addTab(create_summary_tab(self), "Summary")
        self.tabs.addTab(create_settings_tab(self), "Settings")
        self.tabs.addTab(create_graph_tab(self), "Graph")

    def start_test(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            QMessageBox.warning(self, "در حال اجرا", "یک تست در حال اجراست. لطفاً صبر کنید.")
            return

        self.text_area.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.start_btn.setEnabled(False)
        self.start_btn.setText("در حال تست...")

        self.worker = Worker(self.settings)
        self.worker.output_signal.connect(self.text_area.append)
        self.worker.error_signal.connect(self.on_test_error)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.results_signal.connect(self.on_test_finished)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.text_area.append(message)

    def on_test_error(self, error):
        self.text_area.append(f"<span style='color:red'>خطا: {error}</span>")
        QMessageBox.critical(self, "خطا", error)

    def on_test_finished(self, results):
        self.text_area.append("\n<span style='color:#81c784; font-weight:bold'>تست با موفقیت به پایان رسید!</span>\n")
        flag = FLAG_EMOJIS.get(results.get('country', 'Unknown'), '🌍')
        self.text_area.append(f"کشور: {results.get('country', 'Unknown')} {flag} | ISP: {results.get('isp', 'Unknown')}\n")
        self.load_summary_page()  # بروزرسانی جدول

    def on_worker_finished(self):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Start Test")
        self.progress_bar.setVisible(False)

    def update_output(self, text):
        self.text_area.append(text)

    def update_progress(self, value, msg):
        self.progress_bar.setValue(value)
        self.text_area.append(msg + "\n")

    def update_error(self, error):
        self.text_area.append(f"Error: {error}\n")
        QMessageBox.critical(self, "Error", error)

    def on_results_ready(self, results):
        self.update_summary_page()
        flag = FLAG_EMOJIS.get(results.get('country', 'Unknown'), '🌍')
        self.text_area.append(f"Country: {results.get('country', 'Unknown')} {flag}\n")

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

                country = row[7] or "Unknown"
                flag = FLAG_EMOJIS.get(country, '🌍')
                isp_country = f"{row[8] or ''} / {country} {flag}".strip(" /")

                dns_time = f"{row[10]:.1f} ms" if row[10] and row[10] > 0 else "—"

                items = [
                    str(row[0]),
                    row[1][:19].replace('T', ' '),
                    f"{row[2]:.3f}" if row[2] else "0.000",
                    f"{row[3]:.3f}" if row[3] else "0.000",
                    f"{row[4]:.3f}" if row[4] else "0.000",
                    f"{row[5]:.1f}" if row[5] is not None else "0.0",
                    f"{row[6]:.1f}",
                    isp_country or "Unknown",
                    row[9] or "",
                    row[11] or "—",
                    dns_time,
                    ""
                ]

                for i, txt in enumerate(items):
                    item = QTableWidgetItem(txt)
                    if i in (2, 3, 4, 5, 6, 10):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.summary_table.setItem(r, i, item)

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

    def update_summary_page(self):
        self.load_summary_page()

    def clear_filter(self):
        self.date_from.setDate(QDate(2000, 1, 1))
        self.date_to.setDate(QDate.currentDate())
        self.time_from.setTime(QTime(0, 0))
        self.time_to.setTime(QTime(23, 59))
        self.search_edit.clear()
        self.current_page = 0
        self.load_summary_page()

    def filter_summary(self):
        self.current_page = 0
        from_dt = datetime.combine(self.date_from.date().toPyDate(), self.time_from.time().toPyTime()).isoformat()
        to_dt = datetime.combine(self.date_to.date().toPyDate(), self.time_to.time().toPyTime()).isoformat()

        raw_search = self.search_edit.text().strip()
        search = raw_search[:50]
        if len(raw_search) > 50:
            self.update_error("Search term too long. Limited to 50 characters.")
            return

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

            # پاک کردن جدول
            self.summary_table.setRowCount(0)

            # پر کردن جدول — دقیقاً مثل load_summary_page
            for row in rows[:self.PAGE_SIZE]:
                r = self.summary_table.rowCount()
                self.summary_table.insertRow(r)

                country = row[7] or "Unknown"
                flag = FLAG_EMOJIS.get(country, '🌍')
                country_with_flag = f"{country} {flag}"

                isp = row[8] or ""
                isp_country = f"{isp} / {country_with_flag}".strip()
                if not isp_country.replace('/', '').strip():
                    isp_country = "Unknown"

                dns_time = f"{row[10]:.1f} ms" if row[10] and row[10] > 0 else "—"

                items = [
                    str(row[0]),                                    # ID
                    row[1][:19].replace('T', ' '),                  # Time
                    f"{row[2]:.3f}" if row[2] is not None else "0.000",  # Down
                    f"{row[3]:.3f}" if row[3] is not None else "0.000",  # Up
                    f"{row[4]:.3f}" if row[4] is not None else "0.000",  # Jitter
                    f"{row[5]:.1f}" if row[5] is not None else "0.0",    # Ping
                    f"{row[6]:.1f}",                                    # Loss
                    isp_country,                                    # ISP / Country + Flag
                    row[9] or "",                                   # IP
                    row[11] or "—",                                 # DNS Server
                    dns_time,                                       # DNS Response
                    ""                                              # Actions
                ]

                for i, txt in enumerate(items):
                    item = QTableWidgetItem(txt)
                    if i in (2, 3, 4, 5, 6, 10):  # ستون‌های عددی: وسط‌چین
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.summary_table.setItem(r, i, item)

                # راست‌چین کردن IP و DNS Server
                for col in [8, 9]:
                    item = self.summary_table.item(r, col)
                    if item:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # صفحه‌بندی
            has_next = len(rows) > self.PAGE_SIZE
            self.next_page_btn.setEnabled(has_next)
            self.prev_page_btn.setEnabled(False)  # چون صفحه اول هستیم
            self.page_label.setText("Page 1")

        except Exception as e:
            self.update_error(f"Filter Error: {e}")
            print(f"[Filter Debug] {e}")

    def apply_settings(self):
        self.settings.update({
            'download_enabled': self.download_cb.isChecked(),
            'upload_enabled': self.upload_cb.isChecked(),
            'jitter_enabled': self.jitter_cb.isChecked(),
            'jitter_samples': self.jitter_samples_slider.value(),
            'ping_enabled': self.ping_cb.isChecked(),
            'dns_enabled': self.dns_cb.isChecked(),
            'location_enabled': self.location_cb.isChecked()
        })
        self.save_settings()
        QMessageBox.information(self, "Success", "Settings applied and saved!")

    def save_settings(self):
        try:
            SETTINGS_PATH.write_text(json.dumps(self.settings, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception as e:
            print(f"Save failed: {e}")

    def load_settings(self):
        if SETTINGS_PATH.exists():
            try:
                loaded = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
                self.settings.update(loaded)

                self.download_cb.setChecked(self.settings.get('download_enabled', True))
                self.upload_cb.setChecked(self.settings.get('upload_enabled', True))
                self.jitter_cb.setChecked(self.settings.get('jitter_enabled', True))
                self.ping_cb.setChecked(self.settings.get('ping_enabled', True))
                self.dns_cb.setChecked(self.settings.get('dns_enabled', True))
                self.location_cb.setChecked(self.settings.get('location_enabled', True))
                self.jitter_samples_slider.setValue(self.settings.get('jitter_samples', 10))
                self.jitter_value_label.setText(str(self.settings.get('jitter_samples', 10)))
            except Exception as e:
                QMessageBox.warning(self, "خطا", f"بارگذاری تنظیمات失敗: {e}")

    def generate_graph(self):
        generate_graph(self)

    def export_to_excel(self):
        try:
            default_path = BASE_DIR / "fluxflow_tests.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                str(default_path),
                "Excel Files (*.xlsx)"
            )
            if not file_path:
                return

            file_path = Path(file_path)

            if file_path.exists():
                reply = QMessageBox.question(
                    self,
                    "File Exists",
                    f"File already exists:\n{file_path.name}\n\nOverwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query('''
                    SELECT id, timestamp, download, upload, jitter, ping,
                           packet_loss, country, isp, ip_address, dns, dns_server
                    FROM tests ORDER BY timestamp DESC
                ''', conn)

            if df.empty:
                QMessageBox.warning(self, "No Data", "No test results to export.")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

            df['country_with_flag'] = df['country'].apply(
                lambda x: f"{x} {FLAG_EMOJIS.get(x, '🌍')}" if pd.notna(x) else "Unknown"
            )

            df['ISP/Country'] = df['isp'].fillna('') + " / " + df['country_with_flag']
            df['ISP/Country'] = df['ISP/Country'].str.replace(r' \/ $', '', regex=True)

            df['DNS Response'] = df['dns'].apply(
                lambda x: f"{x:.1f} ms" if pd.notna(x) and x > 0 else "—"
            )

            export_df = df[[
                'id', 'timestamp', 'download', 'upload', 'jitter', 'ping',
                'packet_loss', 'ISP/Country', 'ip_address', 'dns_server', 'DNS Response'
            ]].copy()

            export_df.columns = [
                'ID', 'Time', 'Down (Mbps)', 'Up (Mbps)', 'Jitter (ms)', 'Ping (ms)',
                'Loss (%)', 'ISP / Country', 'IP Address', 'DNS Server', 'DNS Response'
            ]

            export_df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(
                self,
                "Success",
                f"Data exported successfully!\n\nFile: {file_path}\nRecords: {len(export_df)}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred:\n{e}")
            print(f"[Export Debug] {e}")

    def import_from_excel(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
            if not file_path:
                return

            df = pd.read_excel(file_path, engine='openpyxl')

            required = ['ID', 'Time', 'Down (Mbps)', 'Up (Mbps)', 'Jitter (ms)', 'Ping (ms)', 'Loss (%)', 'ISP / Country', 'IP Address', 'DNS Server', 'DNS Response']
            if not all(col in df.columns for col in required):
                QMessageBox.warning(self, "Error", "Invalid Excel format. Missing required columns.")
                return

            records = []
            for _, row in df.iterrows():
                try:
                    isp_country = str(row['ISP / Country']).strip()
                    isp = country = ""
                    if " / " in isp_country:
                        parts = isp_country.split(" / ", 1)
                        isp = parts[0].strip()
                        country_part = parts[1].strip()
                        country = country_part.split(" ", 1)[0] if " " in country_part else country_part
                    else:
                        country = isp_country.split(" ", 1)[0] if " " in isp_country else isp_country

                    dns_str = str(row['DNS Response'])
                    dns = float(dns_str.replace(" ms", "").strip()) if "ms" in dns_str and dns_str.strip() != "—" else None

                    records.append((
                        row['Time'],
                        float(row['Down (Mbps)']) if pd.notna(row['Down (Mbps)']) else 0,
                        float(row['Up (Mbps)']) if pd.notna(row['Up (Mbps)']) else 0,
                        float(row['Jitter (ms)']) if pd.notna(row['Jitter (ms)']) else 0,
                        float(row['Ping (ms)']) if pd.notna(row['Ping (ms)']) else 0,
                        float(row['Loss (%)']) if pd.notna(row['Loss (%)']) else 0,
                        country,
                        isp,
                        str(row['IP Address']) if pd.notna(row['IP Address']) else "Unknown",
                        dns,
                        str(row['DNS Server']) if pd.notna(row['DNS Server']) else "Unknown"
                    ))
                except Exception as row_error:
                    print(f"Skipped invalid row: {row_error}")
                    continue

            if not records:
                QMessageBox.warning(self, "Error", "No valid data found in the Excel file.")
                return

            with sqlite3.connect(DB_PATH) as conn:
                conn.executemany('''
                    INSERT INTO tests (timestamp, download, upload, jitter, ping,
                        packet_loss, country, isp, ip_address, dns, dns_server)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', records)

            self.load_summary_page()
            self.update_summary_page()
            QMessageBox.information(self, "Success", f"Successfully imported {len(records)} records.")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Import failed:\n{e}")
            print(f"[Import Debug] {e}")

    def check_for_updates(self, silent=False):
        check_for_updates(self, silent)