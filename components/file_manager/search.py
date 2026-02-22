import os
import subprocess
import threading
import platform
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ──────────────────────────────────────────────────────────────────────────────
# Directories to completely skip during scanning
# ──────────────────────────────────────────────────────────────────────────────

IGNORED_DIRS_WIN = {
    'Windows', 'ProgramData', 'Program Files', 'Program Files (x86)',
    'WindowsApps', '$Recycle.Bin', 'System Volume Information',
    'Intel', 'PerfLogs', 'Recovery', 'Boot',
    'node_modules', '__pycache__', '.git',
}

IGNORED_APPDATA_SUBDIRS = {'Local', 'LocalLow'}

IGNORED_DIRS_LINUX = {
    'proc', 'sys', 'dev', 'run', 'tmp', 'snap',
    'lost+found', 'boot',
}

# Additional heavy directories to prune on Linux for speed
_LINUX_EXTRA_PRUNE = [
    '*/node_modules', '*/__pycache__', '*/.git',
    '*/.cache', '*/.local/share/Trash',
]


# ──────────────────────────────────────────────────────────────────────────────
# Cross-platform partition helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_partitions():
    partitions = []
    if HAS_PSUTIL:
        seen_mounts = set()
        for p in psutil.disk_partitions(all=False):
            mp = p.mountpoint
            if not mp or mp in seen_mounts: continue
            if platform.system() == 'Linux' and p.fstype in (
                'proc', 'sysfs', 'devtmpfs', 'devpts', 'tmpfs', 'cgroup', 'cgroup2'
            ): continue
            seen_mounts.add(mp)
            partitions.append((mp, mp))
    else:
        if os.name == 'nt':
            import string
            for letter in string.ascii_uppercase:
                mp = f"{letter}:\\"
                if os.path.exists(mp): partitions.append((mp, mp))
        else:
            user_home = str(Path.home())
            for mp in [user_home, '/media', '/mnt', '/']:
                if os.path.exists(mp): partitions.append((mp, mp))

    if os.name == 'nt':
        user_profile = os.environ.get('USERPROFILE', '')
        exists = {mp for mp, _ in partitions}
        priority = []
        for sub in ('Desktop', 'Documents', 'Downloads', 'OneDrive'):
            p = os.path.join(user_profile, sub)
            if os.path.exists(p) and p not in exists:
                priority.append((p, sub))
        partitions = priority + partitions
    return partitions


# Global tracking for concurrent searches and cancellation
CANCEL_FLAGS = {}
ACTIVE_SEARCHES = set()

# ──────────────────────────────────────────────────────────────────────────────
# Per-partition search workers
# ──────────────────────────────────────────────────────────────────────────────

def _is_word_match(query_lower, name_lower):
    stem = name_lower.split('.')[0] if '.' in name_lower else name_lower
    if stem == query_lower or name_lower == query_lower: return True
    tokens = re.split(r'[\s\-_.,()[\]{}]+', stem)
    return query_lower in tokens


def _search_partition_windows(root_path, label, query, results_lock, all_results, status_queue=None):
    query_lower = query.lower()
    try:
        for root, dirs, files in os.walk(root_path):
            if CANCEL_FLAGS.get(query, False): return # Early exit check

            pruned = []
            for d in dirs:
                if d in IGNORED_DIRS_WIN or d.startswith('.'): continue
                if 'AppData' in root and d in IGNORED_APPDATA_SUBDIRS: continue
                pruned.append(d)
            dirs[:] = pruned

            for d in dirs:
                if CANCEL_FLAGS.get(query, False): return # Early exit check
                if _is_word_match(query_lower, d.lower()):
                    full_path = os.path.join(root, d)
                    with results_lock:
                        all_results.append({'path': full_path, 'type': 'dir', 'exact': d.lower() == query_lower, 'label': label})
                        count = len(all_results)
                    if status_queue:
                        status_queue.put(("SEARCH_COUNT", (query, count)))
            for f in files:
                if CANCEL_FLAGS.get(query, False): return # Early exit check
                if _is_word_match(query_lower, f.lower()):
                    full_path = os.path.join(root, f)
                    with results_lock:
                        all_results.append({'path': full_path, 'type': 'file', 'exact': os.path.splitext(f)[0].lower() == query_lower, 'label': label})
                        count = len(all_results)
                    if status_queue:
                        status_queue.put(("SEARCH_COUNT", (query, count)))
    except Exception: pass


