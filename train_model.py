import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
import torch.cuda.amp as amp
import os
import shutil
import numpy as np
from PIL import Image, ImageFile
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ================================================
# ВКЛЮЧАЕМ ОБРАБОТКУ УСЕЧЕННЫХ ИЗОБРАЖЕНИЙ
# ================================================
ImageFile.LOAD_TRUNCATED_IMAGES = True  # Разрешаем загрузку усеченных изображений

# ================================================
# КОНФИГУРАЦИЯ (С ПРАВИЛЬНЫМИ НАЗВАНИЯМИ КЛАССОВ)
# ================================================
class Config:
    # Пути (изменены для Windows)
    BASE_DIR = os.path.join(os.getcwd(), 'wagon_classification')
    DATA_DIR = os.path.join(os.getcwd(), 'wagon_classification', 'data', 'processed')
    EXTRACTED_DIR = os.path.join(os.getcwd(), 'wagon_data', 'extracted')
    MODEL_SAVE_PATH = os.path.join(os.getcwd(), 'wagon_classification', 'best_model.pth')

    # Параметры - ИСПРАВЛЕНО: pered вместо prered
    CLASS_NAMES = ['pered', 'zad', 'none']  # Изменено prered -> pered
    NUM_CLASSES = 3

    # Гиперпараметры
    BATCH_SIZE = 32  # Оптимальный размер для T4
    NUM_EPOCHS = 15

    # Устройство
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    @staticmethod
    def print_info():
        print(f"\n📊 КОНФИГУРАЦИЯ:")
        print(f"  • Устройство: {Config.DEVICE}")
        if Config.DEVICE.type == 'cuda':
            print(f"  • GPU: {torch.cuda.get_device_name(0)}")
            print(f"  • Память: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print(f"  • Классы: {Config.CLASS_NAMES}")
        print(f"  • Batch size: {Config.BATCH_SIZE}")
        print(f"  • Эпох: {Config.NUM_EPOCHS}")

# ================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ
# ================================================
def load_image_safe(image_path, target_size=(224, 224)):
    """Безопасная загрузка изображения с обработкой ошибок"""
    try:
        # Пытаемся открыть изображение
        image = Image.open(image_path)

        # Проверяем, что изображение валидно
        image.verify()  # Проверка целостности файла

        # Закрываем и открываем снова (после verify нужно переоткрыть)
        image = Image.open(image_path)

        # Конвертируем в RGB если нужно
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Проверяем размеры
        if image.size[0] == 0 or image.size[1] == 0:
            print(f"⚠ Изображение {image_path} имеет нулевые размеры")
            # Создаем черное изображение
            image = Image.new('RGB', target_size, color='black')

        return image

    except (IOError, OSError, Image.DecompressionBombError) as e:
        print(f"⚠ Ошибка загрузки {image_path}: {e}")
        # Создаем черное изображение в случае ошибки
        return Image.new('RGB', target_size, color='black')

    except Exception as e:
        print(f"⚠ Неизвестная ошибка при загрузке {image_path}: {e}")
        return Image.new('RGB', target_size, color='black')

def repair_image_file(image_path):
    """Пытается восстановить поврежденный файл изображения"""
    try:
        with open(image_path, 'rb') as f:
            data = f.read()

        # Проверяем, что файл не пустой
        if len(data) == 0:
            print(f"❌ Файл {image_path} пустой")
            return False

        # Пытаемся восстановить как JPEG
        if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
            # Добавляем маркер конца JPEG если нужно
            if not data.endswith(b'\xff\xd9'):
                print(f"⚠ Восстанавливаю JPEG файл {image_path}")
                data += b'\xff\xd9'
                with open(image_path, 'wb') as f:
                    f.write(data)
                return True

        return False

    except Exception as e:
        print(f"❌ Ошибка при восстановлении {image_path}: {e}")
        return False

# ================================================
# ТРАНСФОРМАЦИИ (ПРОСТЫЕ И РАБОЧИЕ)
# ================================================
def get_transforms():
    """Создание простых и рабочих трансформаций"""
    # Обучающие трансформации
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])

    # Валидационные трансформации
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])

    return train_transform, val_transform

