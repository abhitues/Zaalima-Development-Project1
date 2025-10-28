# security.py
"""
Security module for file organization application.
Features:
- Antivirus scanning using ClamAV
- MIME type verification
- Quarantine management
- Email notification system for security alerts

Email notifications are sent when:
- Threats are detected during scans
- Files are quarantined
- Security scans complete

Configure email settings in the Settings page of the GUI.
"""
import os
import shutil
import subprocess
import smtplib
from pathlib import Path
from typing import Callable, List, Tuple
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Optional dependencies
try:
    import pyclamd
    HAVE_PYCLAMD = True
except Exception:
    HAVE_PYCLAMD = False

try:
    import magic
    HAVE_MAGIC = True
except Exception:
    HAVE_MAGIC = False

# Quarantine directory (relative to application root)
QUARANTINE_DIR = Path("quarantine")
QUARANTINE_DIR.mkdir(exist_ok=True)

# Email notification configuration
EMAIL_CONFIG = {
    "enabled": False,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "recipient_email": ""
}

def load_email_config():
    """Load email configuration from a file if it exists."""
    config_file = Path("email_config.txt")
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        if key in EMAIL_CONFIG:
                            if key == "enabled":
                                EMAIL_CONFIG[key] = value.lower() == "true"
                            else:
                                EMAIL_CONFIG[key] = value
        except Exception:
            pass

def save_email_config():
    """Save email configuration to a file."""
    try:
        with open("email_config.txt", "w") as f:
            for key, value in EMAIL_CONFIG.items():
                f.write(f"{key}={value}\n")
    except Exception:
        pass

def send_email_notification(subject: str, body: str) -> bool:
    """
    Send an email notification with the provided subject and body.
    Returns True if successful, False otherwise.
    """
    if not EMAIL_CONFIG["enabled"]:
        return False
    
    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["recipient_email"]:
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = EMAIL_CONFIG["recipient_email"]
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        # Connect to SMTP server
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        
        # Send email
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False

def send_scan_report(scan_results: List[dict], mime_results: List[dict], folder_path: str):
    """
    Send an email report of the security scan results.
    """
    infected_files = [r for r in scan_results if r.get("infected")]
    mismatched_files = [m for m in mime_results if m.get("match") is False]
    
    # Subject line
    infected_count = len(infected_files)
    if infected_count > 0:
        subject = f"🚨 Security Alert: {infected_count} Threat(s) Detected"
    else:
        subject = "✅ Security Scan Completed - All Clear"
    
    # Build email body
    body = f"""File Organizer - Security Scan Report

Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Scanned Folder: {folder_path}

SCAN SUMMARY:
═══════════════════════════════════════
Total Files Scanned: {len(scan_results)}
Threats Detected: {len(infected_files)}
Suspicious Files: {len(mismatched_files)}
Clean Files: {len([r for r in scan_results if not r.get('infected')])}
═══════════════════════════════════════

"""
    
    # Add infected files details
    if infected_files:
        body += "\n🚨 DETECTED THREATS:\n"
        body += "─────────────────────────────────────\n"
        for threat in infected_files:
            filename = Path(threat["path"]).name
            detail = threat.get("detail", "Unknown threat")
            body += f"• {filename}\n"
            body += f"  Threat: {detail}\n"
            body += f"  Location: {threat['path']}\n"
            if threat.get("quarantined_to"):
                body += f"  Status: ✅ Quarantined\n"
            body += "\n"
    else:
        body += "\n✅ NO THREATS DETECTED\n"
        body += "All files have been scanned and verified as safe.\n\n"
    
    # Add mismatched files
    if mismatched_files:
        body += "\n⚠️ FILES WITH TYPE MISMATCH:\n"
        body += "─────────────────────────────────────\n"
        for mismatch in mismatched_files:
            filename = Path(mismatch["path"]).name
            mime = mismatch.get("mime", "Unknown")
            body += f"• {filename}\n"
            body += f"  Detected MIME: {mime}\n\n"
    
    body += "\n─────────────────────────────────────\n"
    body += "This is an automated security scan report.\n"
    body += "Files marked as threats have been moved to quarantine.\n"
    
    return send_email_notification(subject, body)

# Load configuration on module import
load_email_config()

def _clamd_scan_file(path: str):
    """
    Try to use pyclamd to scan a single file. Returns None for clean or a dict describing detection.
    """
    if not HAVE_PYCLAMD:
        return None

    try:
        cd = pyclamd.ClamdAgnostic()
        # may raise if clamd not available
        result = cd.scan_file(path)
        # result is None if clean
        if result:
            # result example: {'/path/to/file': ('FOUND', 'Eicar-Test-Signature')}
            return result
        return None
    except Exception:
        return None

