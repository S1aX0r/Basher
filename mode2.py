#!/usr/bin/env python3
"""
mode2.py

Usage:
  python3 mode2.py

Description:
  1) Untars the 'baseline.tar.gz' into a temporary directory.
  2) Compares the extracted baseline to the current filesystem.
     - Only prints out NEW, MODIFIED, REMOVED differences (no UNCHANGED).
  3) Deletes the temporary extracted baseline.
"""

import os
import tarfile
import tempfile
import shutil
import hashlib

SIZE_THRESHOLD = 1 * 1024 * 1024  # 1MB
SKIP_DIRS = {
    '/proc',
    '/sys',
    '/dev',
    '/run',
    '/tmp',
    '/var/run',
    # add more as needed
}

def calculate_sha256(file_path, chunk_size=65536):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_baseline(baseline_dir):
    """
    Walk the extracted baseline_dir and build a dictionary:
      { relative_file_path: {"is_large": bool, "hash": <sha256 or None>, "size": int } }

    If we see *.hash => is_large = True, parse the hash/size from the file.
    Else => it's a small file copy => is_large = False.
    """
    baseline_info = {}

    for dirpath, dirnames, filenames in os.walk(baseline_dir, followlinks=False):
        rel_dir = os.path.relpath(dirpath, baseline_dir)
        if rel_dir == ".":
            rel_dir = ""

        for fname in filenames:
            full_path = os.path.join(dirpath, fname)

            if fname.endswith(".hash"):
                # large file
                base_name = fname[:-5]  # remove ".hash"
                rel_file_path = os.path.join(rel_dir, base_name)
                # parse
                file_hash = None
                file_size = None
                try:
                    with open(full_path, "r") as hf:
                        for line in hf:
                            line = line.strip()
                            if line.startswith("HASH: "):
                                file_hash = line.split("HASH: ", 1)[1]
                            elif line.startswith("SIZE: "):
                                file_size = int(line.split("SIZE: ", 1)[1])
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")

                baseline_info[rel_file_path] = {
                    "is_large": True,
                    "hash": file_hash,
                    "size": file_size,
                }
            else:
                # small file
                rel_file_path = os.path.join(rel_dir, fname)
                try:
                    file_size = os.path.getsize(full_path)
                except:
                    file_size = None
                baseline_info[rel_file_path] = {
                    "is_large": False,
                    "hash": None,
                    "size": file_size,
                }

    return baseline_info

def compare_small_files(current_file, baseline_file):
    """
    Compare two small files by hashing. Return True if identical, False otherwise.
    """
    return calculate_sha256(current_file) == calculate_sha256(baseline_file)

def mode2(root_dir='/', baseline_tar='baseline.tar.gz'):
    """
    1) Untar the baseline_tar into a temp directory.
    2) Load the baseline data.
    3) Compare with the current filesystem, skipping special dirs.
       - Only print NEW, MODIFIED, REMOVED (suppress UNCHANGED).
    4) Remove the temp directory.
    """

    root_dir = os.path.abspath(root_dir)
    baseline_tar = os.path.abspath(baseline_tar)

    if not os.path.isfile(baseline_tar):
        print(f"Error: cannot find {baseline_tar}")
        return

    # 1) Extract tar to a temp dir
    tempdir = tempfile.mkdtemp(prefix="baseline_extract_")
    print(f"Extracting baseline to {tempdir} ...")
    try:
        with tarfile.open(baseline_tar, "r:gz") as tar:
            tar.extractall(path=tempdir)
    except Exception as e:
        print(f"Error extracting {baseline_tar}: {e}")
        shutil.rmtree(tempdir, ignore_errors=True)
        return

    # Typically, the tar might contain "baseline" as the top-level folder
    # Let's find that folder
    extracted_baseline_dir = None
    for item in os.listdir(tempdir):
        candidate = os.path.join(tempdir, item)
        if os.path.isdir(candidate):
            extracted_baseline_dir = candidate
            break

    if not extracted_baseline_dir:
        print("Error: could not find extracted baseline directory!")
        shutil.rmtree(tempdir, ignore_errors=True)
        return

    # 2) Load baseline data
    baseline_info = load_baseline(extracted_baseline_dir)

    # Keep track of which baseline items we find in the current filesystem
    found_in_current = set()

    # 3) Walk the current filesystem and compare
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        abs_dirpath = os.path.abspath(dirpath)

        if any(abs_dirpath.startswith(sd) for sd in SKIP_DIRS):
            dirnames[:] = []
            filenames[:] = []
            continue

        # Also skip if it's the baseline tar file directory or tempdir
        if abs_dirpath.startswith(tempdir):
            dirnames[:] = []
            filenames[:] = []
            continue

        rel_dir = os.path.relpath(abs_dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = ""

        for fname in filenames:
            current_file = os.path.join(abs_dirpath, fname)
            if not os.path.isfile(current_file):
                continue

            rel_file_path = os.path.join(rel_dir, fname)
            found_in_current.add(rel_file_path)

            if rel_file_path not in baseline_info:
                # It's new
                print(f"NEW: {current_file}")
            else:
                # We have an entry in baseline
                info = baseline_info[rel_file_path]
                if info["is_large"]:
                    # Compare the stored hash
                    current_hash = calculate_sha256(current_file)
                    if current_hash != info["hash"]:
                        print(f"MODIFIED: {current_file}")
                    # else it's unchanged => do not print
                else:
                    # It's a small file => we have a copy
                    baseline_copy = os.path.join(extracted_baseline_dir, rel_file_path)
                    # If the baseline copy doesn't exist for some reason, call it modified
                    if not os.path.isfile(baseline_copy):
                        print(f"MODIFIED: {current_file}")
                    else:
                        # Compare the two files
                        if not compare_small_files(current_file, baseline_copy):
                            print(f"MODIFIED: {current_file}")
                        # else it's unchanged => do not print

    # 4) Anything in baseline that isn't found in current => REMOVED
    for rel_file_path in baseline_info:
        if rel_file_path not in found_in_current:
            # It's removed
            print(f"REMOVED: {rel_file_path}")

    # Clean up
    shutil.rmtree(tempdir, ignore_errors=True)
    print("Done. Temporary extracted baseline removed.")
    

if __name__ == '__main__':
    mode2()
