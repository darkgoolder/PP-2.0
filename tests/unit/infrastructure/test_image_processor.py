"""
Unit-тесты для обработчика изображений
"""

import pytest
from PIL import Image
import io
from fastapi import HTTPException
from app.infrastructure.image_processor import validate_image_file, process_image
from app.config import settings


class MockUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.file = io.BytesIO(content)
    
    def seek(self, offset, whence=0):
        self.file.seek(offset, whence)
    
    def tell(self):
        return self.file.tell()
    
    def read(self):
        return self.file.getvalue()


class TestValidateImageFile:
    """Тесты валидации изображений"""
    
    def test_valid_jpg_file_passes(self):
        """Корректный JPG файл — проходит валидацию"""
        img = Image.new('RGB', (100, 100))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        file = MockUploadFile("test.jpg", img_bytes.getvalue())
        
        result = validate_image_file(file, settings)
        assert result is True
    
    def test_valid_png_file_passes(self):
        """Корректный PNG файл — проходит валидацию"""
        img = Image.new('RGB', (100, 100))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        file = MockUploadFile("test.png", img_bytes.getvalue())
        
        result = validate_image_file(file, settings)
        assert result is True
    
    def test_invalid_extension_raises_error(self):
        """Неподдерживаемое расширение — вызывает ошибку"""
        file = MockUploadFile("test.txt", b"not an image")
        
        with pytest.raises(HTTPException) as exc:
            validate_image_file(file, settings)
        
        assert exc.value.status_code == 400


class TestProcessImage:
    """Тесты обработки изображений"""
    
    def test_process_valid_jpg_returns_pil_image(self):
        """Обработка корректного JPG — возвращает PIL Image"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        file = MockUploadFile("test.jpg", img_bytes.getvalue())
        
        result = process_image(file)
        
        assert result is not None
        assert result.size == (100, 100)
    
    def test_process_invalid_file_raises_error(self):
        """Обработка некорректного файла — вызывает ошибку"""
        file = MockUploadFile("test.txt", b"not an image")
        
        with pytest.raises(HTTPException) as exc:
            process_image(file)
        
        assert exc.value.status_code == 400
        

class TestImageProcessorCoverage:
    """Тесты для покрытия image_processor.py"""
    
    def test_validate_image_file_with_valid_png(self):
        """Валидация PNG файла — проходит"""
        from PIL import Image
        import io
        from app.infrastructure.image_processor import validate_image_file
        from app.config import settings
        
        class MockFile:
            def __init__(self):
                img = Image.new('RGB', (100, 100))
                self.bytes = io.BytesIO()
                img.save(self.bytes, format='PNG')
                self.bytes.seek(0)
                self.filename = "test.png"
                self.file = self.bytes
        
        result = validate_image_file(MockFile(), settings)
        assert result is True
    
    def test_process_image_with_valid_file(self):
        """Обработка изображения — возвращает PIL Image"""
        from PIL import Image
        import io
        from app.infrastructure.image_processor import process_image
        
        class MockFile:
            def __init__(self):
                img = Image.new('RGB', (100, 100))
                self.bytes = io.BytesIO()
                img.save(self.bytes, format='JPEG')
                self.bytes.seek(0)
                self.file = self.bytes
                self.filename = "test.jpg"
        
        result = process_image(MockFile())
        assert result is not None
        assert result.size == (100, 100)