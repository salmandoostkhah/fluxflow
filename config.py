from pathlib import Path
import tempfile

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "fluxflow_tests.db"
SETTINGS_PATH = BASE_DIR / "settings.json"
GRAPH_TEMP_PATH = Path(tempfile.gettempdir()) / "fluxflow_graph.png"

FLAG_EMOJIS = {
    'Iran': '🇮🇷', 'United States': '🇺🇸', 'Germany': '🇩🇪', 'United Kingdom': '🇬🇧',
    'France': '🇫🇷', 'India': '🇮🇳', 'China': '🇨🇳', 'Japan': '🇯🇵',
    'Brazil': '🇧🇷', 'Canada': '🇨🇦', 'Australia': '🇦🇺', 'Russia': '🇷🇺',
    'Italy': '🇮🇹', 'Spain': '🇪🇸', 'Unknown': '🌍'
}

PAGE_SIZE = 100

DEFAULT_SETTINGS = {
    'download_enabled': True,
    'upload_enabled': True,
    'jitter_enabled': True,
    'jitter_samples': 10,
    'ping_enabled': True,
    'dns_enabled': True,
    'location_enabled': True
}

# استایل کامل از کد اصلیت
CHARCOAL_STYLESHEET = """
QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1e1e, stop:1 #2d2d2d); color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
QLabel { color: #d0d0d0; font-size: 14px; font-weight: 500; }
QLabel[accessibleName="title"] { font-size: 28px; font-weight: bold; color: #4fc3f7; margin: 20px;}
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