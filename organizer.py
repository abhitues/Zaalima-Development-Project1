import os
import shutil
import time
from pathlib import Path
import mimetypes

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

def organize_files(folder_path, progress_callback=None):
    """
    Organize files in folder_path.
    progress_callback(percent:int, text:str) -> used to report progress.
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
        "time_taken_sec": 0.0
    }

    # If no files, return empty analytics quickly
    if total == 0:
        analytics["time_taken_sec"] = round(time.time() - start, 3)
        if progress_callback:
            progress_callback(100, "No files to organize")
        return logs, analytics

    for i, file in enumerate(files, start=1):
        try:
            ext = file.suffix
            size = file.stat().st_size
            analytics["total_size_bytes"] += size

            category = get_category(ext)
            analytics["categories"].setdefault(category, 0)
            analytics["categories"][category] += 1

            dest_dir = folder / category
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(file), dest_dir / file.name)

            logs.append(f"Moved: {file.name} → {category}")
        except Exception as e:
            logs.append(f"Error moving {file.name}: {e}")

        # report progress
        if progress_callback and total:
            percent = int((i / total) * 100)
            progress_callback(percent, f"Processing {file.name} ({percent}%)")

    analytics["time_taken_sec"] = round(time.time() - start, 3)
    # final progress
    if progress_callback:
        progress_callback(100, f"Completed — {analytics['total_files']} files")

    return logs, analytics