def _clamscan_fallback(path: str) -> Tuple[bool, str]:
    """
    fallback to calling clamscan command-line if pyclamd is not available or clamd not running.
    Returns (infected_bool, message)
    """
    try:
        r = subprocess.run(["clamscan", "--no-summary", path], capture_output=True, text=True, check=False)
        out = r.stdout + r.stderr
        if "OK" in out:
            return False, "OK"
        # parse typical output: /path: Eicar-Test-Signature FOUND
        if "FOUND" in out:
            # try to parse the signature name
            parts = out.split(":")
            if len(parts) >= 2:
                msg = parts[1].strip()
            else:
                msg = out.strip()
            return True, msg
        return False, out.strip()
    except FileNotFoundError:
        return False, "clamscan-not-installed"
    except Exception as e:
        return False, f"clamscan-error: {e}"

def scan_file(path: str) -> dict:
    """
    Scans a single file using clamd if available, otherwise clamscan fallback.
    Returns a dict: { "path": path, "infected": bool, "detail": str }
    """
    path = str(path)
    # try pyclamd first
    if HAVE_PYCLAMD:
        try:
            res = _clamd_scan_file(path)
            if res:
                # map to a readable detail
                # res like {'/path': ('FOUND', 'SigName')}
                v = list(res.values())[0]
                return {"path": path, "infected": True, "detail": f"{v[1]} ({v[0]})"}
            else:
                return {"path": path, "infected": False, "detail": "OK (clamd)"}
        except Exception:
            pass

    # fallback to clamscan CLI
    infected, msg = _clamscan_fallback(path)
    return {"path": path, "infected": infected, "detail": msg}

def verify_mime(path: str, expected_mime_prefix: str = None) -> dict:
    """
    Uses python-magic to detect the file mime. If expected_mime_prefix is provided
    (example: 'image/' for images), returns mismatch if prefix not in mime.
    """
    if not HAVE_MAGIC:
        return {"path": str(path), "mime": None, "match": None, "detail": "python-magic not installed"}
    try:
        mime = magic.from_file(str(path), mime=True)
        match = None
        if expected_mime_prefix:
            match = expected_mime_prefix in mime
        return {"path": str(path), "mime": mime, "match": match, "detail": "OK"}
    except Exception as e:
        return {"path": str(path), "mime": None, "match": False, "detail": f"magic-error: {e}"}

def move_to_quarantine(path: str) -> str:
    """
    Move a suspicious file to quarantine and return new path.
    """
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(path)
    dest = QUARANTINE_DIR / src.name
    # ensure unique name (avoid overwrite)
    counter = 1
    base = src.stem
    suf = src.suffix
    while dest.exists():
        dest = QUARANTINE_DIR / f"{base}_{counter}{suf}"
        counter += 1
    shutil.move(str(src), str(dest))
    return str(dest)

def restore_from_quarantine(filename: str, dest_folder: str) -> str:
    """
    Restore a file from quarantine to dest_folder (destination must exist).
    Returns restored path.
    """
    qpath = QUARANTINE_DIR / filename
    if not qpath.exists():
        raise FileNotFoundError(filename)
    dest = Path(dest_folder) / qpath.name
    shutil.move(str(qpath), str(dest))
    return str(dest)

def delete_from_quarantine(filename: str) -> bool:
    qpath = QUARANTINE_DIR / filename
    if qpath.exists():
        qpath.unlink()
        return True
    return False

def list_quarantine() -> List[str]:
    return [p.name for p in QUARANTINE_DIR.iterdir() if p.is_file()]

def scan_folder(folder: str, expected_mime_map: dict = None, progress_callback: Callable[[int, str], None] = None) -> Tuple[List[dict], List[dict]]:
    """
    Scan all files under 'folder'. expected_mime_map: optional map of extension -> mime prefix to validate (e.g. {'.jpg':'image/'}).
    progress_callback(percent:int, text:str) can be used to show progress.
    Returns tuple: (scan_results_list, mime_checks_list)
    """
    folder = Path(folder)
    files = [p for p in folder.rglob("*") if p.is_file()]
    total = len(files)
    scan_results = []
    mime_results = []

    for i, f in enumerate(files, start=1):
        pct = int(i / total * 100) if total else 100
        if progress_callback:
            progress_callback(pct, f"Scanning {f.name} ({i}/{total})")
        # antivirus scan
        s = scan_file(str(f))
        if s.get("infected"):
            # move to quarantine
            try:
                qpath = move_to_quarantine(str(f))
                s["quarantined_to"] = qpath
            except Exception as e:
                s["quarantine_error"] = str(e)
        scan_results.append(s)

        # mime/type verification if map provided
        if expected_mime_map:
            ext = f.suffix.lower()
            expected = expected_mime_map.get(ext)
            if expected:
                m = verify_mime(str(f), expected)
                if m.get("match") is False:
                    # suspicious: move to quarantine also
                    try:
                        qpath = move_to_quarantine(str(f))
                        m["quarantined_to"] = qpath
                    except Exception as e:
                        m["quarantine_error"] = str(e)
                mime_results.append(m)

    if progress_callback:
        progress_callback(100, "Security scan completed.")
    
    # Send email report if enabled
    infected_count = len([r for r in scan_results if r.get("infected")])
    if infected_count > 0 or EMAIL_CONFIG.get("always_send", False):
        send_scan_report(scan_results, mime_results, str(folder))
    
    return scan_results, mime_results
