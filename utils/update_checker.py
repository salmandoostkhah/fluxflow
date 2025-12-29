import requests
import webbrowser
from packaging import version
from PyQt6.QtWidgets import QMessageBox
from config import BASE_DIR

def check_for_updates(parent=None, silent=False):
    try:
        version_path = BASE_DIR / "version.txt"
        current_version = version_path.read_text(encoding='utf-8').strip() if version_path.exists() else "unknown"

        api_url = "https://api.github.com/repos/salmandostkhah/fluxflow/releases/latest"
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            if not silent:
                QMessageBox.information(parent, "آپدیت", "خطا در ارتباط با GitHub.")
            return

        data = response.json()
        latest_version = data['tag_name'].lstrip('v')

        if current_version != "unknown" and version.parse(latest_version) > version.parse(current_version):
            reply = QMessageBox.question(
                parent, "آپدیت موجود!",
                f"نسخه جدید {latest_version} موجود است!\n"
                f"نسخه فعلی: {current_version}\n\n"
                f"تغییرات:\n{data.get('body', 'بدون توضیح')[:400]}...\n\n"
                "باز کردن صفحه دانلود؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open(data['html_url'])
        elif not silent:
            QMessageBox.information(parent, "آپدیت", f"برنامه به‌روز است (نسخه {current_version}) 😊")
    except Exception as e:
        if not silent:
            QMessageBox.warning(parent, "خطا", f"خطا در چک آپدیت: {str(e)}")