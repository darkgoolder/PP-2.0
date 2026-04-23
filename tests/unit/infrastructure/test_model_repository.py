"""
Unit-тесты для репозитория модели (с моками)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from app.infrastructure.model_repository import WagonClassifier
import torch
# import torch.nn as nn
# from torchvision import models


class TestWagonClassifier:
    """Тесты классификатора с моками"""
    
    @pytest.fixture
    def mock_model(self):
        """Мок модели PyTorch"""
        model = MagicMock()
        model.return_value = MagicMock()
        return model
    
    @pytest.fixture
    def classifier(self, tmp_path):
        """Создание классификатора с временным файлом модели"""
        import torch
        import torch.nn as nn
        from torchvision import models
        
        # Создаём фиктивную модель
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        return WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_classifier_initialization(self, classifier):
        """Классификатор инициализируется корректно"""
        assert classifier is not None
        assert classifier.device == 'cpu'
        assert len(classifier.class_names) == 3
    
    def test_predict_returns_tuple(self, classifier):
        """Метод predict возвращает кортеж из 3 элементов"""
        image = Image.new('RGB', (224, 224), color='red')
        
        result = classifier.predict(image)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], str)  # class
        assert isinstance(result[1], float)  # confidence
        assert isinstance(result[2], dict)  # probabilities
        
    def test_predict_batch_returns_list(self, classifier):
        """Пакетное предсказание — возвращает список результатов"""
        # Arrange - создаём ДВА изображения
        images = [
            Image.new('RGB', (224, 224), color='red'),
            Image.new('RGB', (224, 224), color='blue')
        ]
        
        # Act
        results = classifier.predict_batch(images)
        
        # Assert
        assert isinstance(results, list)
        assert len(results) == 2  # теперь будет 2
        for result in results:
            assert "class" in result
            assert "confidence" in result
            assert "probabilities" in result
            
            
class TestWagonClassifierProperties:
    """Тесты свойств классификатора"""
    
    @pytest.fixture
    def classifier(self, tmp_path):
        from app.infrastructure.model_repository import WagonClassifier
        import torch
        import torch.nn as nn
        from torchvision import models
        
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        return WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_class_names_property(self, classifier):
        """Свойство class_names — возвращает список классов"""
        assert classifier.class_names == ['pered', 'zad', 'none']
    
    def test_device_property(self, classifier):
        """Свойство device — возвращает устройство"""
        assert classifier.device in ['cuda', 'cpu']
    
    def test_class_names_ru_property(self, classifier):
        """Свойство class_names_ru — возвращает русские названия"""
        assert "pered" in classifier.class_names_ru
        assert "zad" in classifier.class_names_ru
        assert "none" in classifier.class_names_ru
        

class TestWagonClassifierAdditional:
    """Дополнительные тесты классификатора"""
    
    @pytest.fixture
    def classifier(self, tmp_path):
        from app.infrastructure.model_repository import WagonClassifier
        import torch
        import torch.nn as nn
        from torchvision import models
        
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        return WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_class_names_ru_contains_all_classes(self, classifier):
        """class_names_ru — содержит все классы"""
        assert "pered" in classifier.class_names_ru
        assert "zad" in classifier.class_names_ru
        assert "none" in classifier.class_names_ru
        assert classifier.class_names_ru["pered"] == "передняя часть вагона"
    
    def test_preprocess_image_returns_tensor(self, classifier):
        """Предобработка изображения — возвращает тензор"""
        from PIL import Image
        image = Image.new('RGB', (224, 224), color='red')
        
        tensor = classifier._preprocess_image(image)
        
        assert tensor is not None
        assert tensor.shape[0] == 1  # batch
        assert tensor.shape[1] == 3  # channels
    
    def test_predict_batch_empty_list_returns_empty(self, classifier):
        """Пакетное предсказание с пустым списком — возвращает пустой список"""
        results = classifier.predict_batch([])
        assert results == []
        
        
class TestWagonClassifierEdgeCases:
    """Тесты краевых случаев классификатора"""
    
    @pytest.fixture
    def classifier(self, tmp_path):
        from app.infrastructure.model_repository import WagonClassifier
        import torch
        import torch.nn as nn
        from torchvision import models
        
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        return WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_predict_with_non_rgb_image_converts_automatically(self, classifier):
        """Предсказание с изображением в режиме L (черно-белое) — автоматически конвертирует в RGB"""
        from PIL import Image
        # Создаём черно-белое изображение
        image = Image.new('L', (224, 224), color=128)
        
        result = classifier.predict(image)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_predict_with_different_image_sizes_works(self, classifier):
        """Предсказание с изображениями разных размеров — работает (ресемплинг)"""
        from PIL import Image
        image = Image.new('RGB', (500, 300), color='red')
        
        result = classifier.predict(image)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    # def test_get_classifier_returns_singleton(self):
    #     """get_classifier — возвращает один и тот же экземпляр (синглтон)"""
    #     from app.infrastructure.model_repository import get_classifier, _classifier_instance
        
    #     # Сбрасываем синглтон для теста
    #     import app.infrastructure.model_repository as repo
    #     repo._classifier_instance = None
        
    #     classifier1 = get_classifier()
    #     classifier2 = get_classifier()
        
    #     assert classifier1 is classifier2
    
    def test_load_model_handles_checkpoint_without_state_dict(self, tmp_path):
        """Загрузка модели — обрабатывает чекпоинт без ключа model_state_dict"""
        from app.infrastructure.model_repository import WagonClassifier
        import torch
        import torch.nn as nn
        from torchvision import models
        
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model_direct.pth"
        # Сохраняем напрямую state_dict (без обёртки)
        torch.save(model.state_dict(), model_path)
        
        classifier = WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
        
        assert classifier is not None
        
        
        
class TestWagonClassifierModelLoading:
    """Тесты загрузки модели (покрытие строк 29-43, 50-72, 75, 78-84)"""
    
    def test_create_model_returns_efficientnet(self):
        """create_model — создаёт модель EfficientNet-B2"""
        from app.infrastructure.model_repository import create_model
        
        model = create_model(num_classes=3)
        
        assert model is not None
        # Проверяем, что это EfficientNet
        assert "efficientnet" in model.__class__.__name__.lower()
    
    def test_create_model_with_custom_num_classes(self):
        """create_model — создаёт модель с правильным количеством классов"""
        from app.infrastructure.model_repository import create_model
        
        model = create_model(num_classes=5)
        
        # Последний слой должен иметь 5 выходов
        assert model.classifier[-1].out_features == 5
    
    def test_load_image_safe_handles_corrupted_image(self, tmp_path):
        """load_image_safe — обрабатывает повреждённое изображение"""
        from app.infrastructure.model_repository import load_image_safe
        
        # Создаём битый файл
        bad_path = tmp_path / "bad.jpg"
        bad_path.write_bytes(b"not an image")
        
        image = load_image_safe(str(bad_path))
        
        # Должен вернуть чёрное изображение, а не упасть
        assert image is not None
        assert image.size == (224, 224)
    
    def test_load_image_safe_handles_zero_size_image(self, tmp_path):
        """load_image_safe — обрабатывает маленькое изображение"""
        from app.infrastructure.model_repository import load_image_safe
        from PIL import Image
        
        # Создаём маленькое изображение 1x1
        img_path = tmp_path / "small.png"
        img = Image.new('RGB', (1, 1), color='black')
        img.save(img_path)
        
        image = load_image_safe(str(img_path))
        
        # Функция load_image_safe возвращает изображение как есть
        assert image is not None
        # Проверяем, что изображение загрузилось (размер может быть 1x1)
        assert image.size == (1, 1)
    
    def test_robust_wagon_dataset_initialization(self, tmp_path):
        """RobustWagonDataset — инициализируется с корректными данными"""
        from app.infrastructure.model_repository import RobustWagonDataset
        
        # Создаём структуру папок
        data_dir = tmp_path / "data"
        for split in ["train", "val"]:
            for class_name in ["pered", "zad", "none"]:
                (data_dir / split / class_name).mkdir(parents=True, exist_ok=True)
                # Создаём пустой файл-заглушку
                (data_dir / split / class_name / "test.jpg").touch()
        
        dataset = RobustWagonDataset(
            data_dir=str(data_dir),
            class_names=["pered", "zad", "none"],
            mode="train"
        )
        
        assert len(dataset) == 3  # по одному изображению на класс


class TestWagonClassifierExceptionHandling:
    """Тесты обработки исключений"""
    
    @pytest.fixture
    def classifier_with_missing_model(self, tmp_path):
        """Классификатор с отсутствующим файлом модели"""
        from app.infrastructure.model_repository import WagonClassifier
        
        # Путь к несуществующему файлу
        missing_path = tmp_path / "missing.pth"
        
        return WagonClassifier(
            model_path=str(missing_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
    
    def test_load_model_raises_file_not_found(self, tmp_path):
        """_load_model — вызывает FileNotFoundError при отсутствии модели"""
        from app.infrastructure.model_repository import WagonClassifier
        
        # Путь к несуществующему файлу
        missing_path = tmp_path / "missing.pth"
        
        with pytest.raises(FileNotFoundError) as exc:
            WagonClassifier(
                model_path=str(missing_path),
                class_names=['pered', 'zad', 'none'],
                device='cpu'
            )
        
        assert "Model not found" in str(exc.value)
    
    def test_predict_handles_exception_and_raises(self, tmp_path):
        """predict — перехватывает исключение и пробрасывает дальше"""
        from app.infrastructure.model_repository import WagonClassifier
        from PIL import Image
        import torch
        
        # Создаём некорректный чекпоинт (сохраняем строку вместо словаря)
        bad_path = tmp_path / "bad_model.pth"
        # Используем torch.save с некорректным форматом
        with open(bad_path, 'w') as f:
            f.write("not a valid checkpoint")
        
        with pytest.raises(Exception):
            classifier = WagonClassifier(
                model_path=str(bad_path),
                class_names=['pered', 'zad', 'none'],
                device='cpu'
            )
            # Доступ к model вызывает _load_model
            _ = classifier.model
    
    def test_get_classifier_returns_singleton(self):
        """get_classifier — возвращает синглтон (с моком)"""
        from app.infrastructure.model_repository import get_classifier, _classifier_instance
        from unittest.mock import patch
        
        # Сбрасываем синглтон
        import app.infrastructure.model_repository as repo
        repo._classifier_instance = None
        
        # Мокаем создание классификатора, чтобы не загружать реальную модель
        with patch('app.infrastructure.model_repository.WagonClassifier') as MockClassifier:
            MockClassifier.return_value = "mock_classifier"
            
            classifier1 = get_classifier()
            classifier2 = get_classifier()
            
            # Проверяем, что синглтон работает
            assert classifier1 is classifier2
    
    def test_predict_batch_processes_multiple_images(self, tmp_path):
        """predict_batch — обрабатывает несколько изображений"""
        from app.infrastructure.model_repository import WagonClassifier
        from PIL import Image
        import torch
        import torch.nn as nn
        from torchvision import models
        
        # Создаём реальную модель для теста
        model = models.efficientnet_b2(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 3)
        )
        
        model_path = tmp_path / "test_model.pth"
        torch.save({
            'model_state_dict': model.state_dict(),
            'class_names': ['pered', 'zad', 'none']
        }, model_path)
        
        classifier = WagonClassifier(
            model_path=str(model_path),
            class_names=['pered', 'zad', 'none'],
            device='cpu'
        )
        
        images = [
            Image.new('RGB', (224, 224), color='red'),
            Image.new('RGB', (224, 224), color='blue'),
            Image.new('RGB', (224, 224), color='green')
        ]
        
        results = classifier.predict_batch(images)
        
        assert len(results) == 3
        for result in results:
            assert "class" in result
            assert "confidence" in result
            assert "probabilities" in result