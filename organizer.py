import os
import shutil
import time
from pathlib import Path
import mimetypes
import security

# Basic categories (you can extend)
FILE_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".csv"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Music": [".mp3", ".wav", ".aac", ".flac"],
    "Archives": [".zip", ".rar", ".tar", ".gz"],
}

def get_category(extension: str) -> str:
    """Return category name for an extension, or 'Others'."""
    ext = extension.lower()
    for cat, exts in FILE_CATEGORIES.items():
        if ext in exts:
            return cat
    mime = mimetypes.guess_type("file" + ext)[0]
    if mime:
        main_type = mime.split("/")[0]
        if main_type in ["image", "video", "audio"]:
            return main_type.capitalize() + "s"
    return "Others"

def organize_files(folder_path, progress_callback=None, enable_security=True):
    """
    Organize files in folder_path with optional security scanning.
    progress_callback(percent:int, text:str) -> used to report progress.
    enable_security: If True, scan files for threats before organizing.
    Returns: (logs:list[str], analytics:dict)
    """
    start = time.time()
    folder = Path(folder_path)
    files = [f for f in folder.iterdir() if f.is_file()]
    total = len(files)

    logs = []
    analytics = {
        "total_files": total,
        "total_size_bytes": 0,
        "categories": {},   # e.g. {"Images": 10, "Documents": 5}
        "time_taken_sec": 0.0,
        "security_scan": {
            "scanned": 0,
            "infected": 0,
            "quarantined": 0,
            "clean": 0
        }
    }

    # If no files, return empty analytics quickly
    if total == 0:
        analytics["time_taken_sec"] = round(time.time() - start, 3)
        if progress_callback:
            progress_callback(100, "No files to organize")
        return logs, analytics

    for i, file in enumerate(files, start=1):
        try:
            # Security scanning
            if enable_security:
                if progress_callback:
                    progress_callback(int((i / total) * 50), f"🔒 Scanning {file.name}...")
                
                scan_result = security.scan_file(str(file))
                analytics["security_scan"]["scanned"] += 1
                
                if scan_result.get("infected", False):
                    # File is infected - move to quarantine instead
                    try:
                        qpath = security.move_to_quarantine(str(file))
                        logs.append(f"🚨 THREAT DETECTED & QUARANTINED: {file.name} → {scan_result.get('detail', 'virus')}")
                        analytics["security_scan"]["infected"] += 1
                        analytics["security_scan"]["quarantined"] += 1
                    except Exception as e:
                        logs.append(f"🚨 INFECTED: {file.name} (quarantine failed: {e})")
                    continue  # Skip organizing this file
                else:
                    analytics["security_scan"]["clean"] += 1
                    logs.append(f"✓ Security check passed: {file.name}")

            # File organization
            ext = file.suffix
            size = file.stat().st_size
            analytics["total_size_bytes"] += size

            category = get_category(ext)
            analytics["categories"].setdefault(category, 0)
            analytics["categories"][category] += 1

            if progress_callback:
                progress_callback(int((i / total) * 50) + 50, f"📁 Organizing {file.name}...")

            dest_dir = folder / category
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(file), dest_dir / file.name)

            logs.append(f"Moved: {file.name} → {category}")
        except Exception as e:
            logs.append(f"Error moving {file.name}: {e}")

    analytics["time_taken_sec"] = round(time.time() - start, 3)
    
    # Add security summary to logs if security was enabled
    if enable_security:
        sec_info = analytics["security_scan"]
        if sec_info["infected"] > 0:
            logs.insert(0, f"⚠️ Security Alert: {sec_info['infected']} threat(s) detected and quarantined!")
        logs.insert(0, f"🔒 Security: {sec_info['clean']} files scanned and verified safe.")
    
    # final progress
    if progress_callback:
        progress_callback(100, f"Completed — {analytics['total_files']} files")
        if enable_security and analytics["security_scan"]["infected"] > 0:
            progress_callback(100, f"⚠️ {analytics['security_scan']['infected']} threat(s) quarantined!")
    # --- Generate Analytics Chart (Pie chart of file categories) ---
    if analytics["categories"]:
        try:
            labels = list(analytics["categories"].keys())
            sizes = list(analytics["categories"].values())

            plt.figure(figsize=(6, 6))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title("File Category Distribution")

            # ✅ Save chart as image for email attachment
            plt.savefig("analytics.png")
            plt.close()
            
            logs.append("📊 Analytics chart saved as analytics.png")
        except Exception as e:
            logs.append(f"⚠️ Failed to generate chart: {e}")


    return logs, analytics