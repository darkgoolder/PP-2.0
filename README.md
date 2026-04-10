FB - (Front-Back) 
  
FB - сервис для автоматического определения ориентации железнодорожного вагона по изображению с использованием модели EfficientNet-B2.
Сервис получает изображение вагона, запускает модель EfficientNet-B2 для классификации, определяя, является ли изображение передней частью вагона, задней частью или не содержит вагона. На выходе система возвращает метку класса и уверенность предсказания.
Логика решения
  
Основной сценарий работы:

1.	Пользователь отправляет изображение вагона через API или CLI
   
2.	Изображение проходит предварительную обработку (Resize, Normalize)
   
3.	Модель EfficientNet-B2 выполняет классификацию изображения
   
4.	Результат инференса преобразуется в доменную сущность с вероятностями
   
5.	API возвращает предсказанный класс и распределение вероятностей
  
Упрощенная схема:
```
Image → Preprocessing → EfficientNet-B2 Inference → Softmax → Classification Result
```
  
Возможные классы:

•	pered - передняя часть вагона

•	zad - задняя часть вагона

•	none - вагон не обнаружен на изображении
  
# Архитектура проекта
  
```
FB/
├── app/
│   ├── application/      # Use case и прикладные порты
│   ├── core/             # Конфигурация приложения
│   ├── domain/           # Бизнес-сущности, доменные сервисы
│   ├── infrastructure/   # Адаптеры модели, preprocessing, сериализация
│   ├── interfaces/       # HTTP API (FastAPI) и CLI
│   └── main.py           # Точка входа FastAPI
├── models/               # Директория для сохранения моделей
├── tests/
│   ├── unit/             # Unit-тесты
│   └── integration/      # Интеграционные тесты
├── .github/workflows/    # CI/CD pipeline
├── docs/                 # Проектная документация
├── examples/             # Примеры использования
└── scripts/              # Вспомогательные скрипты
```
  
Кратко по слоям:

•	app/domain - бизнес-логика классификации вагонов без привязки к FastAPI или модели

•	app/application - оркестрация сценария предсказания через ClassifyUseCase

•	app/infrastructure - конкретные реализации для модели EfficientNet, preprocessing, загрузки изображений

•	app/interfaces - REST API слой (FastAPI) и CLI интерфейс

•	app/core/config.py - единая точка доступа к переменным окружения
  
Технологии

•	Python 3.9

•	FastAPI - веб-фреймворк для API

•	PyTorch – язык для программирования 

•	TorchVision - модели и трансформации (EfficientNet-B2)

•	EfficientNet-B2 - предобученная модель для классификации

•	OpenCV - обработка изображений

•	NumPy - работа с массивами

•	Pillow - работа с изображениями

•	scikit-learn - метрики и визуализация

•	Matplotlib, Seaborn - визуализация результатов

•	Pytest - тестирование

•	Flake8, Pylint, Mypy, Black, isort - качество кода

•	GitHub Actions - CI/CD

•	Docker - контейнеризация

•	uv - менеджер зависимостей
  
# Установка и запуск
  
Требования

•	Python 3.9

•	CUDA (опционально, для GPU)

•	pip или uv (рекомендуется)

•	Docker (опционально)
  
Локальный запуск через uv
  
1.	Клонируйте репозиторий:
```
bash
git clone https://github.com/yourusername/pp-2.0.git
cd pp-2.0
```
  
2.	Создайте и активируйте виртуальное окружение:
```
bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```
  
3.	Установите зависимости через uv:
```
bash
uv sync --all-groups
```
  
4.	Скопируйте и настройте переменные окружения:
```
bash
cp .env.example .env
```
  
Минимальная конфигурация .env:
```
env
MODEL_PATH=models/best_model.pth
CLASS_NAMES=pered,zad,none
IMAGE_SIZE=224
BATCH_SIZE=32
DEVICE=cpu  # или cuda для GPU
API_HOST=0.0.0.0
API_PORT=8000
```
  
5.	Запустите FastAPI сервер:
  
```
bash
uvicorn app.main:app --reload
```
  
Для Windows PowerShell:
  
  
```
powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
uv sync --all-groups
uvicorn app.main:app --reload
```
  
6.	API будет доступен по адресу:
   
•	API: http://127.0.0.1:8000

•	Swagger UI: http://127.0.0.1:8000/docs

•	ReDoc: http://127.0.0.1:8000/redoc
  
Использование API
  
Входные параметры:
  
Параметр  |   Тип	   |    Описание
|---------|----------|---------------------------------------|
file	    |   File	 |    Изображение вагона (JPEG, PNG, JPG)
  
Пример через curl:
```
bash
curl -X POST "http://127.0.0.1:8000/classify" \
  -F "file=@examples/yournamepage.jpg" \
  --output result.json
```
  
Пример ответа (JSON)
```
json
{
  "success": true,
  "predicted_class": "pered",
  "confidence": 0.9543,
  "probabilities": {
    "pered": 0.9543,
    "zad": 0.0321,
    "none": 0.0136
  },
  "processing_time_ms": 45.2,
  "image_size": [224, 224]
}
```
  
# Обучение модели
  
Подготовка данных
  
Запуск обучения:
```
python train.py
```
  
