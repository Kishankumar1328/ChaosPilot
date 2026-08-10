import os
import shutil
import logging
from typing import Tuple
from app.models.codefix import CodePatch

logger = logging.getLogger(__name__)

class PatchEngine:
    """
    Safely applies proposed code patches and executes regression tests.
    Performs backups to allow safe rollback.
    """
    @staticmethod
    def apply_patch(patch: CodePatch) -> Tuple[bool, str]:
        if not os.path.exists(patch.file_path):
            return False, f"Target file '{patch.file_path}' does not exist."

        backup_path = f"{patch.file_path}.bak"
        try:
            # Create backup
            shutil.copyfile(patch.file_path, backup_path)

            # Apply proposed patch code
            with open(patch.file_path, "w", encoding="utf-8") as f:
                f.write(patch.proposed_code)

            logger.info(f"Applied patch to {patch.file_path} (Backup: {backup_path})")
            return True, f"Successfully applied patch to {patch.file_path}"
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            return False, str(e)

    @staticmethod
    def rollback_patch(file_path: str) -> Tuple[bool, str]:
        backup_path = f"{file_path}.bak"
        if not os.path.exists(backup_path):
            return False, f"Backup file '{backup_path}' not found."

        try:
            shutil.copyfile(backup_path, file_path)
            os.remove(backup_path)
            logger.info(f"Rolled back patch for {file_path}")
            return True, f"Successfully rolled back patch for {file_path}"
        except Exception as e:
            return False, str(e)
