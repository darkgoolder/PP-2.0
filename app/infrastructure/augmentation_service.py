"""
Сервис аугментации данных
"""

from torchvision import transforms


class AugmentationService:
    """Сервис для аугментации изображений"""

    @staticmethod
    def get_train_transforms() -> transforms.Compose:
        """Трансформации для обучения (с аугментацией)"""
        return transforms.Compose(
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

    @staticmethod
    def get_val_transforms() -> transforms.Compose:
        """Трансформации для валидации (без аугментации)"""
        return transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