# ================================================
# ПОДГОТОВКА ДАННЫХ (С ПРАВИЛЬНЫМИ ИМЕНАМИ ПАПОК)
# ================================================
def prepare_data_simple():
    """Упрощенная подготовка данных с правильными именами папок"""
    print("=" * 60)
    print("📊 ПОДГОТОВКА ДАННЫХ")
    print("=" * 60)

    # Создаем папки
    os.makedirs(Config.BASE_DIR, exist_ok=True)
    os.makedirs(Config.EXTRACTED_DIR, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)

    # Для Windows - ручной ввод пути к архиву
    print("\n📤 ШАГ 1: Укажите путь к архиву vagon1.rar")
    print("Пример: C:/Users/Username/Downloads/vagon1.rar")
    archive_path = input("Введите полный путь к архиву: ").strip()
    
    # Заменяем прямые слеши на обратные для Windows
    archive_path = archive_path.replace('/', '\\')
    
    if not os.path.exists(archive_path):
        print(f"\n❌ Файл не найден: {archive_path}")
        return False

    print(f"\n✅ Найден архив: {os.path.basename(archive_path)}")

    # Распаковываем с использованием patool (кроссплатформенный)
    try:
        import patoolib
        print("📦 Распаковка архива...")
        patoolib.extract_archive(archive_path, outdir=Config.EXTRACTED_DIR)
        print("✅ Архив распакован")
    except ImportError:
        print("⚠ Установите библиотеку patool: pip install patool")
        print("Или распакуйте архив вручную в папку:", Config.EXTRACTED_DIR)
        return False
    except Exception as e:
        print(f"⚠ Ошибка при распаковке: {e}")
        print("Попробуйте распаковать вручную в папку:", Config.EXTRACTED_DIR)
        return False

    # Проверяем структуру - ИЩЕМ ПРАВИЛЬНЫЕ ИМЕНА ПАПОК
    print("\n🔍 Проверка данных...")

    # Список возможных имен папок (учитываем опечатки)
    possible_folders = {
        'pered': ['pered', 'prered', 'peredn', 'peredniy', 'front', 'перед'],
        'zad': ['zad', 'zadn', 'zadniy', 'back', 'rear', 'зад'],
        'none': ['none', 'non', 'empty', 'нет', 'пусто']
    }

    actual_folders = os.listdir(Config.EXTRACTED_DIR)
    print(f"Найдены папки в extracted: {actual_folders}")

    # Сопоставляем фактические папки с нашими классами
    folder_mapping = {}
    for target_class, possible_names in possible_folders.items():
        for folder in actual_folders:
            folder_lower = folder.lower()
            if folder_lower in possible_names:
                folder_mapping[target_class] = folder
                print(f"  ✓ {target_class} → {folder}")
                break

    # Если не нашли все классы, пытаемся найти по содержимому
    if len(folder_mapping) < len(Config.CLASS_NAMES):
        print("\n⚠ Не все классы найдены. Ищем изображения...")
        for folder in actual_folders:
            folder_path = os.path.join(Config.EXTRACTED_DIR, folder)
            if os.path.isdir(folder_path):
                images = [f for f in os.listdir(folder_path)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if images:
                    print(f"  Папка '{folder}': {len(images)} изображений")
                    # Пробуем угадать класс
                    if 'pered' in folder.lower() or 'перед' in folder.lower():
                        folder_mapping['pered'] = folder
                    elif 'zad' in folder.lower() or 'зад' in folder.lower():
                        folder_mapping['zad'] = folder
                    elif 'none' in folder.lower() or 'нет' in folder.lower():
                        folder_mapping['none'] = folder

    # Проверяем, что нашли все необходимые классы
    missing_classes = []
    for cls in Config.CLASS_NAMES:
        if cls not in folder_mapping:
            missing_classes.append(cls)

    if missing_classes:
        print(f"\n❌ Отсутствуют классы: {missing_classes}")
        print("Пожалуйста, убедитесь что в архиве есть папки с именами:")
        print("  - 'pered' (или похожее) - для передней части вагона")
        print("  - 'zad' (или похожее) - для задней части вагона")
        print("  - 'none' (или похожее) - для отсутствия вагона")
        return False

    print("\n✅ Все классы найдены!")

    # Создаем структуру
    print("\n📁 Создание структуры train/val...")
    for split in ['train', 'val']:
        for cls in Config.CLASS_NAMES:
            os.makedirs(os.path.join(Config.DATA_DIR, split, cls), exist_ok=True)

    # Распределяем данные
    print("📊 Разделение на train/val (80/20)...")
    total_images = 0

    for target_class, source_folder in folder_mapping.items():
        source_dir = os.path.join(Config.EXTRACTED_DIR, source_folder)

        if not os.path.exists(source_dir):
            print(f"⚠ Папка {source_folder} не найдена, пропускаем")
            continue

        images = [f for f in os.listdir(source_dir)
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not images:
            print(f"⚠ В папке {source_folder} нет изображений")
            continue

        print(f"\n📂 Обрабатываем {source_folder} → {target_class}:")
        print(f"  Найдено {len(images)} изображений")

        # Разделяем
        train_imgs, val_imgs = train_test_split(
            images, test_size=0.2, random_state=42
        )

        # Копируем train
        print(f"  Копируем {len(train_imgs)} в train...")
        for img in tqdm(train_imgs, desc=f"  {target_class} train"):
            src = os.path.join(source_dir, img)
            dst = os.path.join(Config.DATA_DIR, 'train', target_class, img)
            shutil.copy2(src, dst)

        # Копируем val
        print(f"  Копируем {len(val_imgs)} в val...")
        for img in tqdm(val_imgs, desc=f"  {target_class} val"):
            src = os.path.join(source_dir, img)
            dst = os.path.join(Config.DATA_DIR, 'val', target_class, img)
            shutil.copy2(src, dst)

        total_images += len(images)
        print(f"  ✓ {target_class}: {len(train_imgs)} train, {len(val_imgs)} val")

    # Проверяем финальную структуру
    print(f"\n✅ Готово! Всего {total_images} изображений")
    print("\n📂 Финальная структура данных:")

    for split in ['train', 'val']:
        split_total = 0
        print(f"\n  {split.upper()}:")
        for cls in Config.CLASS_NAMES:
            cls_dir = os.path.join(Config.DATA_DIR, split, cls)
            if os.path.exists(cls_dir):
                count = len([f for f in os.listdir(cls_dir)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                print(f"    {cls}: {count} изображений")
                split_total += count
        print(f"    Всего: {split_total}")

    return True

# ================================================
# ДАТАСЕТ С ОБРАБОТКОЙ ПОВРЕЖДЕННЫХ ИЗОБРАЖЕНИЙ
# ================================================
class RobustWagonDataset(Dataset):
    """Надежный датасет с обработкой поврежденных изображений"""
    def __init__(self, data_dir, transform=None, mode='train'):
        self.image_paths = []
        self.labels = []
        self.transform = transform

        data_path = os.path.join(data_dir, mode)

        for class_idx, class_name in enumerate(Config.CLASS_NAMES):
            class_dir = os.path.join(data_path, class_name)
            if not os.path.exists(class_dir):
                print(f"⚠ Папка {class_dir} не найдена!")
                continue

            images = [f for f in os.listdir(class_dir)
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

            for img in images:
                self.image_paths.append(os.path.join(class_dir, img))
                self.labels.append(class_idx)

        print(f"✅ {mode.upper()}: загружено {len(self.image_paths)} изображений")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Загружаем изображение с обработкой ошибок
        img_path = self.image_paths[idx]

        # Пытаемся загрузить изображение
        image = load_image_safe(img_path)

        # Применяем трансформации
        if self.transform:
            image = self.transform(image)

        return image, self.labels[idx]

# ================================================
# МОДЕЛЬ
# ================================================
def create_simple_model():
    """Создание простой модели"""
    # Используем EfficientNet-B2 как компромисс между скоростью и точностью
    model = models.efficientnet_b2(weights='DEFAULT')

    # Заменяем классификатор
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, Config.NUM_CLASSES)
    )

    return model.to(Config.DEVICE)

# ================================================
# ОБУЧЕНИЕ (РАБОЧАЯ ВЕРСИЯ)
# ================================================
def train_simple_model():
    """Простая и рабочая функция обучения"""
    print("\n" + "="*60)
    print("🏋️‍♂️ НАЧИНАЕМ ОБУЧЕНИЕ")
    print("=" * 60)

    # Очищаем кэш GPU
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    Config.print_info()

    # Получаем трансформации
    train_transform, val_transform = get_transforms()

    # Создаем датасеты
    print("\n📥 Загрузка данных...")
    train_dataset = RobustWagonDataset(
        Config.DATA_DIR,
        transform=train_transform,
        mode='train'
    )

    val_dataset = RobustWagonDataset(
        Config.DATA_DIR,
        transform=val_transform,
        mode='val'
    )

    if len(train_dataset) == 0:
        print("❌ Обучающие данные не найдены!")
        return None, None

    # Создаем DataLoader
    train_loader = DataLoader(
        train_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=True,
        num_workers=0,  # 0 для Windows чтобы избежать проблем
        pin_memory=True if torch.cuda.is_available() else False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=False,
        num_workers=0,  # 0 для Windows чтобы избежать проблем
        pin_memory=True if torch.cuda.is_available() else False
    )

    # Создаем модель
    print("\n🧠 Создание модели...")
    model = create_simple_model()

    # Функция потерь и оптимизатор
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    # История обучения
    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': []
    }

    best_val_acc = 0.0

    print("\n" + "="*50)
    print("🏁 НАЧАЛО ОБУЧЕНИЯ")
    print("="*50)

    for epoch in range(Config.NUM_EPOCHS):
        print(f"\n📅 ЭПОХА {epoch + 1}/{Config.NUM_EPOCHS}")

        # ===== ОБУЧЕНИЕ =====
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        train_bar = tqdm(train_loader, desc='Training')
        for images, labels in train_bar:
            # Перемещаем данные на GPU
            images = images.to(Config.DEVICE)
            labels = labels.to(Config.DEVICE)

            # Forward pass
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)

            # Backward pass
            loss.backward()
            optimizer.step()

            # Статистика
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

            # Обновляем прогресс-бар
            train_bar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100.*train_correct/train_total:.1f}%'
            })

        # Средние значения за эпоху
        avg_train_loss = train_loss / len(train_loader)
        train_accuracy = train_correct / train_total

        # ===== ВАЛИДАЦИЯ =====
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        all_preds = []
        all_labels = []

        with torch.no_grad():
            val_bar = tqdm(val_loader, desc='Validation')
            for images, labels in val_bar:
                images = images.to(Config.DEVICE)
                labels = labels.to(Config.DEVICE)

                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        avg_val_loss = val_loss / len(val_loader)
        val_accuracy = val_correct / val_total

        # Обновляем scheduler
        scheduler.step()

        # Сохраняем историю
        history['train_loss'].append(avg_train_loss)
        history['train_acc'].append(train_accuracy)
        history['val_loss'].append(avg_val_loss)
        history['val_acc'].append(val_accuracy)

        # Сохраняем лучшую модель
        if val_accuracy > best_val_acc:
            best_val_acc = val_accuracy
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_accuracy,
                'train_acc': train_accuracy,
                'class_names': Config.CLASS_NAMES
            }, Config.MODEL_SAVE_PATH)
            print(f"💾 Сохранена лучшая модель! Точность: {val_accuracy:.4f}")

        # Выводим статистику
        print(f"📊 Результаты эпохи {epoch + 1}:")
        print(f"  Train Loss: {avg_train_loss:.4f}, Acc: {train_accuracy:.4f}")
        print(f"  Val Loss: {avg_val_loss:.4f}, Acc: {val_accuracy:.4f}")
        print(f"  LR: {scheduler.get_last_lr()[0]:.2e}")

    # ===== ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ =====
    print("\n📈 Визуализация результатов...")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # График потерь
    axes[0, 0].plot(history['train_loss'], label='Train', marker='o', linewidth=2)
    axes[0, 0].plot(history['val_loss'], label='Val', marker='s', linewidth=2)
    axes[0, 0].set_title('Loss History', fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # График точности
    axes[0, 1].plot(history['train_acc'], label='Train', marker='o', linewidth=2)
    axes[0, 1].plot(history['val_acc'], label='Val', marker='s', linewidth=2)
    axes[0, 1].set_title('Accuracy History', fontsize=14, fontweight='bold')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Confusion Matrix
    try:
        cm = confusion_matrix(all_labels, all_preds)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=Config.CLASS_NAMES,
                   yticklabels=Config.CLASS_NAMES,
                   ax=axes[1, 0])
        axes[1, 0].set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('Predicted')
        axes[1, 0].set_ylabel('True')
    except:
        axes[1, 0].text(0.5, 0.5, 'Confusion Matrix\nне доступна',
                       ha='center', va='center', fontsize=12)
        axes[1, 0].set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        axes[1, 0].axis('off')

    # Classification Report
    try:
        report = classification_report(all_labels, all_preds,
                                      target_names=Config.CLASS_NAMES)
        axes[1, 1].text(0, 1, report, fontsize=10, fontfamily='monospace',
                       verticalalignment='top', transform=axes[1, 1].transAxes)
    except:
        axes[1, 1].text(0.5, 0.5, 'Classification Report\nне доступен',
                       ha='center', va='center', fontsize=12)

    axes[1, 1].set_title('Classification Report', fontsize=14, fontweight='bold')
    axes[1, 1].axis('off')

    plt.tight_layout()
    results_path = os.path.join(os.getcwd(), 'training_results.png')
    plt.savefig(results_path, dpi=100, bbox_inches='tight')
    plt.show()

    # Выводим отчет по классификации
    print("\n" + "="*60)
    print("📋 ОТЧЕТ ПО КЛАССИФИКАЦИИ")
    print("="*60)
    try:
        print(classification_report(all_labels, all_preds,
                                  target_names=Config.CLASS_NAMES))
    except:
        print("Отчет не доступен")

    print("\n" + "="*60)
    print("🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    print(f"🏆 Лучшая точность на валидации: {best_val_acc:.4f}")
    print(f"💾 Модель сохранена: {Config.MODEL_SAVE_PATH}")
    print("\n📋 Классы модели:")
    for i, cls in enumerate(Config.CLASS_NAMES):
        print(f"  {i}: {cls}")

    return model, history

# ================================================
# ПРЕДСКАЗАНИЕ С ОБРАБОТКОЙ ПОВРЕЖДЕННЫХ ИЗОБРАЖЕНИЙ
# ================================================
def predict_single_image():
    """Предсказание для одного изображения с обработкой поврежденных файлов"""
    if not os.path.exists(Config.MODEL_SAVE_PATH):
        print("❌ Модель не обучена!")
        return

    print("\n📤 Введите путь к изображению для классификации...")
    image_path = input("Введите полный путь к изображению: ").strip()
    image_path = image_path.replace('/', '\\')
    
    if not os.path.exists(image_path):
        print(f"❌ Файл не найден: {image_path}")
        return

    print(f"✅ Изображение найдено: {os.path.basename(image_path)}")

    # Пытаемся восстановить поврежденное изображение
    print("🔧 Проверка целостности изображения...")
    repair_success = repair_image_file(image_path)
    if repair_success:
        print("✅ Изображение восстановлено")

    # Загружаем модель
    model = create_simple_model()
    checkpoint = torch.load(Config.MODEL_SAVE_PATH, map_location=Config.DEVICE)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # Получаем трансформации
    _, val_transform = get_transforms()

    # Загружаем и обрабатываем изображение
    try:
        # Используем безопасную загрузку
        print("🖼️ Загрузка изображения...")
        image = load_image_safe(image_path)

        # Проверяем, что изображение загрузилось
        if image is None:
            print("❌ Не удалось загрузить изображение")
            return None

        print(f"✅ Изображение загружено. Размер: {image.size}")

        # Применяем трансформации
        print("🔄 Применение трансформаций...")
        input_tensor = val_transform(image).unsqueeze(0).to(Config.DEVICE)

        # Предсказание
        print("🧠 Выполнение предсказания...")
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            predicted_idx = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_idx].item()

        predicted_class = Config.CLASS_NAMES[predicted_idx]

        # Выводим результат
        print("\n" + "="*60)
        print("🎯 РЕЗУЛЬТАТ КЛАССИФИКАЦИИ")
        print("="*60)
        print(f"📋 Класс: {predicted_class}")
        print(f"📊 Уверенность: {confidence:.2%}")
        print(f"\n📈 Распределение вероятностей:")
        for i, cls in enumerate(Config.CLASS_NAMES):
            prob = probabilities[0][i].item()
            prob_percent = prob * 100
            # Создаем прогресс-бар
            bar_length = 20
            filled_length = int(bar_length * prob)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            # Подсвечиваем предсказанный класс
            if i == predicted_idx:
                print(f"  ⭐ {cls}: {bar} {prob_percent:5.1f}% ({prob:.4f})")
            else:
                print(f"     {cls}: {bar} {prob_percent:5.1f}% ({prob:.4f})")

        # Визуализация
        plt.figure(figsize=(14, 6))

        # Изображение
        plt.subplot(1, 3, 1)
        plt.imshow(image)
        plt.title(f"Входное изображение\n{os.path.basename(image_path)}", fontsize=12)
        plt.axis('off')

        # График вероятностей
        plt.subplot(1, 3, 2)
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        probs = probabilities[0].cpu().numpy()

        bars = plt.bar(Config.CLASS_NAMES, probs, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        bars[predicted_idx].set_alpha(1.0)
        bars[predicted_idx].set_linewidth(3)
        bars[predicted_idx].set_edgecolor('red')

        plt.title(f"Предсказание: {predicted_class}\nУверенность: {confidence:.2%}",
                 fontsize=14, fontweight='bold')
        plt.ylim([0, 1.1])
        plt.ylabel('Вероятность', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')

        # Добавляем значения на столбцы
        for i, (bar, prob) in enumerate(zip(bars, probs)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{prob:.2%}', ha='center', va='bottom', fontsize=11,
                    fontweight='bold' if i == predicted_idx else 'normal',
                    color='red' if i == predicted_idx else 'black')

        # Тепловая карта вероятностей
        plt.subplot(1, 3, 3)
        prob_matrix = probabilities.cpu().numpy().reshape(-1, 1)
        plt.imshow(prob_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        plt.colorbar(label='Вероятность')
        plt.yticks(range(len(Config.CLASS_NAMES)), Config.CLASS_NAMES)
        plt.xticks([])
        plt.title('Тепловая карта вероятностей', fontsize=14, fontweight='bold')

        # Добавляем значения в ячейки
        for i, prob in enumerate(prob_matrix):
            plt.text(0, i, f'{prob[0]:.3f}', ha='center', va='center',
                    color='white' if prob[0] > 0.5 else 'black',
                    fontweight='bold' if i == predicted_idx else 'normal')

        plt.tight_layout()
        plt.show()

        # Дополнительная информация
        print("\n📝 ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТА:")
        if predicted_class == 'pered':
            print("  🚂 Передняя часть вагона обнаружена")
        elif predicted_class == 'zad':
            print("  🚂 Задняя часть вагона обнаружена")
        elif predicted_class == 'none':
            print("  ⭕ Вагон не обнаружен")

        if confidence > 0.9:
            print("  ✅ Высокая уверенность предсказания")
        elif confidence > 0.7:
            print("  ⚠ Средняя уверенность предсказания")
        else:
            print("  ❓ Низкая уверенность, возможно неоднозначное изображение")

        return predicted_class, confidence

    except Exception as e:
        print(f"\n❌ Критическая ошибка при обработке изображения: {e}")
        print("\n🔧 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
        print("  1. Попробуйте загрузить другое изображение")
        print("  2. Убедитесь, что файл не поврежден")
        print("  3. Проверьте формат файла (должен быть JPG, PNG)")

        import traceback
        traceback.print_exc()
        return None

# ================================================
# ПАКЕТНОЕ ТЕСТИРОВАНИЕ
# ================================================
def batch_test_images():
    """Тестирование модели на нескольких изображениях"""
    if not os.path.exists(Config.MODEL_SAVE_PATH):
        print("❌ Модель не обучена!")
        return

    print("\n📤 Введите путь к папке с изображениями для тестирования...")
    folder_path = input("Введите полный путь к папке: ").strip()
    folder_path = folder_path.replace('/', '\\')
    
    if not os.path.exists(folder_path):
        print(f"❌ Папка не найдена: {folder_path}")
        return

    # Получаем список изображений
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(folder_path) 
                   if f.lower().endswith(image_extensions)]
    
    if not image_files:
        print(f"❌ В папке нет изображений: {folder_path}")
        return

    print(f"✅ Найдено {len(image_files)} изображений")

    # Загружаем модель
    model = create_simple_model()
    checkpoint = torch.load(Config.MODEL_SAVE_PATH, map_location=Config.DEVICE)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # Получаем трансформации
    _, val_transform = get_transforms()

    results = []

    for image_name in image_files:
        print(f"\n🔍 Обработка: {image_name}")

        # Путь к изображению
        image_path = os.path.join(folder_path, image_name)

        try:
            # Безопасная загрузка
            image = load_image_safe(image_path)
            if image is None:
                print(f"  ❌ Не удалось загрузить {image_name}")
                continue

            # Предсказание
            input_tensor = val_transform(image).unsqueeze(0).to(Config.DEVICE)

            with torch.no_grad():
                outputs = model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                predicted_idx = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_idx].item()

            predicted_class = Config.CLASS_NAMES[predicted_idx]
            results.append((image_name, predicted_class, confidence))

            print(f"  ✅ {predicted_class} ({confidence:.2%})")

        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append((image_name, "ERROR", 0.0))

    # Выводим сводку
    print("\n" + "="*60)
    print("📊 СВОДКА ПО ТЕСТИРОВАНИЮ")
    print("="*60)

    if not results:
        print("❌ Нет результатов")
        return

    # Группируем по классам
    class_summary = {}
    for _, cls, conf in results:
        if cls not in class_summary:
            class_summary[cls] = []
        class_summary[cls].append(conf)

    print("\n📈 Статистика по классам:")
    for cls, confidences in class_summary.items():
        if cls == "ERROR":
            print(f"  ❌ Ошибки: {len(confidences)} изображений")
        else:
            avg_conf = np.mean(confidences) if confidences else 0
            print(f"  {cls}: {len(confidences)} изображений, средняя уверенность: {avg_conf:.2%}")

    # Подробные результаты
    print("\n📋 Подробные результаты:")
    for i, (img_name, cls, conf) in enumerate(results, 1):
        if cls == "ERROR":
            print(f"  {i:2d}. ❌ {img_name}")
        else:
            print(f"  {i:2d}. ✅ {img_name}: {cls} ({conf:.2%})")

    return results

# ================================================
# ГЛАВНОЕ МЕНЮ
# ================================================
def main_menu():
    """Главное меню"""
    print("\n" + "="*60)
    print("🚂 КЛАССИФИКАТОР ВАГОНОВ")
    print("="*60)
    print(f"📱 Устройство: {Config.DEVICE}")
    if Config.DEVICE.type == 'cuda':
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 Память: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    while True:
        print("\n" + "="*60)
        print("ГЛАВНОЕ МЕНЮ:")
        print("1. 📊 Подготовить данные")
        print("2. 🏋️‍♂️ Обучить модель")
        print("3. 🔍 Протестировать одно изображение")
        print("4. 📦 Протестировать несколько изображений")
        print("5. 📈 Показать графики")
        print("6. 🧹 Очистить кэш")
        print("0. ❌ Выход")
        print("="*60)

        choice = input("\nВыберите действие (0-6): ").strip()

        if choice == '1':
            # Подготовка данных
            print("\n" + "="*60)
            print("ПОДГОТОВКА ДАННЫХ")
            print("="*60)

            success = prepare_data_simple()
            if success:
                print("\n✅ Данные готовы к обучению!")
            else:
                print("\n❌ Ошибка при подготовке данных")

        elif choice == '2':
            # Обучение модели
            if not os.path.exists(Config.DATA_DIR):
                print("\n❌ Данные не подготовлены! Сначала выполните шаг 1.")
                continue

            try:
                model, history = train_simple_model()
                if model is not None:
                    print("\n✅ Обучение успешно завершено!")
            except Exception as e:
                print(f"\n❌ Ошибка при обучении: {e}")
                import traceback
                traceback.print_exc()

        elif choice == '3':
            # Тестирование одного изображения
            if not os.path.exists(Config.MODEL_SAVE_PATH):
                print("\n❌ Модель не обучена! Сначала выполните шаг 2.")
                continue

            try:
                result = predict_single_image()
                if result:
                    print("\n✅ Предсказание выполнено успешно!")
            except Exception as e:
                print(f"\n❌ Ошибка при предсказании: {e}")

        elif choice == '4':
            # Пакетное тестирование
            if not os.path.exists(Config.MODEL_SAVE_PATH):
                print("\n❌ Модель не обучена! Сначала выполните шаг 2.")
                continue

            try:
                results = batch_test_images()
                if results:
                    print("\n✅ Пакетное тестирование завершено!")
            except Exception as e:
                print(f"\n❌ Ошибка при пакетном тестировании: {e}")

        elif choice == '5':
            # Показать графики
            results_path = os.path.join(os.getcwd(), 'training_results.png')
            if os.path.exists(results_path):
                print("\n📊 Графики обучения:")
                try:
                    img = plt.imread(results_path)
                    plt.figure(figsize=(12, 8))
                    plt.imshow(img)
                    plt.axis('off')
                    plt.show()
                except Exception as e:
                    print(f"❌ Ошибка при загрузке графиков: {e}")
            else:
                print("\n❌ Графики не найдены. Сначала обучите модель.")

        elif choice == '6':
            # Очистка кэша
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("✅ Кэш GPU очищен!")
            else:
                print("⚠ GPU не доступна")

        elif choice == '0':
            print("\n👋 До свидания!")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            break

        else:
            print("\n❌ Неверный выбор. Пожалуйста, выберите от 0 до 6.")

# ================================================
# ЗАПУСК
# ================================================
if __name__ == "__main__":
    print("🚂 КЛАССИФИКАТОР ВАГОНОВ ДЛЯ WINDOWS 10")
    print("=" * 60)
    print("📦 Зависимости:")
    print("Установите библиотеки из файла requirements.txt:")
    print("pip install -r requirements.txt")
    print("=" * 60)
    
    # Запускаем меню
    main_menu()