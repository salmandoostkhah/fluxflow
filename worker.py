from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
import requests
from config import DEFAULT_SETTINGS
from database import save_test_result
from utils.network_tests import test_download, test_upload, test_jitter, test_ping, test_dns
from utils.geo_location import detect_location

class Worker(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)
    results_signal = pyqtSignal(dict)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings or DEFAULT_SETTINGS

    def run(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            self.output_signal.emit("Network connection verified.\n")
        except:
            self.error_signal.emit("No internet connection.")
            return

        results = {k: 0 for k in ['download', 'upload', 'jitter', 'ping', 'packet_loss', 'dns']}
        results.update({'country': 'Unknown', 'isp': 'Unknown', 'ip_address': 'Unknown', 'dns_server': 'Unknown'})
        results['timestamp'] = datetime.now().isoformat()

        total_steps = sum([25 if self.settings.get(k, False) else 0 for k in ['download_enabled', 'upload_enabled', 'jitter_enabled']])
        total_steps += 15 if self.settings.get('ping_enabled', False) else 0
        total_steps += 5 if self.settings.get('dns_enabled', False) else 0
        total_steps += 5 if self.settings.get('location_enabled', False) else 0
        if total_steps == 0:
            self.error_signal.emit("No tests selected.")
            return

        progress_scale = 100 / total_steps
        current_progress = 0

        if self.settings.get('download_enabled'):
            current_progress += 25
            self.progress_signal.emit(int(current_progress * progress_scale), "Testing download...")
            results['download'] = test_download(self.output_signal)

        if self.settings.get('upload_enabled'):
            current_progress += 25
            self.progress_signal.emit(int(current_progress * progress_scale), "Testing upload...")
            results['upload'] = test_upload(self.output_signal)

        if self.settings.get('jitter_enabled'):
            current_progress += 25
            self.progress_signal.emit(int(current_progress * progress_scale), "Computing jitter...")
            results['jitter'] = test_jitter(self.output_signal, self.settings.get('jitter_samples', 10))

        if self.settings.get('ping_enabled'):
            current_progress += 15
            self.progress_signal.emit(int(current_progress * progress_scale), "Pinging...")
            ping, loss = test_ping(self.output_signal)
            results['ping'] = ping
            results['packet_loss'] = loss

        if self.settings.get('dns_enabled'):
            current_progress += 5
            self.progress_signal.emit(int(current_progress * progress_scale), "Testing DNS...")
            dns_time, dns_server = test_dns(self.output_signal)
            results['dns'] = dns_time
            results['dns_server'] = dns_server

        if self.settings.get('location_enabled'):
            current_progress += 5
            self.progress_signal.emit(int(current_progress * progress_scale), "Detecting location...")
            location_data = detect_location(self.output_signal)
            results.update(location_data)

        save_test_result(results)
        self.results_signal.emit(results)
        self.output_signal.emit(f"Test completed at: {datetime.now().strftime('%H:%M:%S')}\n")