def _search_partition_linux(root_path, label, query, results_lock, all_results, status_queue=None, exclude_paths=None):
    """
    Optimized Linux search:
    1. Try 'locate' (plocate/mlocate) for instant indexed results
    2. Fall back to a SINGLE 'find' traversal with all patterns combined via -o
       (original code ran 11 separate find commands, each traversing the full tree)
    """
    seen_locally = set()
    query_lower = query.lower()

    def _add_result(path, exact=False):
        """Thread-safe result addition with deduplication."""
        if not path or path in seen_locally:
            return
        seen_locally.add(path)
        with results_lock:
            all_results.append({
                'path': path,
                'type': 'dir' if os.path.isdir(path) else 'file',
                'exact': exact,
                'label': label
            })
            count = len(all_results)
        if status_queue:
            status_queue.put(("SEARCH_COUNT", (query, count)))

    # ── Build prune arguments once (reused by find) ──
    all_excludes = list(exclude_paths or [])
    # Add standard Linux system dirs to prune
    for d in IGNORED_DIRS_LINUX:
        all_excludes.append(os.path.join(root_path, d))
    # Add heavy dev/cache directories
    all_excludes.extend(_LINUX_EXTRA_PRUNE)

    prune_args = []
    if all_excludes:
        prune_args = ['(']
        for i, ex in enumerate(all_excludes):
            prune_args += ['-path', ex, '-prune']
            if i < len(all_excludes) - 1:
                prune_args.append('-o')
        prune_args += [')', '-o']

    # ── Fast Path: Try 'locate' (plocate/mlocate) for instant indexed results ──
    locate_cmd = shutil.which('plocate') or shutil.which('locate')
    if locate_cmd:
        try:
            proc = subprocess.Popen(
                [locate_cmd, '-i', '-l', '500', query],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
            )
            for line in proc.stdout:
                if CANCEL_FLAGS.get(query, False):
                    proc.terminate()
                    return
                path = line.strip()
                if path and path.startswith(root_path):
                    name_lower = os.path.basename(path).lower()
                    stem = os.path.splitext(name_lower)[0]
                    exact = (stem == query_lower or name_lower == query_lower)
                    _add_result(path, exact=exact)
            proc.wait()
            if seen_locally:
                return  # locate found results, skip the slower find
        except Exception:
            pass

    # ── Fallback: Single-pass find with ALL patterns combined ──
    # Original code ran 11 separate find commands (each traversing the full tree).
    # This combines everything into ONE traversal using -o (OR).
    separators = ['-', '_', ' ']

    cmd = ['find', root_path]
    cmd += prune_args
    cmd.append('(')

    # Pattern 1: exact name (case-sensitive)
    cmd += ['-name', query]

    # Pattern 2: extension match (e.g. query.txt, query.pdf)
    cmd += ['-o', '-iname', f'{query}.*']

    # Patterns 3-11: separator variations
    for sep in separators:
        cmd += ['-o', '-iname', f'*{sep}{query}{sep}*']
        cmd += ['-o', '-iname', f'{query}{sep}*']
        cmd += ['-o', '-iname', f'*{sep}{query}']

    cmd += [')', '-print']

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        for line in proc.stdout:
            if CANCEL_FLAGS.get(query, False):
                proc.terminate()
                return
            path = line.strip()
            if path:
                name_lower = os.path.basename(path).lower()
                stem = os.path.splitext(name_lower)[0]
                exact = (stem == query_lower or name_lower == query_lower)
                _add_result(path, exact=exact)
        proc.wait()
    except Exception:
        pass


# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

def background_search(query, speaker, status_queue=None):
    """
    Parallel file search across all detected partitions.
    
    If results are found:
    - They are sent to the UI process to be displayed in a unified Results Viewer.
    
    If no results are found:
    - It signals the UI process to open a fallback search box.
    """
    if speaker:
        threading.Thread(target=speaker.speak, args=(f"Searching for {query}...",), daemon=True).start()

    partitions = _get_partitions()
    if not partitions:
        if speaker: 
            threading.Thread(target=speaker.speak, args=("No drives found to search.",), daemon=True).start()
        return

    # Register active search
    ACTIVE_SEARCHES.add(query)
    CANCEL_FLAGS[query] = False

    results_lock = threading.Lock()
    all_results = []
    is_windows = os.name == 'nt'
    linux_priority_paths = [mp for mp, _ in partitions if mp != '/'] if not is_windows else []

    with ThreadPoolExecutor(max_workers=min(len(partitions), 8)) as executor:
        futures = []
        for mp, label in partitions:
            if is_windows:
                futures.append(executor.submit(_search_partition_windows, mp, label, query, results_lock, all_results, status_queue))
            else:
                futures.append(executor.submit(_search_partition_linux, mp, label, query, results_lock, all_results, status_queue, linux_priority_paths if mp == '/' else None))
        for f in as_completed(futures): pass

    # Cleanup flags
    was_canceled = CANCEL_FLAGS.get(query, False)
    ACTIVE_SEARCHES.discard(query)
    if query in CANCEL_FLAGS:
        del CANCEL_FLAGS[query]

    if not all_results:
        if not was_canceled:
            if speaker:
                msg = f"I couldn't find {query}. Opening a search box so you can type it."
                threading.Thread(target=speaker.speak, args=(msg,), daemon=True).start()
            
            # Cross-process signal: Tell UI process to show the search dialog
            if status_queue:
                status_queue.put(("FILE_SEARCH_GUI", query))
        else:
            if speaker:
                threading.Thread(target=speaker.speak, args=(f"Search for {query} canceled.",), daemon=True).start()
        return

    # Process results: Sort and Deduplicate
    all_results.sort(key=lambda r: (not r['exact'], r['path'].lower()))
    seen, unique_results = set(), []
    for r in all_results:
        if r['path'] not in seen:
            seen.add(r['path'])
            unique_results.append(r)

    # ── [NEW] Send results to UI process instead of auto-opening ──
    if status_queue:
        # We send both the query and the list of results
        status_queue.put(("FILE_SEARCH_RESULTS", (query, unique_results)))

    if speaker:
        exact_count = sum(1 for r in unique_results if r['exact'])
        total = len(unique_results)
        
        if was_canceled:
            msg = f"Search canceled. Showing {total} results found so far for {query}."
        elif exact_count > 0:
            msg = f"Found {exact_count} exact match{'es' if exact_count > 1 else ''} for {query}. Displaying them now."
        else:
            msg = f"No exact match for {query}. Found {total} related result{'s' if total > 1 else ''}. Displaying them now."
            
        # Do not block the search thread waiting for TTS to finish speaking
        threading.Thread(target=speaker.speak, args=(msg,), daemon=True).start()
