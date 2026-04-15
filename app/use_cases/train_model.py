# """
# Use Case: Обучение модели
# Содержит бизнес-логику обучения EfficientNet-B2
# """

# import logging
# import os
# from typing import Optional, Tuple

# import torch
# from torch import nn, optim
# from torch.utils.data import DataLoader
# from torchvision import transforms
# from tqdm import tqdm
# from app.domain.exceptions import DataPreparationException
# from app.infrastructure.model_repository import RobustWagonDataset, create_model

# logger = logging.getLogger(__name__)


# class TrainModelUseCase:
#     """Use case для обучения модели"""

#     def __init__(self, data_dir: str, model_save_path: str, class_names: list):
#         self.data_dir = data_dir
#         self.model_save_path = model_save_path
#         self.class_names = class_names
#         self.num_classes = len(class_names)

#     def _get_transforms(self) -> Tuple[transforms.Compose, transforms.Compose]:
#         """Получение трансформаций для обучения и валидации"""
#         train_transform = transforms.Compose(
#             [
#                 transforms.Resize((256, 256)),
#                 transforms.RandomCrop(224),
#                 transforms.RandomHorizontalFlip(p=0.5),
#                 transforms.ColorJitter(brightness=0.2, contrast=0.2),
#                 transforms.ToTensor(),
#                 transforms.Normalize(
#                     mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
#                 ),
#             ]
#         )

#         val_transform = transforms.Compose(
#             [
#                 transforms.Resize((224, 224)),
#                 transforms.ToTensor(),
#                 transforms.Normalize(
#                     mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
#                 ),
#             ]
#         )

#         return train_transform, val_transform

#     def execute(self, config: Optional[TrainingConfig] = None) -> TrainingHistory:
#         """Запуск обучения модели"""
#         if config is None:
#             config = TrainingConfig()

#         device = config.device or ("cuda" if torch.cuda.is_available() else "cpu")
#         logger.info(f"Начало обучения на устройстве: {device}")
#         logger.info(f"Batch size: {config.batch_size}, Эпох: {config.num_epochs}")

#         if torch.cuda.is_available():
#             torch.cuda.empty_cache()

#         if not os.path.exists(self.data_dir):
#             raise DataPreparationException(f"Данные не найдены: {self.data_dir}")

#         train_transform, val_transform = self._get_transforms()

#         train_dataset = RobustWagonDataset(
#             self.data_dir, self.class_names, transform=train_transform, mode="train"
#         )

#         val_dataset = RobustWagonDataset(
#             self.data_dir, self.class_names, transform=val_transform, mode="val"
#         )

#         if len(train_dataset) == 0:
#             raise DataPreparationException("Обучающие данные не найдены!")

#         train_loader = DataLoader(
#             train_dataset,
#             batch_size=config.batch_size,
#             shuffle=True,
#             num_workers=0,
#             pin_memory=torch.cuda.is_available(),
#         )

#         val_loader = DataLoader(
#             val_dataset,
#             batch_size=config.batch_size,
#             shuffle=False,
#             num_workers=0,
#             pin_memory=torch.cuda.is_available(),
#         )

#         model = create_model(self.num_classes).to(device)

#         criterion = nn.CrossEntropyLoss()
#         optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
#         scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

#         history = TrainingHistory()

#         logger.info("=" * 50)
#         logger.info("НАЧАЛО ОБУЧЕНИЯ")
#         logger.info("=" * 50)

#         for epoch in range(config.num_epochs):
#             logger.info(f"\nЭпоха {epoch + 1}/{config.num_epochs}")

#             train_loss, train_acc = self._train_epoch(
#                 model, train_loader, criterion, optimizer, device
#             )

#             val_loss, val_acc = self._validate_epoch(
#                 model, val_loader, criterion, device
#             )

#             scheduler.step()

#             history.train_loss.append(train_loss)
#             history.train_acc.append(train_acc)
#             history.val_loss.append(val_loss)
#             history.val_acc.append(val_acc)

