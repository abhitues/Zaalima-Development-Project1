# import os
# import hashlib
# from collections import defaultdict

# def hash_file(file_path):
#     """Generate a hash for a file to compare duplicates."""
#     hash_md5 = hashlib.md5()
#     try:
#         with open(file_path, "rb") as f:
#             for chunk in iter(lambda: f.read(4096), b""):
#                 hash_md5.update(chunk)
#         return hash_md5.hexdigest()
#     except Exception as e:
#         print(f"Error hashing {file_path}: {e}")
#         return None


# def find_duplicates(folder_path):
#     """
#     Scans the folder and returns a dictionary of duplicate files.
#     Example output:
#     {
#         'd41d8cd98f00b204e9800998ecf8427e': ['C:/path/a.txt', 'C:/path/b.txt'],
#         ...
#     }
#     """
#     file_hashes = defaultdict(list)
#     duplicates = {}
#     total_files = 0

#     print(f"\nScanning folder: {folder_path}\n")

#     for root, _, files in os.walk(folder_path):
#         for file in files:
#             total_files += 1
#             file_path = os.path.join(root, file)
#             print(f"Hashing: {file_path}")  # progress message
#             file_hash = hash_file(file_path)
#             if file_hash:
#                 file_hashes[file_hash].append(file_path)

#     # Filter only duplicate hashes (more than 1 file per hash)
#     for hash_val, paths in file_hashes.items():
#         if len(paths) > 1:
#             duplicates[hash_val] = paths

#     print("\nScan complete!")
#     print(f"Total files scanned: {total_files}")
#     print(f"Duplicate sets found: {len(duplicates)}")

#     # Optional: calculate total duplicate size
#     total_duplicate_size = 0
#     for paths in duplicates.values():
#         for p in paths[1:]:  # ignore the first (original)
#             try:
#                 total_duplicate_size += os.path.getsize(p)
#             except OSError:
#                 pass
#     print(f"Total duplicate file size: {total_duplicate_size / 1024:.2f} KB")

#     # Ask user if they want to delete duplicates
#     if duplicates:
#         choice = input("\nDo you want to delete duplicate files (keep one copy)? (y/n): ").strip().lower()
#         if choice == 'y':
#             for paths in duplicates.values():
#                 for p in paths[1:]:
#                     try:
#                         os.remove(p)
#                         print(f"Deleted duplicate: {p}")
#                     except Exception as e:
#                         print(f"Could not delete {p}: {e}")
#             print("\nAll duplicates removed successfully.")
#         else:
#             print("\nNo files were deleted.")

#     return duplicates


# # Example usage
# if __name__ == "__main__":
#     folder = input("Enter the folder path to scan for duplicates: ").strip()
#     if os.path.isdir(folder):
#         find_duplicates(folder)
#     else:
#         print("Invalid folder path.")
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
        'hash1': ['path1', 'path2'],
        ...
    }
    """
    file_hashes = defaultdict(list)
    duplicates = {}
    total_files = 0

    for root, _, files in os.walk(folder_path):
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            file_hash = hash_file(file_path)
            if file_hash:
                file_hashes[file_hash].append(file_path)

    for hash_val, paths in file_hashes.items():
        if len(paths) > 1:
            duplicates[hash_val] = paths

    # Return the full results to main.py
    return duplicates
