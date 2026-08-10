import os
import glob
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CodeInspector:
    """
    Scans a local target repository to locate source files matching route paths
    or error log keywords for root cause analysis.
    """
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    def find_relevant_files(self, keywords: List[str]) -> List[str]:
        if not os.path.exists(self.repo_dir):
            return []

        matched_files = set()
        search_extensions = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.html"]

        for ext in search_extensions:
            for filepath in glob.glob(os.path.join(self.repo_dir, "**", ext), recursive=True):
                if ".venv" in filepath or "node_modules" in filepath or ".git" in filepath:
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for kw in keywords:
                            if kw and kw.lower() in content.lower():
                                matched_files.add(filepath)
                                break
                except Exception as e:
                    logger.debug(f"Error reading file {filepath}: {e}")

        return list(matched_files)

    def read_file_snippet(self, filepath: str, max_lines: int = 150) -> str:
        if not os.path.exists(filepath):
            return ""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                return "".join(lines[:max_lines])
        except Exception as e:
            logger.error(f"Error reading snippet for {filepath}: {e}")
            return ""