#             if val_acc > history.best_val_acc:
#                 history.best_val_acc = val_acc
#                 self._save_model(model, optimizer, epoch, val_acc, train_acc)
#                 logger.info(f"Сохранена лучшая модель! Точность: {val_acc:.4f}")

#             logger.info(f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f}")
#             logger.info(f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

#         logger.info("=" * 50)
#         logger.info(f"Обучение завершено! Лучшая точность: {history.best_val_acc:.4f}")
#         logger.info(f"Модель сохранена: {self.model_save_path}")

#         return history

#     def _train_epoch(
#         self, model, loader, criterion, optimizer, device
#     ) -> Tuple[float, float]:
#         """Обучение одной эпохи"""
#         model.train()
#         total_loss = 0.0
#         correct = 0
#         total = 0

#         train_bar = tqdm(loader, desc="Training")
#         for images, labels in train_bar:
#             images = images.to(device)
#             labels = labels.to(device)

#             optimizer.zero_grad()
#             outputs = model(images)
#             loss = criterion(outputs, labels)
#             loss.backward()
#             optimizer.step()

#             total_loss += loss.item()
#             _, predicted = outputs.max(1)
#             total += labels.size(0)
#             correct += predicted.eq(labels).sum().item()

#             train_bar.set_postfix(
#                 {"Loss": f"{loss.item():.4f}", "Acc": f"{100. * correct / total:.1f}%"}
#             )

#         avg_loss = total_loss / len(loader)
#         accuracy = correct / total

#         return avg_loss, accuracy

#     def _validate_epoch(self, model, loader, criterion, device) -> Tuple[float, float]:
#         """Валидация одной эпохи"""
#         model.eval()
#         total_loss = 0.0
#         correct = 0
#         total = 0

#         with torch.no_grad():
#             val_bar = tqdm(loader, desc="Validation")
#             for images, labels in val_bar:
#                 images = images.to(device)
#                 labels = labels.to(device)

#                 outputs = model(images)
#                 loss = criterion(outputs, labels)

#                 total_loss += loss.item()
#                 _, predicted = outputs.max(1)
#                 total += labels.size(0)
#                 correct += predicted.eq(labels).sum().item()

#         avg_loss = total_loss / len(loader)
#         accuracy = correct / total

#         return avg_loss, accuracy

#     def _save_model(self, model, optimizer, epoch, val_acc, train_acc):
#         """Сохранение модели"""
#         os.makedirs(os.path.dirname(self.model_save_path), exist_ok=True)

#         torch.save(
#             {
#                 "epoch": epoch,
#                 "model_state_dict": model.state_dict(),
#                 "optimizer_state_dict": optimizer.state_dict(),
#                 "val_acc": val_acc,
#                 "train_acc": train_acc,
#                 "class_names": self.class_names,
#             },
#             self.model_save_path,
#         )


