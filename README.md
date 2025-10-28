# File Organizer - Security Scanner with Email Notifications

A PyQt5-based file organization application with built-in security scanning and email notifications.

## Features

- 📁 **File Organization** - Automatically organize files by type
- 🔒 **Security Scanning** - Scan files for malware and threats
- 🧱 **Quarantine System** - Isolate suspicious files safely
- 📧 **Email Notifications** - Get notified via email when threats are detected
- 📊 **Analytics** - View file statistics and charts

## Installation

1. **Install Python** (3.7 or higher)

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Install antivirus scanner:**
   - Install ClamAV: https://www.clamav.net/
   - This enables antivirus scanning functionality

## Running the Application

### On Windows:
```powershell
python main.py
```

### On Linux/Mac:
```bash
python3 main.py
```

## Using Email Notifications

1. **Open the Settings page** in the application
2. **Configure your email:**
   - Sender Email: Your Gmail address
   - Password: Generate an App Password (see below)
   - Recipient Email: Where to send notifications
3. **Enable Email Notifications** checkbox
4. **Click "Save Email Settings"**
5. **Click "Test Email (Send Now)"** to verify it works

### Gmail Setup

For Gmail users, you need to create an App Password:

1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Go to "App passwords": https://myaccount.google.com/apppasswords
4. Generate a new app password for "Mail"
5. Use this 16-character password in the application

### Other Email Providers

- **Outlook/Hotmail**: smtp.office365.com, Port 587
- **Yahoo**: smtp.mail.yahoo.com, Port 587
- **Custom SMTP**: Configure in the Settings page

## Usage

### Organize Files
1. Click **"Browse Folder"** on the Home page
2. Select the folder to organize
3. Click **"Start Organizing"**
4. Files will be sorted into categories (Documents, Images, Videos, etc.)

### Security Scan
1. Go to the **🔒 Security** page
2. Click **"Select Folder"**
3. Choose folder to scan
4. Click **"Scan Folder"**
5. View results in the scan results list
6. Check quarantined files section
7. Options: Restore, Delete, or Rescan files

### View Reports
- **Analytics**: See file distribution charts
- **Logs**: View detailed operation logs
- **Email**: Receive email reports when threats are detected

## Project Structure

```
.
├── main.py           # Main GUI application
├── organizer.py      # File organization logic
├── security.py       # Security scanning & email notifications
├── quarantine/       # Quarantined files storage
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Email Notification Features

- Automatic reports sent when threats are detected
- Detailed threat information
- Scan statistics
- Quarantine status updates
- Professional formatted email reports

## Security Features

- ✅ Antivirus scanning (ClamAV)
- ✅ MIME type verification
- ✅ Quarantine system for suspicious files
- ✅ Email alerts for security events
- ✅ Detailed security logs

## Troubleshooting

**Email not sending?**
- Check SMTP server settings
- Verify App Password for Gmail
- Check firewall settings
- Ensure recipient email is correct

**Antivirus not working?**
- Install ClamAV on your system
- Make sure ClamAV daemon is running
- Check path to clamscan executable

## License

This project is for educational purposes.


