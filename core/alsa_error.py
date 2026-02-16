import os
import sys
import platform
from contextlib import contextmanager

@contextmanager
def no_alsa_error():
    """
    Cross-platform context manager to suppress audio library errors.
    
    On Linux: Suppresses stdout/stderr from C libraries (ALSA, JACK, etc.)
    by redirecting file descriptors to /dev/null.
    
    On Windows/macOS: Acts as a no-op since these systems don't use ALSA.
    """
    # Only suppress errors on Linux systems
    if platform.system() != 'Linux':
        # No-op for Windows and macOS
        yield
        return
    
    # Linux-specific ALSA error suppression
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
    except (FileNotFoundError, OSError):
        # If we can't open /dev/null, just continue without suppression
        yield
        return

    # Save original file descriptors
    original_stderr = os.dup(2)
    
    try:
        # Flush python buffers to ensure order
        sys.stderr.flush()
        
        # Redirect stderr to /dev/null
        os.dup2(devnull, 2)
        
        yield
        
    finally:
        # Restore stderr
        os.dup2(original_stderr, 2)
        os.close(original_stderr)
        os.close(devnull)
