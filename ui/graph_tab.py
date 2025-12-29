from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
from PyQt6.QtGui import QPixmap
from config import DB_PATH, GRAPH_TEMP_PATH, FLAG_EMOJIS

def create_graph_tab(parent):
    graph_tab = QWidget()
    g_layout = QVBoxLayout(graph_tab)
    g_layout.setContentsMargins(25, 25, 25, 25)

    parent.graph_btn = QPushButton("Generate Speed & Performance Graph")
    parent.graph_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    parent.graph_btn.clicked.connect(parent.generate_graph)
    g_layout.addWidget(parent.graph_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    parent.graph_label = QLabel("Click 'Generate' to view the performance graph.")
    parent.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    parent.graph_label.setStyleSheet("color: #b0b0b0; font-size: 14px;")
    g_layout.addWidget(parent.graph_label)

    return graph_tab

def generate_graph(parent):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT timestamp, download, upload, ping, jitter, packet_loss, dns, country, isp
                FROM tests ORDER BY timestamp ASC
            ''')
            rows = cur.fetchall()

        if not rows:
            parent.graph_label.setText("No data available for graph.")
            return

        timestamps = [datetime.fromisoformat(row[0]).strftime('%H:%M') for row in rows]
        downloads = [row[1] or 0 for row in rows]
        uploads = [row[2] or 0 for row in rows]
        pings = [row[3] or 0 for row in rows]
        jitters = [row[4] or 0 for row in rows]
        packet_losses = [row[5] or 0 for row in rows]
        dns_times = [row[6] or 0 for row in rows]
        countries = [row[7] or "Unknown" for row in rows]

        fig, ax1 = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor('#1e1e1e')
        ax1.set_facecolor('#2d2d2d')

        ax1.set_xlabel('Time', color='white', fontsize=12)
        ax1.set_ylabel('Speed (Mbps)', color='#4fc3f7', fontsize=12)
        ax1.plot(timestamps, downloads, 'o-', label='Download', color='#42a5f5', linewidth=2.5, markersize=6)
        ax1.plot(timestamps, uploads, 's-', label='Upload', color='#81c784', linewidth=2.5, markersize=6)
        ax1.tick_params(axis='y', labelcolor='#4fc3f7')
        ax1.grid(True, alpha=0.3, color='#444')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Latency (ms) / Loss (%)', color='#ff7043', fontsize=12)
        ax2.plot(timestamps, pings, '^-', label='Ping', color='#ff7043', linewidth=2, markersize=6)
        ax2.plot(timestamps, jitters, 'd-', label='Jitter', color='#ffd54f', linewidth=2, markersize=6)
        ax2.plot(timestamps, dns_times, 'x-', label='DNS Time', color='#ba68c8', linewidth=2, markersize=6)
        ax2.plot(timestamps, packet_losses, 'v-', label='Packet Loss %', color='#ef5350', linewidth=2, markersize=6)
        ax2.tick_params(axis='y', labelcolor='#ff7043')

        lines = ax1.get_lines() + ax2.get_lines()
        ax1.legend(lines, [l.get_label() for l in lines], loc='upper left',
                   facecolor='#2d2d2d', edgecolor='#42a5f5', labelcolor='white')

        plt.title('FluxFlow - Network Performance Over Time', color='white', fontsize=16, pad=20)
        ax1.tick_params(colors='white')
        ax2.tick_params(colors='white')
        plt.xticks(rotation=45, color='white')
        plt.tight_layout()

        for i, country in enumerate(countries):
            flag = FLAG_EMOJIS.get(country, '🌍')
            ax1.annotate(flag, (timestamps[i], downloads[i]),
                         xytext=(0, 10), textcoords='offset points',
                         fontsize=10, ha='center', color='yellow')

        if GRAPH_TEMP_PATH.exists():
            GRAPH_TEMP_PATH.unlink(missing_ok=True)

        plt.savefig(GRAPH_TEMP_PATH, dpi=150, bbox_inches='tight', facecolor='#1e1e1e', format='png')
        plt.close(fig)

        if GRAPH_TEMP_PATH.exists():
            pixmap = QPixmap(str(GRAPH_TEMP_PATH))
            if not pixmap.isNull():
                parent.graph_label.setPixmap(pixmap.scaled(900, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                parent.graph_label.setText("")
            else:
                parent.graph_label.setText("Failed to load graph image.")
        else:
            parent.graph_label.setText("Graph file not created.")

    except Exception as e:
        parent.graph_label.setText(f"Graph Error: {e}")