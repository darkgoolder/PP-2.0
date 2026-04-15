# """
# Unit-тесты для use case обучения модели (с моками)
# """

# import pytest
# from unittest.mock import Mock, AsyncMock, patch
# from app.use_cases.train_model import TrainModelUseCase


# class TestTrainModelUseCase:
#     """Тесты use case обучения модели"""
    
#     @pytest.fixture
#     def mock_model_repository(self):
#         """Мок репозитория модели"""
#         with patch('app.infrastructure.model_repository.create_model') as mock:
#             mock_model = Mock()
#             mock_model.to = Mock(return_value=mock_model)
#             mock.return_value = mock_model
#             yield mock
    
#     @pytest.fixture
#     def use_case(self, tmp_path):
#         """Use case с временными путями"""
#         data_dir = tmp_path / "data"
#         data_dir.mkdir()
#         return TrainModelUseCase(
#             data_dir=str(data_dir),
#             model_save_path=str(tmp_path / "model.pth"),
#             class_names=["pered", "zad", "none"]
#         )
    
#     def test_initialization_creates_use_case(self, use_case):
#         """Инициализация — создаёт объект use case"""
#         assert use_case is not None
#         assert use_case.num_classes == 3
    
#     def test_get_transforms_returns_two_transforms(self, use_case):
#         """Получение трансформаций — возвращает train и val трансформации"""
#         train_transform, val_transform = use_case._get_transforms()
#         assert train_transform is not None
#         assert val_transform is not None


"""
Unit-тесты для TrainModelUseCase
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.use_cases.train_model import TrainModelUseCase, TrainingConfig, TrainingHistory


class TestTrainModelUseCase:
    """Тесты use case обучения модели"""
    
    def test_initialization_creates_use_case(self, tmp_path):
        """Инициализация — создаёт объект use case"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        use_case = TrainModelUseCase(
            data_dir=str(data_dir),
            model_save_path=str(tmp_path / "model.pth"),
            class_names=["pered", "zad", "none"]
        )
        
        assert use_case is not None
        assert use_case.num_classes == 3
        assert use_case.data_dir == str(data_dir)
    
    def test_training_config_default_values(self):
        """TrainingConfig — имеет корректные значения по умолчанию"""
        config = TrainingConfig()
        
        assert config.batch_size == 32
        assert config.num_epochs == 15
        assert config.learning_rate == 1e-4
        assert config.val_split == 0.2
    
    def test_training_history_tracks_best_accuracy(self):
        """TrainingHistory — отслеживает лучшую точность"""
        history = TrainingHistory()
        
        history.add_epoch(train_loss=1.0, train_acc=0.5,
                         val_loss=0.9, val_acc=0.6, epoch=0)
        history.add_epoch(train_loss=0.8, train_acc=0.7,
                         val_loss=0.7, val_acc=0.8, epoch=1)
        
        assert history.best_val_acc == 0.8
        assert history.best_epoch == 1
        assert len(history.train_loss) == 2
        assert len(history.val_acc) == 2
    
    def test_get_device_returns_string(self):
        """get_device — возвращает строку с устройством"""
        from app.use_cases.train_model import get_device
        device = get_device()
        assert device in ["cuda", "cpu"]
    
    def test_get_transforms_returns_compose(self):
        """Трансформации — возвращают объект Compose"""
        from app.use_cases.train_model import get_train_transforms, get_val_transforms
        
        train_transform = get_train_transforms()
        val_transform = get_val_transforms()
        
        assert train_transform is not None
        assert val_transform is not None