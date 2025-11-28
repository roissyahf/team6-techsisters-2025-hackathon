"""
Path helper utilities for building absolute paths.
"""
from pathlib import Path


def get_absolute_path(*path_components: str) -> Path:
    """
    Build an absolute path from path components.
    
    This function finds the base directory (parent of MODEL_API_nontechnical_questions)
    and joins the provided path components to create an absolute path.
    
    The function searches for the project directory by looking for app.py or
    the MODEL_API_nontechnical_questions directory name, then uses its parent
    as the base directory.
    
    Args:
        *path_components: Variable number of path component strings
        
    Returns:
        Path: Absolute path object
        
    Example:
        get_absolute_path("MODEL_API_nontechnical_questions", "static_data", "roles_upd.json")
        # Returns: /path/to/parent/MODEL_API_nontechnical_questions/static_data/roles_upd.json
    """
    # Start from the utils directory (where this file is)
    current = Path(__file__).resolve().parent
    
    # Find the project root (MODEL_API_nontechnical_questions directory)
    # by searching up the directory tree
    project_root = None
    search_path = current
    
    # Search up to 5 levels to find the project root
    for _ in range(5):
        # Check if this directory contains app.py (project root)
        if (search_path / "app.py").exists():
            project_root = search_path
            break
        # Check if this directory is named MODEL_API_nontechnical_questions
        if search_path.name == "MODEL_API_nontechnical_questions":
            project_root = search_path
            break
        # Stop if we've reached the filesystem root
        if search_path.parent == search_path:
            break
        search_path = search_path.parent
    
    # If we found the project root, use its parent as the base
    # (since get_absolute_path calls include "MODEL_API_nontechnical_questions" as first component)
    if project_root is not None:
        base_dir = project_root.parent
    else:
        # Fallback: assume we're in the project and go up one level
        base_dir = current.parent.parent
    
    # Build the path by joining all components
    result_path = base_dir
    for component in path_components:
        result_path = result_path / component
    
    return result_path.resolve()

