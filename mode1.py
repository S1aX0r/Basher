#!/usr/bin/env python3
"""
mode1.py

Usage:
  python3 mode1.py

Description:
  1) Creates a baseline directory by scanning the filesystem.
  2) If a file is larger than 1MB, store a .hash file with its SHA256.
  3) Otherwise, copy the file fully.
  4) Tars the 'baseline' directory to 'baseline.tar.gz'.
  5) Removes the 'baseline' directory.
"""

import os
import shutil
import hashlib
import tarfile

SIZE_THRESHOLD = 1 * 1024 * 1024  # 1MB
SKIP_DIRS = {
    '/proc',
    '/sys',
    '/dev',
    '/run',
    '/tmp',
    '/var/run',
    # Add more as needed
}

def calculate_sha256(file_path, chunk_size=65536):
    """
    Calculate SHA-256 hash of a file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def mode1(root_dir='/', baseline_dir='./baseline', baseline_tar='baseline.tar.gz'):
    """
    1) Walk 'root_dir', skip system dirs, build the 'baseline_dir'.
    2) Tar up 'baseline_dir' into 'baseline.tar.gz'.
    3) Remove 'baseline_dir'.
    """

    root_dir = os.path.abspath(root_dir)
    baseline_dir = os.path.abspath(baseline_dir)
    baseline_tar = os.path.abspath(baseline_tar)

    print(f"Building baseline from {root_dir} into {baseline_dir}...")

    # Create the baseline directory
    os.makedirs(baseline_dir, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        # Skip special directories
        abs_dirpath = os.path.abspath(dirpath)

        # Also skip if it's our baseline directory or the tar file's path
        # (in case someone put baseline_tar in root_dir)
        if abs_dirpath.startswith(baseline_dir) or abs_dirpath in SKIP_DIRS:
            dirnames[:] = []
            filenames[:] = []
            continue

        # Also skip if this directory is in SKIP_DIRS by prefix
        if any(abs_dirpath.startswith(sd) for sd in SKIP_DIRS):
            dirnames[:] = []
            filenames[:] = []
            continue

        # Figure out the corresponding path inside baseline_dir
        rel_path = os.path.relpath(abs_dirpath, root_dir)
        if rel_path == '.':
            rel_path = ''
        sub_baseline_dir = os.path.join(baseline_dir, rel_path)
        os.makedirs(sub_baseline_dir, exist_ok=True)

        # Process files
        for fname in filenames:
            src = os.path.join(abs_dirpath, fname)
            # Skip if it's not a regular file
            if not os.path.isfile(src):
                continue

            dst = os.path.join(sub_baseline_dir, fname)
            try:
                size = os.path.getsize(src)
                if size > SIZE_THRESHOLD:
                    # Large file => store .hash
                    file_hash = calculate_sha256(src)
                    with open(dst + '.hash', 'w') as hf:
                        hf.write(f"HASH: {file_hash}\nSIZE: {size}\n")
                else:
                    # Small file => copy fully
                    shutil.copy2(src, dst)
            except Exception as e:
                print(f"Error processing {src}: {e}")

    # Now tar the baseline directory
    print(f"Creating tar archive {baseline_tar}...")
    try:
        with tarfile.open(baseline_tar, "w:gz") as tar:
            # arcname sets how it appears inside the tar
            tar.add(baseline_dir, arcname=os.path.basename(baseline_dir))
    except Exception as e:
        print(f"Error creating tar archive: {e}")
        return

    # Remove the baseline directory
    print(f"Removing uncompressed baseline directory {baseline_dir}...")
    try:
        shutil.rmtree(baseline_dir)
    except Exception as e:
        print(f"Error removing baseline directory: {e}")

    print(f"Baseline complete. Tar saved to {baseline_tar}.")

if __name__ == '__main__':
    mode1()
