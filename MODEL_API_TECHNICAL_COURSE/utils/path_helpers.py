from pathlib import Path
from typing import Union

def get_project_root() -> Path:
    """
    Finds the absolute path to the project's root directory.
    
    It searches upwards from the current file (__file__) until it finds 
    a known root-level marker (like a .git folder or requirements.txt).
    For simplicity, look for 'README.md' or stop after 7 levels up.
    """
    # Start the search from the directory of this file
    current_dir = Path(__file__).resolve().parent
    
    # Define a marker file/directory that must exist in the root
    ROOT_MARKERS = ['.git', 'README.md', 'requirements.txt'] 
    
    # Search upwards for the root, max 7 levels
    for parent in [current_dir] + list(current_dir.parents)[:7]:
        if any((parent / marker).exists() for marker in ROOT_MARKERS):
            return parent
            
    # Fallback: return the directory containing this file
    return Path(__file__).resolve().parent.parent

# Cache the project root path for efficiency after the first call
_PROJECT_ROOT = get_project_root()


def get_absolute_path(*relative_path_parts: Union[str, Path]) -> Path:
    """
    Constructs an absolute path by joining the project root with the 
    provided relative path parts.

    Args:
        relative_path_parts: A sequence of directory names and the final 
                             filename, relative to the project root.

    Returns:
        A pathlib.Path object representing the absolute file path.
    """
    # Use the / operator for clean, OS-independent path joining
    return _PROJECT_ROOT.joinpath(*relative_path_parts)

