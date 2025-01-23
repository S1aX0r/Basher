import os
import hashlib

SIZE_THRESHOLD = 1 * 1024 * 1024  # 1 MB

def calculate_sha256(file_path, chunk_size=65536):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_baseline(baseline_dir):
    """
    Read the baseline directory and build a dictionary describing which files
    existed at baseline time. For large files, we only have .hash files.
    For small files, we have the real copies.
    """
    baseline_info = {}

    # Walk the baseline directory, but skip too-long path errors
    for dirpath, dirnames, filenames in os.walk(baseline_dir, followlinks=False):
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)

            # If the path is extremely long, skip it
            if len(full_path) > 255:
                continue

            # Catch OSError for "File name too long"
            try:
                # .hash means it's large
                if fname.endswith(".hash"):
                    # The actual file name is fname without the ".hash"
                    base_name = fname[:-5]  # remove .hash
                    # Relative path inside baseline
                    rel_dir = os.path.relpath(dirpath, baseline_dir)
                    if rel_dir == '.':
                        rel_dir = ''
                    rel_file = os.path.join(rel_dir, base_name)

                    # Parse stored HASH and SIZE
                    file_hash = None
                    file_size = None
                    with open(full_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("HASH: "):
                                file_hash = line.split("HASH: ", 1)[1]
                            elif line.startswith("SIZE: "):
                                file_size = int(line.split("SIZE: ", 1)[1])

                    baseline_info[rel_file] = {
                        "is_large": True,
                        "hash": file_hash,
                        "size": file_size,
                    }

                else:
                    # It's presumably a small file
                    file_size = os.path.getsize(full_path)
                    rel_dir = os.path.relpath(dirpath, baseline_dir)
                    if rel_dir == '.':
                        rel_dir = ''
                    rel_file = os.path.join(rel_dir, fname)

                    baseline_info[rel_file] = {
                        "is_large": False,
                        "hash": None,
                        "size": file_size,
                    }

            except OSError as e:
                # Skip if it's a "File name too long" error
                if e.errno == 36:
                    print(f"Skipping too-long file: {full_path}")
                    continue
                else:
                    raise  # Some other error we didn't expect

    return baseline_info

def compare_small_files(current_file, baseline_file):
    """
    Compare two small files by hashing (or a direct byte compare).
    Return True if identical, False otherwise.
    """
    # We'll just do a hash compare for simplicity
    try:
        return calculate_sha256(current_file) == calculate_sha256(baseline_file)
    except OSError as e:
        if e.errno == 36:
            print(f"Skipping compare on too-long file: {current_file}")
            return False
        else:
            raise

def mode2(root_dir='/', baseline_dir='./baseline'):
    """
    Compare the current filesystem to the baseline in `baseline_dir`.
    - If the baseline has .hash, it was a large file. Compare current SHA256 to stored.
    - If the baseline has an actual file, compare the contents (small file).
    - Print out NEW, MODIFIED, REMOVED, or UNCHANGED.
    - Skip paths that are too long.
    - Skip recursing into the baseline directory if it's under root_dir.
    """
    baseline_dir = os.path.abspath(baseline_dir)
    root_dir = os.path.abspath(root_dir)

    # 1) Load the baseline
    baseline_info = load_baseline(baseline_dir)

    # We'll track which baseline files we see in the current filesystem
    seen_baseline_paths = set()

    # Directories to skip
    skip_dirs = {
        '/proc',
        '/sys',
        '/dev',
        '/run',
        '/tmp',
        '/var/run',
        baseline_dir,  # explicitly skip going *into* the baseline again
    }

    # 2) Walk the current filesystem
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        abs_dirpath = os.path.abspath(dirpath)

        # If path is in skip_dirs or starts with them, skip
        if any(abs_dirpath.startswith(sd) for sd in skip_dirs):
            dirnames[:] = []  # clear so we don't recurse
            filenames[:] = []
            continue

        # If path is extremely long, skip descending
        if len(abs_dirpath) > 255:
            dirnames[:] = []
            filenames[:] = []
            continue

        # Compute relative path from root_dir
        rel_dir = os.path.relpath(abs_dirpath, root_dir)
        if rel_dir == '.':
            rel_dir = ''

        for fname in filenames:
            current_file = os.path.join(abs_dirpath, fname)
            if len(current_file) > 255:
                # skip too-long path
                continue

            # skip non-regular files (symlinks, sockets, etc.)
            if not os.path.isfile(current_file):
                continue

            # Relative path to look up in baseline
            rel_file_path = os.path.join(rel_dir, fname)
            seen_baseline_paths.add(rel_file_path)

            if rel_file_path not in baseline_info:
                # Not in baseline => NEW
                print(f"NEW: {current_file}")
            else:
                # Compare
                info = baseline_info[rel_file_path]
                if info["is_large"]:
                    # We have a stored hash. Compare it.
                    try:
                        current_hash = calculate_sha256(current_file)
                    except OSError as e:
                        if e.errno == 36:
                            print(f"Skipping too-long file: {current_file}")
                            continue
                        else:
                            raise
                    if current_hash == info["hash"]:
                        print(f"UNCHANGED: {current_file}")
                    else:
                        print(f"MODIFIED: {current_file}")
                else:
                    # It's a small file in baseline; let's compare the actual file copy
                    baseline_copy = os.path.join(baseline_dir, rel_file_path)
                    if not os.path.isfile(baseline_copy):
                        print(f"MODIFIED (missing baseline copy): {current_file}")
                    else:
                        same = compare_small_files(current_file, baseline_copy)
                        if same:
                            print(f"UNCHANGED: {current_file}")
                        else:
                            print(f"MODIFIED: {current_file}")

    # 3) Anything in baseline not in current => REMOVED
    for rel_file_path in baseline_info:
        if rel_file_path not in seen_baseline_paths:
            # It's no longer on disk => REMOVED
            baseline_full = os.path.join(baseline_dir, rel_file_path)
            # If it was a large file, baseline_full might not exist; it might be baseline_full+'.hash'
            print(f"REMOVED: {baseline_full}")

if __name__ == "__main__":
    mode2(root_dir='/', baseline_dir='./baseline')
