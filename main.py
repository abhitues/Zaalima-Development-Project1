import sys
import threading
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QHBoxLayout, QListWidget,
    QListWidgetItem, QStackedWidget, QMessageBox, QSizePolicy, QScrollArea,
    QFrame, QGridLayout, QCheckBox, QLineEdit
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from organizer import organize_files
from email_notifier import send_summary_mail
import security

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
    security_scan_signal = pyqtSignal(list, list)
    quarantine_update_signal = pyqtSignal()

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
        self.security_scan_signal.connect(self.show_scan_results)
        self.quarantine_update_signal.connect(self.refresh_quarantine_list)

        # layout
        layout = QHBoxLayout(self)

        # Sidebar
        self.sidebar = QListWidget()
        for name, icon in [("Home", "assets/home.png"),
                           ("Logs", "assets/logs.png"),
                           ("Analytics", "assets/analysis.png"),
                           ("🔒 Security", "assets/security.png"),
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

        # --- Security page ---
        security_page = QWidget()
        sec_layout = QVBoxLayout(security_page)
        sec_layout.setAlignment(Qt.AlignTop)
        
        sec_head = QLabel("🔒 Security Scanner")
        sec_head.setFont(QFont("Segoe UI", 14))
        sec_layout.addWidget(sec_head)
        
        # Scan section
        scan_section = QFrame()
        scan_layout = QVBoxLayout(scan_section)
        
        scan_info = QLabel("🔍 Scan a folder for threats and suspicious files")
        scan_layout.addWidget(scan_info)
        
        btn_layout = QHBoxLayout()
        self.security_folder_btn = QPushButton("📁 Select Folder")
        self.security_folder_btn.clicked.connect(self.browse_security_folder)
        btn_layout.addWidget(self.security_folder_btn)
        
        self.scan_btn = QPushButton("🔍 Scan Folder")
        self.scan_btn.clicked.connect(self.start_security_scan)
        btn_layout.addWidget(self.scan_btn)
        scan_layout.addLayout(btn_layout)
        
        self.security_folder_label = QLabel("No folder selected")
        scan_layout.addWidget(self.security_folder_label)
        
        self.security_progress = QProgressBar()
        self.security_progress.setValue(0)
        self.security_progress.setFixedHeight(22)
        scan_layout.addWidget(self.security_progress)
        
        self.security_status = QLabel("")
        scan_layout.addWidget(self.security_status)
        
        sec_layout.addWidget(scan_section)
        
        # Results section
        results_section = QFrame()
        results_layout = QVBoxLayout(results_section)
        results_label = QLabel("📋 Scan Results")
        results_label.setFont(QFont("Segoe UI", 12))
        results_layout.addWidget(results_label)
        
        self.scan_results_list = QListWidget()
        results_layout.addWidget(self.scan_results_list)
        
        sec_layout.addWidget(results_section)
        
        # Quarantine section
        quarantine_section = QFrame()
        q_layout = QVBoxLayout(quarantine_section)
        q_label = QLabel("🧱 Quarantined Files")
        q_label.setFont(QFont("Segoe UI", 12))
        q_layout.addWidget(q_label)
        
        # Quarantine buttons
        q_btn_layout = QHBoxLayout()
        self.refresh_q_btn = QPushButton("🔄 Refresh")
        self.refresh_q_btn.clicked.connect(self.refresh_quarantine_list)
        q_btn_layout.addWidget(self.refresh_q_btn)
        q_layout.addLayout(q_btn_layout)
        
        self.quarantine_list = QListWidget()
        q_layout.addWidget(self.quarantine_list)
        
        # Action buttons for quarantine items
        q_action_layout = QHBoxLayout()
        self.restore_q_btn = QPushButton("↩️ Restore")
        self.restore_q_btn.clicked.connect(self.restore_from_quarantine)
        q_action_layout.addWidget(self.restore_q_btn)
        
        self.delete_q_btn = QPushButton("🗑️ Delete")
        self.delete_q_btn.clicked.connect(self.delete_from_quarantine)
        q_action_layout.addWidget(self.delete_q_btn)
        
        self.rescan_q_btn = QPushButton("🔍 Rescan")
        self.rescan_q_btn.clicked.connect(self.rescan_quarantine)
        q_action_layout.addWidget(self.rescan_q_btn)
        q_layout.addLayout(q_action_layout)
        
        sec_layout.addWidget(quarantine_section)
        
        self.stack.addWidget(security_page)

        # --- Settings page ---
        settings_page = QWidget()
        set_layout = QVBoxLayout(settings_page)
        set_layout.setAlignment(Qt.AlignTop)
        
        # Email configuration section
        email_section = QFrame()
        email_layout = QVBoxLayout(email_section)
        
        email_title = QLabel("📧 Email Notifications")
        email_title.setFont(QFont("Segoe UI", 14))
        email_layout.addWidget(email_title)
        
        email_info = QLabel("Configure email notifications for security scan reports")
        email_layout.addWidget(email_info)
        
        # Email fields
        self.email_enabled_cb = QCheckBox("Enable Email Notifications")
        self.email_enabled_cb.setChecked(security.EMAIL_CONFIG.get("enabled", False))
        email_layout.addWidget(self.email_enabled_cb)
        
        sender_layout = QHBoxLayout()
        sender_layout.addWidget(QLabel("Sender Email:"))
        self.sender_email_input = QLineEdit()
        self.sender_email_input.setText(security.EMAIL_CONFIG.get("sender_email", ""))
        self.sender_email_input.setPlaceholderText("your.email@gmail.com")
        sender_layout.addWidget(self.sender_email_input)
        email_layout.addLayout(sender_layout)
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.sender_password_input = QLineEdit()
        self.sender_password_input.setText(security.EMAIL_CONFIG.get("sender_password", ""))
        self.sender_password_input.setPlaceholderText("Your email password or app password")
        self.sender_password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.sender_password_input)
        email_layout.addLayout(password_layout)
        
        recipient_layout = QHBoxLayout()
        recipient_layout.addWidget(QLabel("Recipient:"))
        self.recipient_email_input = QLineEdit()
        self.recipient_email_input.setText(security.EMAIL_CONFIG.get("recipient_email", ""))
        self.recipient_email_input.setPlaceholderText("recipient@example.com")
        recipient_layout.addWidget(self.recipient_email_input)
        email_layout.addLayout(recipient_layout)
        
        # Save button
        save_email_btn = QPushButton("💾 Save Email Settings")
        save_email_btn.clicked.connect(self.save_email_config)
        email_layout.addWidget(save_email_btn)
        
        # Test button
        test_email_btn = QPushButton("📤 Test Email (Send Now)")
        test_email_btn.clicked.connect(self.test_email)
        email_layout.addWidget(test_email_btn)
        
        email_note = QLabel("Note: For Gmail, use App Password instead of regular password.\nEnable 2FA and generate App Password in Google Account settings.")
        email_note.setWordWrap(True)
        email_note.setStyleSheet("color: #999; font-size: 10px;")
        email_layout.addWidget(email_note)
        
        set_layout.addWidget(email_section)
        
        # Add spacer
        set_layout.addStretch()
        
        self.stack.addWidget(settings_page)

        self.sidebar.setCurrentRow(0)

        self.folder_path = None
        self.security_folder_path = None
        self.logs = []
        self.quarantine_list_current = []

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
            "time_taken_sec": float,
            "security_scan": { "scanned": int, "infected": int, "quarantined": int, "clean": int }
        }
        """
        # summary
        total_files = analytics.get("total_files", 0)
        total_size_mb = analytics.get("total_size_bytes", 0) / (1024 * 1024)
        time_taken = analytics.get("time_taken_sec", 0.0)
        categories = analytics.get("categories", {})
        security_scan = analytics.get("security_scan", {})

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
        
        # Add security information
        if security_scan.get("scanned", 0) > 0:
            infected = security_scan.get("infected", 0)
            scanned = security_scan.get("scanned", 0)
            clean = security_scan.get("clean", 0)
            
            if infected > 0:
                summary += f"\n\n🚨 Security: {infected} threat(s) detected and quarantined!"
            else:
                summary += f"\n\n🔒 Security: {scanned} file(s) scanned, all clean ✓"

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
            self.canvas.figure.savefig("analytics.png")

            return

        labels = list(categories.keys())
        sizes = list(categories.values())

        # avoid 0 or negative values; Matplotlib will handle sizes normally
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        self.canvas.draw()

    # ===== Security Page Methods =====
    def browse_security_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.security_folder_path = folder
            self.security_folder_label.setText(f"Selected: {folder}")

    def start_security_scan(self):
        if not self.security_folder_path:
            QMessageBox.warning(self, "Warning", "Please select a folder to scan first!")
            return

        self.security_status.setText("Scanning for threats...")
        self.security_progress.setValue(0)
        self.scan_results_list.clear()

        def run_scan():
            scan_results, mime_results = security.scan_folder(
                self.security_folder_path,
                progress_callback=self.emit_security_progress
            )
            self.security_scan_signal.emit(scan_results, mime_results)

        thread = threading.Thread(target=run_scan)
        thread.start()

    def emit_security_progress(self, percent, text):
        self.progress_signal.emit(percent, f"🔒 {text}")

    def show_scan_results(self, scan_results, mime_results):
        self.scan_results_list.clear()
        
        infected_count = 0
        for result in scan_results:
            if result.get("infected"):
                item_text = f"🚨 THREAT: {Path(result['path']).name} - {result.get('detail', 'Unknown threat')}"
                self.scan_results_list.addItem(item_text)
                infected_count += 1
            else:
                item_text = f"✓ Clean: {Path(result['path']).name}"
                self.scan_results_list.addItem(item_text)
        
        for result in mime_results:
            if result.get("match") is False:
                item_text = f"⚠️ Type Mismatch: {Path(result['path']).name} - {result.get('mime', 'Unknown')}"
                self.scan_results_list.addItem(item_text)
                infected_count += 1
        
        if infected_count > 0:
            self.security_status.setText(f"⚠️ {infected_count} threat(s) found and quarantined!")
            email_notice = ""
            if security.EMAIL_CONFIG.get("enabled", False):
                email_notice = "\n📧 Email notification sent!"
            QMessageBox.warning(self, "Security Alert", f"{infected_count} threat(s) detected and moved to quarantine!{email_notice}")
        else:
            self.security_status.setText("✅ All files scanned and verified safe")
            if security.EMAIL_CONFIG.get("enabled", False):
                self.security_status.setText("✅ All files scanned and verified safe - Email report sent! 📧")
        
        self.security_progress.setValue(100)
        self.refresh_quarantine_list()

    def refresh_quarantine_list(self):
        self.quarantine_list.clear()
        try:
            files = security.list_quarantine()
            self.quarantine_list_current = files
            for f in files:
                self.quarantine_list.addItem(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load quarantine: {e}")

    def restore_from_quarantine(self):
        current_item = self.quarantine_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a file from quarantine.")
            return
        
        filename = current_item.text()
        folder = QFileDialog.getExistingDirectory(self, "Select folder to restore file to")
        if folder:
            try:
                restored_path = security.restore_from_quarantine(filename, folder)
                QMessageBox.information(self, "Success", f"File restored to: {restored_path}")
                self.refresh_quarantine_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to restore: {e}")

    def delete_from_quarantine(self):
        current_item = self.quarantine_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a file from quarantine.")
            return
        
        filename = current_item.text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete '{filename}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if security.delete_from_quarantine(filename):
                    QMessageBox.information(self, "Success", "File deleted successfully.")
                    self.refresh_quarantine_list()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete file.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}")

    def rescan_quarantine(self):
        current_item = self.quarantine_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a file from quarantine.")
            return
        
        filename = current_item.text()
        qpath = security.QUARANTINE_DIR / filename
        
        if not qpath.exists():
            QMessageBox.warning(self, "Error", "File not found in quarantine.")
            return
        
        # Rescan the file
        result = security.scan_file(str(qpath))
        
        if result.get("infected"):
            QMessageBox.warning(
                self, "Still Infected",
                f"⚠️ File is still infected: {result.get('detail', 'Unknown threat')}\n"
                "Keeping file in quarantine."
            )
        else:
            QMessageBox.information(
                self, "Clean",
                "✅ File appears to be clean now.\nYou can restore it."
            )
    
    # ===== Settings Page Methods =====
    def save_email_config(self):
        """Save email configuration from the UI."""
        try:
            security.EMAIL_CONFIG["enabled"] = self.email_enabled_cb.isChecked()
            security.EMAIL_CONFIG["sender_email"] = self.sender_email_input.text()
            security.EMAIL_CONFIG["sender_password"] = self.sender_password_input.text()
            security.EMAIL_CONFIG["recipient_email"] = self.recipient_email_input.text()
            
            # Save to file
            security.save_email_config()
            
            QMessageBox.information(self, "Success", "Email settings saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save email settings: {e}")
    
    def test_email(self):
        """Send a test email to verify configuration."""
        if not self.email_enabled_cb.isChecked():
            QMessageBox.warning(self, "Warning", "Please enable email notifications first.")
            return
        
        sender_email = self.sender_email_input.text()
        sender_password = self.sender_password_input.text()
        recipient_email = self.recipient_email_input.text()
        
        if not sender_email or not sender_password or not recipient_email:
            QMessageBox.warning(self, "Warning", "Please fill in all email fields.")
            return
        
        # Temporarily update config for test
        old_config = security.EMAIL_CONFIG.copy()
        security.EMAIL_CONFIG["enabled"] = True
        security.EMAIL_CONFIG["sender_email"] = sender_email
        security.EMAIL_CONFIG["sender_password"] = sender_password
        security.EMAIL_CONFIG["recipient_email"] = recipient_email
        
        try:
            subject = "✅ File Organizer - Test Email"
            body = """This is a test email from File Organizer Security Scanner.

If you received this email, your email configuration is working correctly!

You will receive email notifications when:
• Threats are detected during security scans
• Files are quarantined
• Security scans are completed

Configure these settings in the Settings page."""

            if security.send_email_notification(subject, body):
                QMessageBox.information(
                    self, "Success",
                    "Test email sent successfully!\nPlease check your inbox."
                )
            else:
                detail = security.EMAIL_LAST_ERROR or "Unknown error"
                QMessageBox.warning(
                    self, "Failed",
                    f"Failed to send test email.\n\nDetails: {detail}\n\n"
                    "Tips:\n- Use a Gmail App Password (not your normal password)\n"
                    "- Ensure SMTP server/port are correct (smtp.gmail.com:587)\n"
                    "- Check internet/firewall/proxy settings"
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to send test email: {e}")
        finally:
            # Restore old config
            security.EMAIL_CONFIG = old_config


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FileOrganizerApp()
    win.show()
    sys.exit(app.exec_())