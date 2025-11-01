import os
import hashlib
from collections import defaultdict

def hash_file(file_path):
    """Generate a hash for a file to compare duplicates."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error hashing {file_path}: {e}")
        return None


def find_duplicates(folder_path):
    """
    Scans the folder and returns a dictionary of duplicate files.
    Example output:
    {
        'd41d8cd98f00b204e9800998ecf8427e': ['C:/path/a.txt', 'C:/path/b.txt'],
        ...
    }
    """
    file_hashes = defaultdict(list)
    duplicates = {}

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = hash_file(file_path)
            if file_hash:
                file_hashes[file_hash].append(file_path)

    # Filter only duplicate hashes (more than 1 file per hash)
    for hash_val, paths in file_hashes.items():
        if len(paths) > 1:
            duplicates[hash_val] = paths

    return duplicates