"""
Use Case: Обучение модели
Содержит бизнес-логику обучения EfficientNet-B2
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import transforms
from tqdm import tqdm

from app.domain.exceptions import DataPreparationException

logger = logging.getLogger(__name__)


# ================================================
# КЛАССЫ ДЛЯ КОНФИГУРАЦИИ И ИСТОРИИ
# ================================================


@dataclass
class TrainingConfig:
    """Конфигурация обучения"""

    batch_size: int = 32
    num_epochs: int = 15
    learning_rate: float = 1e-4
    device: Optional[str] = None
    val_split: float = 0.2
    random_seed: int = 42


@dataclass
class TrainingHistory:
    """История обучения"""

    train_loss: List[float] = field(default_factory=list)
    train_acc: List[float] = field(default_factory=list)
    val_loss: List[float] = field(default_factory=list)
    val_acc: List[float] = field(default_factory=list)
    best_val_acc: float = 0.0
    best_epoch: int = -1

    def add_epoch(
        self,
        train_loss: float,
        train_acc: float,
        val_loss: float,
        val_acc: float,
        epoch: int,
    ):
        """Добавление данных эпохи"""
        self.train_loss.append(train_loss)
        self.train_acc.append(train_acc)
        self.val_loss.append(val_loss)
        self.val_acc.append(val_acc)

        if val_acc > self.best_val_acc:
            self.best_val_acc = val_acc
            self.best_epoch = epoch


# ================================================
# ДАТАСЕТ (безопасная загрузка изображений)
# ================================================


def load_image_safe(image_path, target_size=(224, 224)):
    """Безопасная загрузка изображения с обработкой ошибок"""
    from PIL import Image, ImageFile

    ImageFile.LOAD_TRUNCATED_IMAGES = True

    try:
        image = Image.open(image_path)
        image.verify()
        image = Image.open(image_path)

        if image.mode != "RGB":
            image = image.convert("RGB")

        if image.size[0] == 0 or image.size[1] == 0:
            image = Image.new("RGB", target_size, color="black")

        return image
    except Exception as e:
        logger.warning(f"Ошибка загрузки {image_path}: {e}")
        return Image.new("RGB", target_size, color="black")


class RobustWagonDataset:
    """Надежный датасет с обработкой поврежденных изображений"""

    def __init__(
        self,
        data_dir: str,
        class_names: List[str],
        transform: Optional[transforms.Compose] = None,
        mode: str = "train",
    ):
        self.image_paths = []
        self.labels = []
        self.transform = transform
        self.class_names = class_names

        data_path = os.path.join(data_dir, mode)

        for class_idx, class_name in enumerate(class_names):
            class_dir = os.path.join(data_path, class_name)
            if not os.path.exists(class_dir):
                logger.warning(f"Папка {class_dir} не найдена!")
                continue

            images = [
                f
                for f in os.listdir(class_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            for img in images:
                self.image_paths.append(os.path.join(class_dir, img))
                self.labels.append(class_idx)

        logger.info(f"{mode.upper()}: загружено {len(self.image_paths)} изображений")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = load_image_safe(img_path)

        if self.transform:
            image = self.transform(image)

        return image, self.labels[idx]


# ================================================
# СОЗДАНИЕ МОДЕЛИ
# ================================================


def create_efficientnet_model(
    num_classes: int = 3, pretrained: bool = True
) -> nn.Module:
    """Создание модели EfficientNet-B2"""
    from torchvision import models

    if pretrained:
        model = models.efficientnet_b2(weights="DEFAULT")
        logger.info("Используются предобученные веса ImageNet")
    else:
        model = models.efficientnet_b2(weights=None)
        logger.info("Создана модель со случайными весами")

    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3), nn.Linear(in_features, num_classes)
    )

    return model


def get_device() -> str:
    """Определение устройства для вычислений"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Используется устройство: {device}")

    if device == "cuda":
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

    return device


# ================================================
# ТРАНСФОРМАЦИИ
# ================================================


def get_train_transforms() -> transforms.Compose:
    """Трансформации для обучения (с аугментацией)"""
    return transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def get_val_transforms() -> transforms.Compose:
    """Трансформации для валидации (без аугментации)"""
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


# ================================================
# USE CASE ОБУЧЕНИЯ
# ================================================


