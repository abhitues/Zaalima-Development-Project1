import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QHBoxLayout, QListWidget,
    QListWidgetItem, QStackedWidget, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from organizer import organize_files

from email_notifier import send_summary_mail
from duplicate_detector import find_duplicates


# Matplotlib for chart embedding
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=4, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        fig.tight_layout()


class FileOrganizerApp(QWidget):
    # signals
    progress_signal = pyqtSignal(int, str)
    log_signal = pyqtSignal(list)
    status_signal = pyqtSignal(str)
    analytics_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Organizer")
        self.setWindowIcon(QIcon("assets/logo.png"))
        self.resize(1000, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: white;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #0078D4;
                border-radius: 8px;
                padding: 8px 14px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #2c2c2c;
            }
            QProgressBar::chunk {
                background-color: #00C853;
                width: 10px;
            }
            QLabel#headline {
                font-size: 18px;
                font-weight: 600;
            }
        """)

        # connect signals
        self.progress_signal.connect(self.update_progress)
        self.log_signal.connect(self.show_logs)
        self.status_signal.connect(self.status_set_text)
        self.analytics_signal.connect(self.show_analytics_page)

        # layout
        layout = QHBoxLayout(self)

        # Sidebar
        self.sidebar = QListWidget()
        for name, icon in [("Home", "assets/home.png"),
                           ("Logs", "assets/logs.png"),
                           ("Analytics", "assets/analysis.png"),
                           ("Settings", "assets/settings.png")]:
            item = QListWidgetItem(QIcon(icon), name)
            item.setTextAlignment(Qt.AlignCenter)
            self.sidebar.addItem(item)
        self.sidebar.setFixedWidth(160)
        self.sidebar.currentRowChanged.connect(self.display_page)
        layout.addWidget(self.sidebar)

        # Stack pages
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- Home page ---
        home_page = QWidget()
        h_layout = QVBoxLayout(home_page)
        h_layout.setAlignment(Qt.AlignTop)

        headline = QLabel("📁Choose a Folder to Organize")
        headline.setObjectName("headline")
        headline.setFont(QFont("Segoe UI", 16))
        h_layout.addWidget(headline, alignment=Qt.AlignCenter)

        self.select_btn = QPushButton("Browse Folder")
        self.select_btn.clicked.connect(self.browse_folder)
        h_layout.addWidget(self.select_btn, alignment=Qt.AlignCenter)

        self.path_label = QLabel("")
        h_layout.addWidget(self.path_label, alignment=Qt.AlignCenter)

        self.start_btn = QPushButton("🚀 Start Organizing")
        self.start_btn.clicked.connect(self.start_organize)
        h_layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFixedHeight(22)
        h_layout.addWidget(self.progress)

        self.status = QLabel("")
        h_layout.addWidget(self.status, alignment=Qt.AlignCenter)

        self.duplicate_btn = QPushButton("🧩 Find Duplicate Files")
        self.duplicate_btn.clicked.connect(self.find_duplicate_files)
        h_layout.addWidget(self.duplicate_btn, alignment=Qt.AlignCenter)


        # quick analytics summary under the progress
        self.quick_stats = QLabel("")
        self.quick_stats.setWordWrap(True)
        h_layout.addWidget(self.quick_stats, alignment=Qt.AlignCenter)

        self.stack.addWidget(home_page)

        # --- Logs page ---
        log_page = QWidget()
        log_layout = QVBoxLayout(log_page)
        log_layout.setAlignment(Qt.AlignTop)

        log_head = QLabel("📜 Recent Logs")
        log_head.setFont(QFont("Segoe UI", 14))
        log_layout.addWidget(log_head)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)

        self.stack.addWidget(log_page)

        # --- Analytics page ---
        analytics_page = QWidget()
        an_layout = QVBoxLayout(analytics_page)
        an_layout.setAlignment(Qt.AlignTop)

        an_head = QLabel("📊 Analytics")
        an_head.setFont(QFont("Segoe UI", 14))
        an_layout.addWidget(an_head)

        # summary label
        self.analytics_summary = QLabel("No analytics yet.")
        self.analytics_summary.setWordWrap(True)
        an_layout.addWidget(self.analytics_summary)

        # Matplotlib canvas
        self.canvas = MatplotlibCanvas(self, width=5, height=4, dpi=100)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        an_layout.addWidget(self.canvas)

        self.stack.addWidget(analytics_page)

        # --- Settings page ---
        settings_page = QWidget()
        set_layout = QVBoxLayout(settings_page)
        set_layout.addWidget(QLabel("⚙️ Settings Coming Soon..."))
        self.stack.addWidget(settings_page)

        self.sidebar.setCurrentRow(0)

        self.folder_path = None
        self.logs = []

    def display_page(self, index):
        self.stack.setCurrentIndex(index)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.path_label.setText(f"Selected: {folder}")

    def start_organize(self):
        if not self.folder_path:
            QMessageBox.warning(self, "Warning", "Please select a folder first!")
            return

        self.status.setText("Organizing files...")
        self.progress.setValue(0)
        self.quick_stats.setText("")

        def run():
            logs, analytics = organize_files(self.folder_path, self.emit_progress)
            # emit logs and analytics back to main thread
            self.log_signal.emit(logs)
            self.analytics_signal.emit(analytics)
            self.status_signal.emit("✅ Completed!")
            
         # Safe email sending with error handling
            try:
                send_summary_mail("abhishektues@gmail.com", analytics)
                self.status_signal.emit("📧 Email report sent successfully!")
            except Exception as e:
                self.status_signal.emit(f"⚠️ Email failed: {e}")
        
        thread = threading.Thread(target=run)
        thread.start()
    
    def find_duplicate_files(self):
        if not self.folder_path:
           QMessageBox.warning(self, "Warning", "Please select a folder first!")
           return

        self.status.setText("🔍 Scanning for duplicate files...")
        self.progress.setValue(0)

    # ✅ define inner thread function
        def run():
            try:
            # find duplicates using helper function
                duplicates = find_duplicates(self.folder_path)

                if not duplicates:
                  self.status_signal.emit("✅ No duplicate files found!")
                  return

            # Prepare result text
                report = "⚠️ Duplicate Files Found:\n\n"
                for i, (hash_val, files) in enumerate(duplicates.items(), start=1):
                    report += f"\nSet {i}:\n" + "\n".join(f"  - {f}" for f in files)

            # show results safely
                self.log_signal.emit([report])
                self.status_signal.emit("⚠️ Duplicate files detected — see Logs tab for details.")
                self.sidebar.setCurrentRow(1)  # switch to Logs tab

            except Exception as e:
                self.status_signal.emit(f"❌ Error finding duplicates: {e}")

        # ✅ run it in a separate thread
        thread = threading.Thread(target=run)
        thread.start()



    def emit_progress(self, percent, text):
        # called from worker thread
        self.progress_signal.emit(percent, text)

    # ---------- Slots ----------
    def update_progress(self, percent, text):
        self.progress.setValue(percent)
        self.status.setText(text)

    def show_logs(self, logs):
        # append logs safely
        self.log_box.append("\n".join(logs))

    def status_set_text(self, text):
        self.status.setText(text)

    def show_analytics_page(self, analytics: dict):
        """
        Receives analytics dict from worker thread and updates the Analytics UI.
        analytics: {
            "total_files": int,
            "total_size_bytes": int,
            "categories": { "Images": 10, ... },
            "time_taken_sec": float
        }
        """
        # summary
        total_files = analytics.get("total_files", 0)
        total_size_mb = analytics.get("total_size_bytes", 0) / (1024 * 1024)
        time_taken = analytics.get("time_taken_sec", 0.0)
        categories = analytics.get("categories", {})

        summary = (
            f"📌 Total files organized: {total_files}\n"
            f"💾 Total size: {total_size_mb:.2f} MB\n"
            f"⏱ Time taken: {time_taken:.2f} sec\n"
        )
        if categories:
            cat_list = ", ".join(f"{k} ({v})" for k, v in categories.items())
            summary += f"📂 Categories: {cat_list}"
        else:
            summary += "📂 Categories: None"

        self.analytics_summary.setText(summary)
        # quick stats below progress on Home page
        self.quick_stats.setText(summary)

        # draw pie chart for category distribution
        self.draw_pie_chart(categories)

        # switch to Analytics page automatically (optional)
        self.sidebar.setCurrentRow(2)  # index for Analytics page

    def draw_pie_chart(self, categories: dict):
        ax = self.canvas.axes
        ax.clear()

        if not categories:
            ax.text(0.5, 0.5, "No data", horizontalalignment='center', verticalalignment='center')
            self.canvas.draw()
            return

        labels = list(categories.keys())
        sizes = list(categories.values())

        # avoid 0 or negative values; Matplotlib will handle sizes normally
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FileOrganizerApp()
    win.show()
    sys.exit(app.exec_())
