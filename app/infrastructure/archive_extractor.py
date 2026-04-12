"""
Сервис для извлечения архивов (RAR/ZIP)
"""

import logging
import zipfile
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# Попытка импортировать rarfile
try:
    import rarfile

    RAR_SUPPORT = True
except ImportError:
    RAR_SUPPORT = False
    logger.warning("rarfile не установлен. Поддержка RAR отключена.")


class ArchiveExtractor:
    """Сервис для извлечения архивов"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def extract(self, archive_path: str) -> List[str]:
        """
        Извлечение архива

        Args:
            archive_path: Путь к архиву

        Returns:
            List[str]: Список извлеченных файлов
        """
        archive_path = Path(archive_path)

        if not archive_path.exists():
            raise FileNotFoundError(f"Архив не найден: {archive_path}")

        if archive_path.suffix.lower() == ".zip":
            return self._extract_zip(archive_path)
        if archive_path.suffix.lower() == ".rar":
            return self._extract_rar(archive_path)
        else:
            raise ValueError(f"Неподдерживаемый формат: {archive_path.suffix}")

    def _extract_zip(self, zip_path: Path) -> List[str]:
        """Извлечение ZIP архива"""
        extracted_files = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            extract_to = self.output_dir / zip_path.stem
            extract_to.mkdir(exist_ok=True, parents=True)
            zip_ref.extractall(extract_to)

            for file in extract_to.rglob("*"):
                if file.is_file():
                    extracted_files.append(str(file))

        logger.info(f"Извлечено {len(extracted_files)} файлов из {zip_path.name}")
        return extracted_files

    def _extract_rar(self, rar_path: Path) -> List[str]:
        """Извлечение RAR архива"""
        if not RAR_SUPPORT:
            raise RuntimeError(
                "Поддержка RAR не доступна. Установите: pip install rarfile"
            )

        extracted_files = []

        with rarfile.RarFile(rar_path, "r") as rar_ref:
            extract_to = self.output_dir / rar_path.stem
            extract_to.mkdir(exist_ok=True, parents=True)
            rar_ref.extractall(extract_to)

            for file in extract_to.rglob("*"):
                if file.is_file():
                    extracted_files.append(str(file))

        logger.info(f"Извлечено {len(extracted_files)} файлов из {rar_path.name}")
        return extracted_files

    def detect_classes(self, extracted_files: List[str]) -> Dict[str, List[str]]:
        """
        Определение классов по структуре папок

        Returns:
            Dict: {class_name: [image_paths]}
        """
        class_folders = {"pered": [], "zad": [], "none": []}

        class_patterns = {
            "pered": ["pered", "prered", "front", "перед"],
            "zad": ["zad", "back", "rear", "зад"],
            "none": ["none", "empty", "нет", "пусто"],
        }

        image_extensions = {".jpg", ".jpeg", ".png"}

        for file_path in extracted_files:
            file_path = Path(file_path)

            if file_path.suffix.lower() not in image_extensions:
                continue

            parent_folder = file_path.parent.name.lower()

            for class_name, patterns in class_patterns.items():
                if any(pattern in parent_folder for pattern in patterns):
                    class_folders[class_name].append(str(file_path))
                    break

        return class_folders
