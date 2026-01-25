import os
import sys
from contextlib import contextmanager

@contextmanager
def no_alsa_error():
    """
    Aggressively suppresses stdout/stderr from C libraries (ALSA, JACK, etc.)
    by redirecting file descriptors to /dev/null.
    """
    # Open /dev/null
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
    except FileNotFoundError:
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