Параметры обучения
```
Параметр	Значение по умолчанию	Описание
BATCH_SIZE	32	Размер батча для обучения
NUM_EPOCHS	15	Количество эпох обучения
LEARNING_RATE	1e-4	Скорость обучения
IMAGE_SIZE	224	Размер входного изображения
DEVICE	cuda/cpu	Устройство для обучения
```
  
# Мониторинг обучения
  
В процессе обучения сохраняются:
  
•	Лучшая модель (models/best_model.pth)

•	История обучения (потери и точность)

•	Графики обучения (training_results.png)

•	Confusion matrix и classification report
  
  
# Конфигурация
```
Переменные окружения
Переменная	Описание	Значение по умолчанию
MODEL_PATH	Путь к файлу модели	models/best_model.pth
CLASS_NAMES	Список классов через запятую	pered,zad,none
IMAGE_SIZE	Размер входного изображения	224
BATCH_SIZE	Размер батча	32
NUM_EPOCHS	Количество эпох	15
LEARNING_RATE	Скорость обучения	0.0001
DEVICE	Устройство (cuda/cpu)	cuda (если доступно)
API_HOST	Хост для FastAPI	0.0.0.0
API_PORT	Порт для FastAPI	8000
LOG_LEVEL	Уровень логирования	INFO
```
  
# Тестирование и качество кода
  
Запуск unit-тестов
```
bash
uv run pytest -q
```
Запуск тестов с покрытием
```
bash
uv run pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```
# Запуск проверок качества
  
Форматирование
```
bash
uv run black --check app tests
uv run isort --check-only app tests
```
  
Type checking
```
bash
uv run mypy app
```
  
# Производительность модели:
  
Метрика	                    |  Значение
|---------------------------|----------------|
Модель	                    | EfficientNet-B2
Параметры                   |	9.1M
Размер модели               |	~35 MB
Время инференса (CPU)       |	45-60 ms
Время инференса (GPU)       |	8-12 ms
Точность на валидации       |	92-95%
Размер входного изображения |	224x224
Результаты обучения         | (пример ниже)
    
```
Classification Report:
              precision    recall  f1-score   support
       pered       0.94      0.93      0.93       150
         zad       0.93      0.94      0.93       150
        none       0.96      0.95      0.95       150

    accuracy                           0.94       450
   macro avg       0.94      0.94      0.94       450
weighted avg       0.94      0.94      0.94       450
```
  
# Docker
  
Стандартная сборка
```
bash
docker build -t fb-classifier
```
  
Сборка с кэшированием модели
  
```
bash
docker build --build-arg CACHE_MODEL=true -t fb-classifier
```
  
Запуск контейнера
```
bash
docker run --rm -p 8000:8000 \
  -e MODEL_PATH=models/best_model.pth \
  -e DEVICE=cpu \
  -v $(pwd)/models:/app/models \
  fb-classifier
```
  
CI/CD Pipeline
В репозитории настроен GitHub Actions pipeline:

•	lint - проверка форматирования (black, isort, flake8, pylint, mypy)

•	test - unit-тесты и контроль покрытия (не ниже 80%)

•	docker - проверка сборки Docker-образа

•	security - сканирование уязвимостей

Coverage-отчет сохраняется как artifact после job test.
  
Secrets для GitHub Actions

Для GitHub Settings -> Secrets and variables -> Actions добавьте:
  
Secrets:

•	DOCKER_USERNAME - имя пользователя Docker Hub

•	DOCKER_PASSWORD - пароль Docker Hub
  
Variables:

•	MODEL_PATH - путь к модели

•	DEVICE - устройство для тестов
  
Воспроизведение результата

Полный пайплайн обучения и инференса

```python```
  
# train.py - обучение модели
```from wagon_classifier import train_simple_model```
  
model, history = train_simple_model()

Модель сохраняется в models/best_model.pth

Графики сохраняются в training_results.png
  
inference.py - использование модели

```from wagon_classifier import predict_single_image```
  
```result = predict_single_image()```

# Результат: (predicted_class, confidence)
  
Пример интеграции
```
python
import requests
import base64
from PIL import Image
import io
```
  
# Классификация через API
```
   def classify_wagon(image_path):
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:8000/classify', files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Класс: {result['predicted_class']}")
        print(f"Уверенность: {result['confidence']:.2%}")
        print(f"Вероятности: {result['probabilities']}")
        return result
    else:
        print(f"Ошибка: {response.status_code}")
        return None
```
  
# Использование

```result = classify_wagon('wagon_photo.jpg')```
  
Устранение неполадок
  
Проблема: Модель не загружается

Решение: Убедитесь, что файл модели существует:

```
bash
ls -la models/best_model.pth
```
  
Если файла нет, обучите модель: python train.py

Проблема: Низкая точность классификации

Решение:

1.	Увеличьте количество эпох обучения
   
3.	Добавьте аугментацию данных
   
5.	Используйте предобученную модель на большем датасете
  
Проблема: Out of Memory на GPU
  
Решение:

BATCH_SIZE=16  Уменьшите размер батча

IMAGE_SIZE=128  Уменьшите размер изображения

Проблема: Медленный инференс на CPU
  
Решение:

Используйте меньшую модель

```
bash
MODEL_NAME=efficientnet_b0
```
Вместо b2
  
Или оптимизируйте модель

```
bash
python -m app.optimize --model models/best_model.pth --output models/optimized.pt
```


  
  
  
  
Запуск API:
```Command Prompt
uvicorn app.main:app --reload
```
  
