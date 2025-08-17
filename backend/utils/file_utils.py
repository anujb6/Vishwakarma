import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False

def cleanup_directory(path: str) -> bool:
    """Remove directory and all contents"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.info(f"Cleaned up directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up directory {path}: {e}")
        return False

def copy_directory(source: str, destination: str) -> bool:
    """Copy directory recursively"""
    try:
        if os.path.exists(destination):
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        return True
    except Exception as e:
        logger.error(f"Error copying directory {source} to {destination}: {e}")
        return False

def get_directory_size(path: str) -> int:
    """Get total size of directory in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
    except Exception as e:
        logger.error(f"Error calculating directory size: {e}")
    return total_size

def get_files_in_directory(path: str, extensions: Optional[List[str]] = None) -> List[str]:
    """Get list of files in directory, optionally filtered by extension"""
    files = []
    try:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                if extensions:
                    if any(filename.lower().endswith(ext.lower()) for ext in extensions):
                        files.append(os.path.join(root, filename))
                else:
                    files.append(os.path.join(root, filename))
    except Exception as e:
        logger.error(f"Error getting files in directory: {e}")
    return files