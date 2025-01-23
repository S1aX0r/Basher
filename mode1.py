import os
import shutil
import hashlib

SIZE_THRESHOLD = 1 * 1024 * 1024

def calculate_sha256(file_path, chunk_size=65536):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def mode1(root_dir='/', baseline_dir='./baseline'):
    # Convert baseline_dir to an absolute path
    baseline_dir = os.path.abspath(baseline_dir)

    # Directories to skip (common system dirs plus the baseline folder)
    skip_dirs = {
        '/proc',
        '/sys',
        '/dev',
        '/run',
        '/tmp',
        '/var/run',
        baseline_dir,  # <-- Skip the baseline folder
    }

    os.makedirs(baseline_dir, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        # Convert the current path to absolute
        abs_dirpath = os.path.abspath(dirpath)
        
        # Check if current dir should be skipped
        if any(abs_dirpath.startswith(sd) for sd in skip_dirs):
            dirnames[:] = []  # Clear subdirs so we don't walk further
            filenames[:] = []
            continue

        # Figure out the corresponding path inside baseline_dir
        relative_path = os.path.relpath(abs_dirpath, start=root_dir)
        if relative_path == '.':
            relative_path = ''

        sub_baseline_dir = os.path.join(baseline_dir, relative_path)
        
        # Make sure the subdir exists
        os.makedirs(sub_baseline_dir, exist_ok=True)

        for filename in filenames:
            source_file = os.path.join(abs_dirpath, filename)
            
            # Only handle real files (skip sockets, etc.)
            if not os.path.isfile(source_file):
                continue

            baseline_file = os.path.join(sub_baseline_dir, filename)

            try:
                size = os.path.getsize(source_file)
                if size > SIZE_THRESHOLD:
                    file_hash = calculate_sha256(source_file)
                    with open(baseline_file + '.hash', 'w') as hf:
                        hf.write(f"HASH: {file_hash}\nSIZE: {size}\n")
                else:
                    shutil.copy2(source_file, baseline_file)
            except Exception as e:
                print(f"Error processing {source_file}: {e}")

if __name__ == "__main__":
    mode1(root_dir='/', baseline_dir='./baseline')