class TrainModelUseCase:
    """Use case для обучения модели"""

    def __init__(self, data_dir: str, model_save_path: str, class_names: List[str]):
        self.data_dir = data_dir
        self.model_save_path = model_save_path
        self.class_names = class_names
        self.num_classes = len(class_names)

    def _create_dataloaders(self, config: TrainingConfig):
        """Создание DataLoader'ов для обучения и валидации"""
        train_dataset = RobustWagonDataset(
            self.data_dir,
            self.class_names,
            transform=get_train_transforms(),
            mode="train",
        )

        val_dataset = RobustWagonDataset(
            self.data_dir, self.class_names, transform=get_val_transforms(), mode="val"
        )

        if len(train_dataset) == 0:
            raise DataPreparationException("Обучающие данные не найдены!")

        train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=0,
            pin_memory=torch.cuda.is_available(),
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=torch.cuda.is_available(),
        )

        return train_loader, val_loader

    def _train_epoch(
        self, model, loader, criterion, optimizer, device
    ) -> Tuple[float, float]:
        """Обучение одной эпохи"""
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        train_bar = tqdm(loader, desc="Training")
        for images, labels in train_bar:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            train_bar.set_postfix(
                {"Loss": f"{loss.item():.4f}", "Acc": f"{100. * correct / total:.1f}%"}
            )

        return total_loss / len(loader), correct / total

    def _validate_epoch(self, model, loader, criterion, device) -> Tuple[float, float]:
        """Валидация одной эпохи"""
        model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            val_bar = tqdm(loader, desc="Validation")
            for images, labels in val_bar:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images)
                loss = criterion(outputs, labels)

                total_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        return total_loss / len(loader), correct / total

    def _save_model(self, model, optimizer, epoch, val_acc, train_acc):
        """Сохранение модели"""
        os.makedirs(os.path.dirname(self.model_save_path), exist_ok=True)

        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_acc,
                "train_acc": train_acc,
                "class_names": self.class_names,
                "timestamp": datetime.now().isoformat(),
            },
            self.model_save_path,
        )

    def execute(self, config: Optional[TrainingConfig] = None) -> TrainingHistory:
        """
        Запуск обучения модели

        Args:
            config: Конфигурация обучения

        Returns:
            TrainingHistory: История обучения
        """
        if config is None:
            config = TrainingConfig()

        device = config.device or get_device()
        logger.info("=" * 60)
        logger.info("🏋️‍♂️ НАЧИНАЕМ ОБУЧЕНИЕ")
        logger.info("=" * 60)
        logger.info(f"Устройство: {device}")
        logger.info(f"Классы: {self.class_names}")
        logger.info(f"Batch size: {config.batch_size}, Эпох: {config.num_epochs}")

        # Очистка кэша GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Проверка наличия данных
        if not os.path.exists(self.data_dir):
            raise DataPreparationException(f"Данные не найдены: {self.data_dir}")

        # Создание DataLoader'ов
        train_loader, val_loader = self._create_dataloaders(config)

        # Создание модели
        model = create_efficientnet_model(self.num_classes, pretrained=True).to(device)

        # Функция потерь и оптимизатор
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

        # История обучения
        history = TrainingHistory()

        logger.info("=" * 50)
        logger.info("🏁 НАЧАЛО ОБУЧЕНИЯ")
        logger.info("=" * 50)

        for epoch in range(config.num_epochs):
            logger.info(f"\n📅 ЭПОХА {epoch + 1}/{config.num_epochs}")

            # Обучение
            train_loss, train_acc = self._train_epoch(
                model, train_loader, criterion, optimizer, device
            )

            # Валидация
            val_loss, val_acc = self._validate_epoch(
                model, val_loader, criterion, device
            )

            # Обновляем scheduler
            scheduler.step()

            # Сохраняем историю
            history.add_epoch(train_loss, train_acc, val_loss, val_acc, epoch)

            # Сохраняем лучшую модель
            if val_acc > history.best_val_acc:
                self._save_model(model, optimizer, epoch, val_acc, train_acc)
                logger.info(f"💾 Сохранена лучшая модель! Точность: {val_acc:.4f}")

            logger.info(f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f}")
            logger.info(f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")
            logger.info(f"LR: {scheduler.get_last_lr()[0]:.2e}")

        logger.info("=" * 60)
        logger.info("🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!")
        logger.info("=" * 60)
        logger.info(f"🏆 Лучшая точность: {history.best_val_acc:.4f}")
        logger.info(f"💾 Модель сохранена: {self.model_save_path}")

        return history
