# """
# Use Case: Обучение модели
# Содержит бизнес-логику обучения EfficientNet-B2
# """

# import logging
# import os
# from dataclasses import dataclass
# from typing import Optional, Tuple

# import torch
# from torch import nn, optim
# from torch.utils.data import DataLoader
# from torchvision import transforms
# from tqdm import tqdm

# from app.domain.entities import TrainingConfig, TrainingHistory
# from app.domain.exceptions import DataPreparationException
# from app.infrastructure.model_repository import RobustWagonDataset, create_model

# logger = logging.getLogger(__name__)


# @dataclass
# class TrainingConfig:
#     """Конфигурация обучения"""

#     batch_size: int = 32
#     num_epochs: int = 15
#     learning_rate: float = 1e-4
#     device: Optional[str] = None


# @dataclass
# class TrainingHistory:
#     """История обучения"""

#     train_loss: list = None
#     train_acc: list = None
#     val_loss: list = None
#     val_acc: list = None
#     best_val_acc: float = 0.0

#     def __post_init__(self):
#         if self.train_loss is None:
#             self.train_loss = []
#             self.train_acc = []
#             self.val_loss = []
#             self.val_acc = []


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
from typing import Optional, Tuple

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import transforms
from tqdm import tqdm

from app.domain.entities import TrainingConfig, TrainingHistory
from app.domain.exceptions import DataPreparationException
from app.infrastructure.model_repository import RobustWagonDataset, create_model

logger = logging.getLogger(__name__)


class TrainModelUseCase:
    """Use case для обучения модели"""

    def __init__(self, data_dir: str, model_save_path: str, class_names: list):
        self.data_dir = data_dir
        self.model_save_path = model_save_path
        self.class_names = class_names
        self.num_classes = len(class_names)

    def _get_transforms(self) -> Tuple[transforms.Compose, transforms.Compose]:
        """Получение трансформаций для обучения и валидации"""
        train_transform = transforms.Compose(
            [
                transforms.Resize((256, 256)),
                transforms.RandomCrop(224),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ColorJitter(brightness=0.2, contrast=0.2),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        val_transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        return train_transform, val_transform

    def execute(self, config: Optional[TrainingConfig] = None) -> TrainingHistory:
        """Запуск обучения модели"""
        if config is None:
            config = TrainingConfig()

        device = config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Начало обучения на устройстве: {device}")
        logger.info(f"Batch size: {config.batch_size}, Эпох: {config.num_epochs}")

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if not os.path.exists(self.data_dir):
            raise DataPreparationException(f"Данные не найдены: {self.data_dir}")

        train_transform, val_transform = self._get_transforms()

        train_dataset = RobustWagonDataset(
            self.data_dir, self.class_names, transform=train_transform, mode="train"
        )

        val_dataset = RobustWagonDataset(
            self.data_dir, self.class_names, transform=val_transform, mode="val"
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

        model = create_model(self.num_classes).to(device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

        history = TrainingHistory()

        logger.info("=" * 50)
        logger.info("НАЧАЛО ОБУЧЕНИЯ")
        logger.info("=" * 50)

        for epoch in range(config.num_epochs):
            logger.info(f"\nЭпоха {epoch + 1}/{config.num_epochs}")

            train_loss, train_acc = self._train_epoch(
                model, train_loader, criterion, optimizer, device
            )

            val_loss, val_acc = self._validate_epoch(
                model, val_loader, criterion, device
            )

            scheduler.step()

            history.train_loss.append(train_loss)
            history.train_acc.append(train_acc)
            history.val_loss.append(val_loss)
            history.val_acc.append(val_acc)

            if val_acc > history.best_val_acc:
                history.best_val_acc = val_acc
                self._save_model(model, optimizer, epoch, val_acc, train_acc)
                logger.info(f"Сохранена лучшая модель! Точность: {val_acc:.4f}")

            logger.info(f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f}")
            logger.info(f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

        logger.info("=" * 50)
        logger.info(f"Обучение завершено! Лучшая точность: {history.best_val_acc:.4f}")
        logger.info(f"Модель сохранена: {self.model_save_path}")

        return history

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

        avg_loss = total_loss / len(loader)
        accuracy = correct / total

        return avg_loss, accuracy

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

        avg_loss = total_loss / len(loader)
        accuracy = correct / total

        return avg_loss, accuracy

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
            },
            self.model_save_path,
        )
