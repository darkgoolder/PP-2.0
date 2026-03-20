# import torch
# import torch.nn as nn
# import torch.optim as optim
# from torch.utils.data import DataLoader, Dataset
# from torchvision import models, transforms
# import torch.cuda.amp as amp  # Для mixed precision training
# import os
# import shutil
# import numpy as np
# from PIL import Image, ImageFile
# import matplotlib.pyplot as plt
# from tqdm import tqdm
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import confusion_matrix, classification_report
# import seaborn as sns
# import warnings
# warnings.filterwarnings('ignore')

# # ================================================
# # ВКЛЮЧАЕМ ОБРАБОТКУ УСЕЧЕННЫХ ИЗОБРАЖЕНИЙ
# # ================================================
# ImageFile.LOAD_TRUNCATED_IMAGES = True

# # ================================================
# # КОНФИГУРАЦИЯ С УЛУЧШЕННОЙ ПОДДЕРЖКОЙ CUDA
# # ================================================
# class Config:
#     # Пути
#     BASE_DIR = os.path.join(os.getcwd(), 'wagon_classification')
#     DATA_DIR = os.path.join(os.getcwd(), 'wagon_classification', 'data', 'processed')
#     EXTRACTED_DIR = os.path.join(os.getcwd(), 'wagon_data', 'extracted')
#     MODEL_SAVE_PATH = os.path.join(os.getcwd(), 'wagon_classification', 'best_model.pth')

#     # Классы
#     CLASS_NAMES = ['pered', 'zad', 'none']
#     NUM_CLASSES = 3

#     # Гиперпараметры - увеличены для GPU
#     BATCH_SIZE = 64 if torch.cuda.is_available() else 32  # Увеличиваем для GPU
#     NUM_EPOCHS = 20
#     NUM_WORKERS = 4 if torch.cuda.is_available() else 0  # Параллельная загрузка для GPU
#     PIN_MEMORY = True if torch.cuda.is_available() else False  # Ускорение передачи на GPU

#     # Mixed precision training
#     USE_AMP = True if torch.cuda.is_available() else False  # Используем AMP только на GPU

#     # Устройство
#     DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#     @staticmethod
#     def print_info():
#         print(f"\n📊 КОНФИГУРАЦИЯ:")
#         print(f"  • Устройство: {Config.DEVICE}")
#         if Config.DEVICE.type == 'cuda':
#             print(f"  • GPU: {torch.cuda.get_device_name(0)}")
#             print(f"  • Память GPU: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
#             print(f"  • CUDA версия: {torch.version.cuda}")
#             print(f"  • PyTorch версия: {torch.__version__}")
#             print(f"  • Используем AMP: {Config.USE_AMP}")
#         print(f"  • Классы: {Config.CLASS_NAMES}")
#         print(f"  • Batch size: {Config.BATCH_SIZE}")
#         print(f"  • Workers: {Config.NUM_WORKERS}")
#         print(f"  • Pin memory: {Config.PIN_MEMORY}")
#         print(f"  • Эпох: {Config.NUM_EPOCHS}")

# # ================================================
# # УТИЛИТЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ
# # ================================================
# def load_image_safe(image_path, target_size=(224, 224)):
#     """Безопасная загрузка изображения с обработкой ошибок"""
#     try:
#         image = Image.open(image_path)
#         image.verify()
#         image = Image.open(image_path)

#         if image.mode != 'RGB':
#             image = image.convert('RGB')

#         if image.size[0] == 0 or image.size[1] == 0:
#             print(f"⚠ Изображение {image_path} имеет нулевые размеры")
#             image = Image.new('RGB', target_size, color='black')

#         return image

#     except Exception as e:
#         print(f"⚠ Ошибка загрузки {image_path}: {e}")
#         return Image.new('RGB', target_size, color='black')

# def repair_image_file(image_path):
#     """Пытается восстановить поврежденный файл изображения"""
#     try:
#         with open(image_path, 'rb') as f:
#             data = f.read()

#         if len(data) == 0:
#             print(f"❌ Файл {image_path} пустой")
#             return False

#         if image_path.lower().endswith(('.jpg', '.jpeg')):
#             if not data.endswith(b'\xff\xd9'):
#                 print(f"⚠ Восстанавливаю JPEG файл {image_path}")
#                 data += b'\xff\xd9'
#                 with open(image_path, 'wb') as f:
#                     f.write(data)
#                 return True

#         return False

#     except Exception as e:
#         print(f"❌ Ошибка при восстановлении {image_path}: {e}")
#         return False

# # ================================================
# # ТРАНСФОРМАЦИИ
# # ================================================
# def get_transforms():
#     """Создание трансформаций"""
#     train_transform = transforms.Compose([
#         transforms.Resize((256, 256)),
#         transforms.RandomCrop(224),
#         transforms.RandomHorizontalFlip(p=0.5),
#         transforms.ColorJitter(brightness=0.2, contrast=0.2),
#         transforms.ToTensor(),
#         transforms.Normalize(mean=[0.485, 0.456, 0.406],
#                            std=[0.229, 0.224, 0.225])
#     ])

#     val_transform = transforms.Compose([
#         transforms.Resize((224, 224)),
#         transforms.ToTensor(),
#         transforms.Normalize(mean=[0.485, 0.456, 0.406],
#                            std=[0.229, 0.224, 0.225])
#     ])

#     return train_transform, val_transform

# # ================================================
# # ПОДГОТОВКА ДАННЫХ
# # ================================================
# def prepare_data_simple():
#     """Упрощенная подготовка данных"""
#     print("=" * 60)
#     print("📊 ПОДГОТОВКА ДАННЫХ")
#     print("=" * 60)

#     os.makedirs(Config.BASE_DIR, exist_ok=True)
#     os.makedirs(Config.EXTRACTED_DIR, exist_ok=True)
#     os.makedirs(Config.DATA_DIR, exist_ok=True)

#     print("\n📤 ШАГ 1: Укажите путь к архиву vagon1.rar")
#     print("Пример: C:/Users/Username/Downloads/vagon1.rar")
#     archive_path = input("Введите полный путь к архиву: ").strip()
    
#     archive_path = archive_path.replace('/', '\\')
    
#     if not os.path.exists(archive_path):
#         print(f"\n❌ Файл не найден: {archive_path}")
#         return False

#     print(f"\n✅ Найден архив: {os.path.basename(archive_path)}")

#     try:
#         import patoolib
#         print("📦 Распаковка архива...")
#         patoolib.extract_archive(archive_path, outdir=Config.EXTRACTED_DIR)
#         print("✅ Архив распакован")
#     except ImportError:
#         print("⚠ Установите библиотеку patool: pip install patool")
#         return False
#     except Exception as e:
#         print(f"⚠ Ошибка при распаковке: {e}")
#         return False

#     print("\n🔍 Проверка данных...")

#     possible_folders = {
#         'pered': ['pered', 'prered', 'peredn', 'peredniy', 'front', 'перед'],
#         'zad': ['zad', 'zadn', 'zadniy', 'back', 'rear', 'зад'],
#         'none': ['none', 'non', 'empty', 'нет', 'пусто']
#     }

#     actual_folders = os.listdir(Config.EXTRACTED_DIR)
#     print(f"Найдены папки в extracted: {actual_folders}")

#     folder_mapping = {}
#     for target_class, possible_names in possible_folders.items():
#         for folder in actual_folders:
#             folder_lower = folder.lower()
#             if any(name in folder_lower for name in possible_names):
#                 folder_mapping[target_class] = folder
#                 print(f"  ✓ {target_class} → {folder}")
#                 break

#     if len(folder_mapping) < len(Config.CLASS_NAMES):
#         missing = [c for c in Config.CLASS_NAMES if c not in folder_mapping]
#         print(f"\n❌ Отсутствуют классы: {missing}")
#         return False

#     print("\n📁 Создание структуры train/val...")
#     for split in ['train', 'val']:
#         for cls in Config.CLASS_NAMES:
#             os.makedirs(os.path.join(Config.DATA_DIR, split, cls), exist_ok=True)

#     print("📊 Разделение на train/val (80/20)...")
#     total_images = 0

#     for target_class, source_folder in folder_mapping.items():
#         source_dir = os.path.join(Config.EXTRACTED_DIR, source_folder)

#         if not os.path.exists(source_dir):
#             continue

#         images = [f for f in os.listdir(source_dir)
#                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

#         if not images:
#             continue

#         print(f"\n📂 Обрабатываем {source_folder} → {target_class}:")
#         print(f"  Найдено {len(images)} изображений")

#         train_imgs, val_imgs = train_test_split(
#             images, test_size=0.2, random_state=42
#         )

#         print(f"  Копируем {len(train_imgs)} в train...")
#         for img in tqdm(train_imgs, desc=f"  {target_class} train"):
#             src = os.path.join(source_dir, img)
#             dst = os.path.join(Config.DATA_DIR, 'train', target_class, img)
#             shutil.copy2(src, dst)

#         print(f"  Копируем {len(val_imgs)} в val...")
#         for img in tqdm(val_imgs, desc=f"  {target_class} val"):
#             src = os.path.join(source_dir, img)
#             dst = os.path.join(Config.DATA_DIR, 'val', target_class, img)
#             shutil.copy2(src, dst)

#         total_images += len(images)

#     print(f"\n✅ Готово! Всего {total_images} изображений")
#     return True

# # ================================================
# # ДАТАСЕТ
# # ================================================
# class RobustWagonDataset(Dataset):
#     """Надежный датасет с обработкой поврежденных изображений"""
#     def __init__(self, data_dir, transform=None, mode='train'):
#         self.image_paths = []
#         self.labels = []
#         self.transform = transform

#         data_path = os.path.join(data_dir, mode)

#         for class_idx, class_name in enumerate(Config.CLASS_NAMES):
#             class_dir = os.path.join(data_path, class_name)
#             if not os.path.exists(class_dir):
#                 print(f"⚠ Папка {class_dir} не найдена!")
#                 continue

#             images = [f for f in os.listdir(class_dir)
#                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

#             for img in images:
#                 self.image_paths.append(os.path.join(class_dir, img))
#                 self.labels.append(class_idx)

#         print(f"✅ {mode.upper()}: загружено {len(self.image_paths)} изображений")

#     def __len__(self):
#         return len(self.image_paths)

#     def __getitem__(self, idx):
#         img_path = self.image_paths[idx]
#         image = load_image_safe(img_path)

#         if self.transform:
#             image = self.transform(image)

#         return image, self.labels[idx]

# # ================================================
# # МОДЕЛЬ
# # ================================================
# def create_simple_model():
#     """Создание модели с поддержкой GPU"""
#     # Используем EfficientNet-B2
#     model = models.efficientnet_b2(weights='DEFAULT')

#     # Заменяем классификатор
#     in_features = model.classifier[1].in_features
#     model.classifier = nn.Sequential(
#         nn.Dropout(p=0.3),
#         nn.Linear(in_features, Config.NUM_CLASSES)
#     )

#     # Перемещаем на устройство
#     model = model.to(Config.DEVICE)

#     # Если несколько GPU, используем DataParallel
#     if torch.cuda.is_available() and torch.cuda.device_count() > 1:
#         print(f"📦 Используем {torch.cuda.device_count()} GPU!")
#         model = nn.DataParallel(model)

#     return model

# # ================================================
# # ОБУЧЕНИЕ С ПОДДЕРЖКОЙ CUDA И MIXED PRECISION
# # ================================================
# def train_simple_model():
#     """Обучение с оптимизацией для GPU"""
#     print("\n" + "="*60)
#     print("🏋️‍♂️ НАЧИНАЕМ ОБУЧЕНИЕ")
#     print("=" * 60)

#     # Очищаем кэш GPU перед началом
#     if torch.cuda.is_available():
#         torch.cuda.empty_cache()
#         torch.cuda.reset_peak_memory_stats()

#     Config.print_info()

#     # Получаем трансформации
#     train_transform, val_transform = get_transforms()

#     # Создаем датасеты
#     print("\n📥 Загрузка данных...")
#     train_dataset = RobustWagonDataset(
#         Config.DATA_DIR,
#         transform=train_transform,
#         mode='train'
#     )

#     val_dataset = RobustWagonDataset(
#         Config.DATA_DIR,
#         transform=val_transform,
#         mode='val'
#     )

#     if len(train_dataset) == 0:
#         print("❌ Обучающие данные не найдены!")
#         return None, None

#     # Создаем DataLoader с оптимизациями для GPU
#     train_loader = DataLoader(
#         train_dataset,
#         batch_size=Config.BATCH_SIZE,
#         shuffle=True,
#         num_workers=Config.NUM_WORKERS,
#         pin_memory=Config.PIN_MEMORY,
#         persistent_workers=True if Config.NUM_WORKERS > 0 else False
#     )

#     val_loader = DataLoader(
#         val_dataset,
#         batch_size=Config.BATCH_SIZE,
#         shuffle=False,
#         num_workers=Config.NUM_WORKERS,
#         pin_memory=Config.PIN_MEMORY,
#         persistent_workers=True if Config.NUM_WORKERS > 0 else False
#     )

#     # Создаем модель
#     print("\n🧠 Создание модели...")
#     model = create_simple_model()

#     # Функция потерь и оптимизатор
#     criterion = nn.CrossEntropyLoss()
#     optimizer = optim.Adam(model.parameters(), lr=1e-4)

#     # Learning rate scheduler
#     scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

#     # Mixed precision scaler для GPU
#     scaler = amp.GradScaler(enabled=Config.USE_AMP)

#     # История обучения
#     history = {
#         'train_loss': [], 'train_acc': [],
#         'val_loss': [], 'val_acc': []
#     }

#     best_val_acc = 0.0

#     print("\n" + "="*50)
#     print("🏁 НАЧАЛО ОБУЧЕНИЯ")
#     print("="*50)

#     for epoch in range(Config.NUM_EPOCHS):
#         print(f"\n📅 ЭПОХА {epoch + 1}/{Config.NUM_EPOCHS}")

#         # ===== ОБУЧЕНИЕ =====
#         model.train()
#         train_loss = 0.0
#         train_correct = 0
#         train_total = 0

#         train_bar = tqdm(train_loader, desc='Training')
#         for images, labels in train_bar:
#             # Перемещаем данные на GPU (если используем pin_memory, это быстрее)
#             images = images.to(Config.DEVICE, non_blocking=True)
#             labels = labels.to(Config.DEVICE, non_blocking=True)

#             optimizer.zero_grad()

#             # Mixed precision forward/backward
#             with torch.cuda.amp.autocast(enabled=Config.USE_AMP):
#                 outputs = model(images)
#                 loss = criterion(outputs, labels)

#             # Backward pass со scaler для AMP
#             scaler.scale(loss).backward()
#             scaler.step(optimizer)
#             scaler.update()

#             # Статистика
#             train_loss += loss.item()
#             _, predicted = outputs.max(1)
#             train_total += labels.size(0)
#             train_correct += predicted.eq(labels).sum().item()

#             # Обновляем прогресс-бар
#             train_bar.set_postfix({
#                 'Loss': f'{loss.item():.4f}',
#                 'Acc': f'{100.*train_correct/train_total:.1f}%'
#             })

#         # Средние значения за эпоху
#         avg_train_loss = train_loss / len(train_loader)
#         train_accuracy = train_correct / train_total

#         # ===== ВАЛИДАЦИЯ =====
#         model.eval()
#         val_loss = 0.0
#         val_correct = 0
#         val_total = 0
#         all_preds = []
#         all_labels = []

#         with torch.no_grad():
#             val_bar = tqdm(val_loader, desc='Validation')
#             for images, labels in val_bar:
#                 images = images.to(Config.DEVICE, non_blocking=True)
#                 labels = labels.to(Config.DEVICE, non_blocking=True)

#                 with torch.cuda.amp.autocast(enabled=Config.USE_AMP):
#                     outputs = model(images)
#                     loss = criterion(outputs, labels)

#                 val_loss += loss.item()
#                 _, predicted = outputs.max(1)
#                 val_total += labels.size(0)
#                 val_correct += predicted.eq(labels).sum().item()

#                 # Перемещаем на CPU для метрик
#                 all_preds.extend(predicted.cpu().numpy())
#                 all_labels.extend(labels.cpu().numpy())

#         avg_val_loss = val_loss / len(val_loader)
#         val_accuracy = val_correct / val_total

#         # Обновляем scheduler
#         scheduler.step()

#         # Сохраняем историю
#         history['train_loss'].append(avg_train_loss)
#         history['train_acc'].append(train_accuracy)
#         history['val_loss'].append(avg_val_loss)
#         history['val_acc'].append(val_accuracy)

#         # Сохраняем лучшую модель
#         if val_accuracy > best_val_acc:
#             best_val_acc = val_accuracy
#             # Сохраняем на CPU для совместимости
#             torch.save({
#                 'epoch': epoch,
#                 'model_state_dict': model.module.state_dict() if hasattr(model, 'module') else model.state_dict(),
#                 'optimizer_state_dict': optimizer.state_dict(),
#                 'val_acc': val_accuracy,
#                 'train_acc': train_accuracy,
#                 'class_names': Config.CLASS_NAMES
#             }, Config.MODEL_SAVE_PATH)
#             print(f"💾 Сохранена лучшая модель! Точность: {val_accuracy:.4f}")

#         # Выводим статистику
#         print(f"📊 Результаты эпохи {epoch + 1}:")
#         print(f"  Train Loss: {avg_train_loss:.4f}, Acc: {train_accuracy:.4f}")
#         print(f"  Val Loss: {avg_val_loss:.4f}, Acc: {val_accuracy:.4f}")
#         print(f"  LR: {scheduler.get_last_lr()[0]:.2e}")

#         # Показываем использование памяти GPU
#         if torch.cuda.is_available():
#             allocated = torch.cuda.memory_allocated(0) / 1024**2
#             cached = torch.cuda.memory_reserved(0) / 1024**2
#             print(f"  GPU память: {allocated:.0f}MB / {cached:.0f}MB")

#     # ===== ВИЗУАЛИЗАЦИЯ =====
#     print("\n📈 Визуализация результатов...")
#     plot_training_results(history, all_labels, all_preds)

#     print("\n" + "="*60)
#     print("🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!")
#     print("="*60)
#     print(f"🏆 Лучшая точность на валидации: {best_val_acc:.4f}")
#     print(f"💾 Модель сохранена: {Config.MODEL_SAVE_PATH}")

#     return model, history

# def plot_training_results(history, all_labels, all_preds):
#     """Визуализация результатов обучения"""
#     fig, axes = plt.subplots(2, 2, figsize=(12, 10))

#     # График потерь
#     axes[0, 0].plot(history['train_loss'], label='Train', marker='o', linewidth=2)
#     axes[0, 0].plot(history['val_loss'], label='Val', marker='s', linewidth=2)
#     axes[0, 0].set_title('Loss History', fontsize=14, fontweight='bold')
#     axes[0, 0].set_xlabel('Epoch')
#     axes[0, 0].set_ylabel('Loss')
#     axes[0, 0].legend()
#     axes[0, 0].grid(True, alpha=0.3)

#     # График точности
#     axes[0, 1].plot(history['train_acc'], label='Train', marker='o', linewidth=2)
#     axes[0, 1].plot(history['val_acc'], label='Val', marker='s', linewidth=2)
#     axes[0, 1].set_title('Accuracy History', fontsize=14, fontweight='bold')
#     axes[0, 1].set_xlabel('Epoch')
#     axes[0, 1].set_ylabel('Accuracy')
#     axes[0, 1].legend()
#     axes[0, 1].grid(True, alpha=0.3)

#     # Confusion Matrix
#     try:
#         cm = confusion_matrix(all_labels, all_preds)
#         sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
#                    xticklabels=Config.CLASS_NAMES,
#                    yticklabels=Config.CLASS_NAMES,
#                    ax=axes[1, 0])
#         axes[1, 0].set_title('Confusion Matrix', fontsize=14, fontweight='bold')
#         axes[1, 0].set_xlabel('Predicted')
#         axes[1, 0].set_ylabel('True')
#     except:
#         axes[1, 0].text(0.5, 0.5, 'Confusion Matrix\nне доступна',
#                        ha='center', va='center', fontsize=12)

#     # Classification Report
#     try:
#         report = classification_report(all_labels, all_preds,
#                                       target_names=Config.CLASS_NAMES)
#         axes[1, 1].text(0, 1, report, fontsize=10, fontfamily='monospace',
#                        verticalalignment='top', transform=axes[1, 1].transAxes)
#     except:
#         axes[1, 1].text(0.5, 0.5, 'Classification Report\nне доступен',
#                        ha='center', va='center', fontsize=12)

#     axes[1, 1].set_title('Classification Report', fontsize=14, fontweight='bold')
#     axes[1, 1].axis('off')

#     plt.tight_layout()
#     results_path = os.path.join(os.getcwd(), 'training_results.png')
#     plt.savefig(results_path, dpi=100, bbox_inches='tight')
#     plt.show()

# # ================================================
# # ПРЕДСКАЗАНИЕ
# # ================================================
# def predict_single_image():
#     """Предсказание для одного изображения"""
#     if not os.path.exists(Config.MODEL_SAVE_PATH):
#         print("❌ Модель не обучена!")
#         return

#     print("\n📤 Введите путь к изображению...")
#     image_path = input("Введите полный путь к изображению: ").strip()
#     image_path = image_path.replace('/', '\\')
    
#     if not os.path.exists(image_path):
#         print(f"❌ Файл не найден: {image_path}")
#         return

#     print(f"✅ Изображение найдено: {os.path.basename(image_path)}")

#     print("🔧 Проверка целостности изображения...")
#     repair_image_file(image_path)

#     # Загружаем модель
#     model = create_simple_model()
#     checkpoint = torch.load(Config.MODEL_SAVE_PATH, map_location=Config.DEVICE)
    
#     # Убираем 'module.' если модель сохранена с DataParallel
#     state_dict = checkpoint['model_state_dict']
#     if list(state_dict.keys())[0].startswith('module.') and not hasattr(model, 'module'):
#         from collections import OrderedDict
#         new_state_dict = OrderedDict()
#         for k, v in state_dict.items():
#             name = k[7:]  # убираем 'module.'
#             new_state_dict[name] = v
#         state_dict = new_state_dict
    
#     model.load_state_dict(state_dict)
#     model.eval()

#     _, val_transform = get_transforms()

#     try:
#         print("🖼️ Загрузка изображения...")
#         image = load_image_safe(image_path)

#         print(f"✅ Изображение загружено. Размер: {image.size}")

#         print("🔄 Применение трансформаций...")
#         input_tensor = val_transform(image).unsqueeze(0)

#         # Перемещаем на GPU
#         input_tensor = input_tensor.to(Config.DEVICE, non_blocking=True)

#         print("🧠 Выполнение предсказания...")
#         with torch.no_grad(), torch.cuda.amp.autocast(enabled=Config.USE_AMP):
#             outputs = model(input_tensor)
#             probabilities = torch.nn.functional.softmax(outputs, dim=1)

#         # Перемещаем обратно на CPU для отображения
#         probabilities = probabilities.cpu()
#         predicted_idx = torch.argmax(probabilities, dim=1).item()
#         confidence = probabilities[0][predicted_idx].item()

#         predicted_class = Config.CLASS_NAMES[predicted_idx]

#         # Выводим результат
#         print("\n" + "="*60)
#         print("🎯 РЕЗУЛЬТАТ КЛАССИФИКАЦИИ")
#         print("="*60)
#         print(f"📋 Класс: {predicted_class}")
#         print(f"📊 Уверенность: {confidence:.2%}")

#         # Визуализация
#         plot_prediction_result(image, predicted_class, confidence, probabilities, image_path)

#         return predicted_class, confidence

#     except Exception as e:
#         print(f"\n❌ Критическая ошибка: {e}")
#         import traceback
#         traceback.print_exc()
#         return None

# def plot_prediction_result(image, predicted_class, confidence, probabilities, image_path):
#     """Визуализация результата предсказания"""
#     plt.figure(figsize=(14, 6))

#     # Изображение
#     plt.subplot(1, 3, 1)
#     plt.imshow(image)
#     plt.title(f"Входное изображение\n{os.path.basename(image_path)}", fontsize=12)
#     plt.axis('off')

#     # График вероятностей
#     plt.subplot(1, 3, 2)
#     colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
#     probs = probabilities[0].numpy()
#     predicted_idx = Config.CLASS_NAMES.index(predicted_class)

#     bars = plt.bar(Config.CLASS_NAMES, probs, color=colors, alpha=0.7, 
#                    edgecolor='black', linewidth=2)
#     bars[predicted_idx].set_alpha(1.0)
#     bars[predicted_idx].set_linewidth(3)
#     bars[predicted_idx].set_edgecolor('red')

#     plt.title(f"Предсказание: {predicted_class}\nУверенность: {confidence:.2%}",
#              fontsize=14, fontweight='bold')
#     plt.ylim([0, 1.1])
#     plt.ylabel('Вероятность', fontsize=12)
#     plt.grid(True, alpha=0.3, axis='y')

#     for i, (bar, prob) in enumerate(zip(bars, probs)):
#         plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
#                 f'{prob:.2%}', ha='center', va='bottom', fontsize=11,
#                 fontweight='bold' if i == predicted_idx else 'normal',
#                 color='red' if i == predicted_idx else 'black')

#     # Тепловая карта
#     plt.subplot(1, 3, 3)
#     prob_matrix = probs.reshape(-1, 1)
#     plt.imshow(prob_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
#     plt.colorbar(label='Вероятность')
#     plt.yticks(range(len(Config.CLASS_NAMES)), Config.CLASS_NAMES)
#     plt.xticks([])
#     plt.title('Тепловая карта вероятностей', fontsize=14, fontweight='bold')

#     for i, prob in enumerate(prob_matrix):
#         plt.text(0, i, f'{prob[0]:.3f}', ha='center', va='center',
#                 color='white' if prob[0] > 0.5 else 'black',
#                 fontweight='bold' if i == predicted_idx else 'normal')

#     plt.tight_layout()
#     plt.show()

# # ================================================
# # ПАКЕТНОЕ ТЕСТИРОВАНИЕ
# # ================================================
# def batch_test_images():
#     """Тестирование модели на нескольких изображениях"""
#     if not os.path.exists(Config.MODEL_SAVE_PATH):
#         print("❌ Модель не обучена!")
#         return

#     print("\n📤 Введите путь к папке с изображениями...")
#     folder_path = input("Введите полный путь к папке: ").strip()
#     folder_path = folder_path.replace('/', '\\')
    
#     if not os.path.exists(folder_path):
#         print(f"❌ Папка не найдена: {folder_path}")
#         return

#     image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
#     image_files = [f for f in os.listdir(folder_path) 
#                    if f.lower().endswith(image_extensions)]
    
#     if not image_files:
#         print(f"❌ В папке нет изображений")
#         return

#     print(f"✅ Найдено {len(image_files)} изображений")

#     # Загружаем модель
#     model = create_simple_model()
#     checkpoint = torch.load(Config.MODEL_SAVE_PATH, map_location=Config.DEVICE)
    
#     # Убираем 'module.' если модель сохранена с DataParallel
#     state_dict = checkpoint['model_state_dict']
#     if list(state_dict.keys())[0].startswith('module.') and not hasattr(model, 'module'):
#         from collections import OrderedDict
#         new_state_dict = OrderedDict()
#         for k, v in state_dict.items():
#             name = k[7:]
#             new_state_dict[name] = v
#         state_dict = new_state_dict
    
#     model.load_state_dict(state_dict)
#     model.eval()

#     _, val_transform = get_transforms()

#     results = []

#     for image_name in tqdm(image_files, desc="Обработка"):
#         image_path = os.path.join(folder_path, image_name)

#         try:
#             image = load_image_safe(image_path)
#             if image is None:
#                 results.append((image_name, "ERROR", 0.0))
#                 continue

#             # Предсказание на GPU
#             input_tensor = val_transform(image).unsqueeze(0).to(Config.DEVICE, non_blocking=True)

#             with torch.no_grad(), torch.cuda.amp.autocast(enabled=Config.USE_AMP):
#                 outputs = model(input_tensor)
#                 probabilities = torch.nn.functional.softmax(outputs, dim=1).cpu()

#             predicted_idx = torch.argmax(probabilities, dim=1).item()
#             confidence = probabilities[0][predicted_idx].item()
#             predicted_class = Config.CLASS_NAMES[predicted_idx]

#             results.append((image_name, predicted_class, confidence))

#         except Exception as e:
#             print(f"\n❌ Ошибка с {image_name}: {e}")
#             results.append((image_name, "ERROR", 0.0))

#     # Выводим сводку
#     print("\n" + "="*60)
#     print("📊 СВОДКА ПО ТЕСТИРОВАНИЮ")
#     print("="*60)

#     if not results:
#         print("❌ Нет результатов")
#         return

#     # Группируем по классам
#     class_summary = {}
#     for _, cls, conf in results:
#         if cls not in class_summary:
#             class_summary[cls] = []
#         class_summary[cls].append(conf)

#     print("\n📈 Статистика по классам:")
#     for cls, confidences in class_summary.items():
#         if cls == "ERROR":
#             print(f"  ❌ Ошибки: {len(confidences)} изображений")
#         else:
#             avg_conf = np.mean(confidences) if confidences else 0
#             print(f"  {cls}: {len(confidences)} изображений, средняя уверенность: {avg_conf:.2%}")

#     return results

# # ================================================
# # ГЛАВНОЕ МЕНЮ
# # ================================================
# def main_menu():
#     """Главное меню"""
#     print("\n" + "="*60)
#     print("🚂 КЛАССИФИКАТОР ВАГОНОВ (CUDA OPTIMIZED)")
#     print("="*60)
    
#     Config.print_info()

#     while True:
#         print("\n" + "="*60)
#         print("ГЛАВНОЕ МЕНЮ:")
#         print("1. 📊 Подготовить данные")
#         print("2. 🏋️‍♂️ Обучить модель (с поддержкой GPU)")
#         print("3. 🔍 Протестировать одно изображение")
#         print("4. 📦 Протестировать несколько изображений")
#         print("5. 📈 Показать графики")
#         print("6. 🧹 Очистить кэш GPU")
#         print("7. ℹ️ Информация о GPU")
#         print("0. ❌ Выход")
#         print("="*60)

#         choice = input("\nВыберите действие (0-7): ").strip()

#         if choice == '1':
#             print("\n" + "="*60)
#             print("ПОДГОТОВКА ДАННЫХ")
#             print("="*60)
#             prepare_data_simple()

#         elif choice == '2':
#             if not os.path.exists(Config.DATA_DIR):
#                 print("\n❌ Данные не подготовлены! Сначала выполните шаг 1.")
#                 continue

#             try:
#                 model, history = train_simple_model()
#                 if model is not None:
#                     print("\n✅ Обучение успешно завершено!")
#             except Exception as e:
#                 print(f"\n❌ Ошибка при обучении: {e}")
#                 import traceback
#                 traceback.print_exc()

#         elif choice == '3':
#             if not os.path.exists(Config.MODEL_SAVE_PATH):
#                 print("\n❌ Модель не обучена! Сначала выполните шаг 2.")
#                 continue

#             try:
#                 predict_single_image()
#             except Exception as e:
#                 print(f"\n❌ Ошибка при предсказании: {e}")

#         elif choice == '4':
#             if not os.path.exists(Config.MODEL_SAVE_PATH):
#                 print("\n❌ Модель не обучена! Сначала выполните шаг 2.")
#                 continue

#             try:
#                 batch_test_images()
#             except Exception as e:
#                 print(f"\n❌ Ошибка при пакетном тестировании: {e}")

#         elif choice == '5':
#             results_path = os.path.join(os.getcwd(), 'training_results.png')
#             if os.path.exists(results_path):
#                 print("\n📊 Графики обучения:")
#                 try:
#                     img = plt.imread(results_path)
#                     plt.figure(figsize=(12, 8))
#                     plt.imshow(img)
#                     plt.axis('off')
#                     plt.show()
#                 except Exception as e:
#                     print(f"❌ Ошибка при загрузке графиков: {e}")
#             else:
#                 print("\n❌ Графики не найдены. Сначала обучите модель.")

#         elif choice == '6':
#             if torch.cuda.is_available():
#                 torch.cuda.empty_cache()
#                 print("✅ Кэш GPU очищен!")
#                 print(f"📊 Свободно: {torch.cuda.memory_available(0)/1024**2:.0f}MB")
#             else:
#                 print("⚠ GPU не доступна")

#         elif choice == '7':
#             if torch.cuda.is_available():
#                 print("\n" + "="*60)
#                 print("ℹ️ ИНФОРМАЦИЯ О GPU")
#                 print("="*60)
#                 print(f"GPU: {torch.cuda.get_device_name(0)}")
#                 print(f"CUDA версия: {torch.version.cuda}")
#                 print(f"PyTorch версия: {torch.__version__}")
#                 print(f"Всего памяти: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
#                 print(f"Используется: {torch.cuda.memory_allocated(0) / 1024**2:.0f} MB")
#                 print(f"Зарезервировано: {torch.cuda.memory_reserved(0) / 1024**2:.0f} MB")
#             else:
#                 print("\n❌ CUDA не доступна!")
#                 print("Проверьте установку драйверов и PyTorch с CUDA")

#         elif choice == '0':
#             print("\n👋 До свидания!")
#             if torch.cuda.is_available():
#                 torch.cuda.empty_cache()
#             break

#         else:
#             print("\n❌ Неверный выбор. Пожалуйста, выберите от 0 до 7.")

# # ================================================
# # ЗАПУСК
# # ================================================
# if __name__ == "__main__":
#     print("🚂 КЛАССИФИКАТОР ВАГОНОВ С ПОДДЕРЖКОЙ CUDA")
#     print("=" * 60)
#     print("📦 Убедитесь, что установлены все зависимости:")
#     print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130")
#     print("   pip install numpy pillow matplotlib tqdm scikit-learn seaborn patool")
#     print("=" * 60)

#     main_menu()






"""
МОДУЛЬ ОБУЧЕНИЯ МОДЕЛИ
Этот скрипт содержит полный код для обучения классификатора вагонов.
Запустите его один раз для получения файла модели.
"""

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
ImageFile.LOAD_TRUNCATED_IMAGES = True

# ================================================
# КОНФИГУРАЦИЯ
# ================================================
class Config:
    # Пути
    BASE_DIR = os.path.join(os.getcwd(), 'wagon_classification')
    DATA_DIR = os.path.join(os.getcwd(), 'wagon_classification', 'data', 'processed')
    EXTRACTED_DIR = os.path.join(os.getcwd(), 'wagon_data', 'extracted')
    MODEL_SAVE_PATH = os.path.join(os.getcwd(), 'models', 'best_model.pth')  # Изменено для новой структуры
    
    # Параметры
    CLASS_NAMES = ['pered', 'zad', 'none']
    NUM_CLASSES = 3
    
    # Гиперпараметры
    BATCH_SIZE = 32
    NUM_EPOCHS = 20
    
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
        image = Image.open(image_path)
        image.verify()
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        if image.size[0] == 0 or image.size[1] == 0:
            print(f"⚠ Изображение {image_path} имеет нулевые размеры")
            image = Image.new('RGB', target_size, color='black')
        return image
    except Exception as e:
        print(f"⚠ Ошибка загрузки {image_path}: {e}")
        return Image.new('RGB', target_size, color='black')

def repair_image_file(image_path):
    """Пытается восстановить поврежденный файл изображения"""
    try:
        with open(image_path, 'rb') as f:
            data = f.read()
        if len(data) == 0:
            print(f"❌ Файл {image_path} пустой")
            return False
        if image_path.lower().endswith(('.jpg', '.jpeg')):
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
# ТРАНСФОРМАЦИИ
# ================================================
def get_transforms():
    """Создание трансформаций для обучения"""
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, val_transform

# ================================================
# ДАТАСЕТ
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
        img_path = self.image_paths[idx]
        image = load_image_safe(img_path)
        if self.transform:
            image = self.transform(image)
        return image, self.labels[idx]

# ================================================
# МОДЕЛЬ
# ================================================
def create_simple_model():
    """Создание архитектуры модели"""
    model = models.efficientnet_b2(weights='DEFAULT')
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, Config.NUM_CLASSES)
    )
    return model.to(Config.DEVICE)

# ================================================
# ПОДГОТОВКА ДАННЫХ
# ================================================
def prepare_data_simple():
    """Подготовка данных с правильными именами папок"""
    print("=" * 60)
    print("📊 ПОДГОТОВКА ДАННЫХ")
    print("=" * 60)
    
    os.makedirs(Config.BASE_DIR, exist_ok=True)
    os.makedirs(Config.EXTRACTED_DIR, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(Config.MODEL_SAVE_PATH), exist_ok=True)
    
    print("\n📤 ШАГ 1: Укажите путь к архиву vagon1.rar")
    print("Пример: C:/Users/Username/Downloads/vagon1.rar")
    archive_path = input("Введите полный путь к архиву: ").strip()
    archive_path = archive_path.replace('/', '\\')
    
    if not os.path.exists(archive_path):
        print(f"\n❌ Файл не найден: {archive_path}")
        return False
    
    print(f"\n✅ Найден архив: {os.path.basename(archive_path)}")
    
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
    
    print("\n🔍 Проверка данных...")
    possible_folders = {
        'pered': ['pered', 'prered', 'peredn', 'peredniy', 'front', 'перед'],
        'zad': ['zad', 'zadn', 'zadniy', 'back', 'rear', 'зад'],
        'none': ['none', 'non', 'empty', 'нет', 'пусто']
    }
    
    actual_folders = os.listdir(Config.EXTRACTED_DIR)
    print(f"Найдены папки в extracted: {actual_folders}")
    
    folder_mapping = {}
    for target_class, possible_names in possible_folders.items():
        for folder in actual_folders:
            folder_lower = folder.lower()
            if folder_lower in possible_names:
                folder_mapping[target_class] = folder
                print(f"  ✓ {target_class} → {folder}")
                break
    
    if len(folder_mapping) < len(Config.CLASS_NAMES):
        print("\n⚠ Не все классы найдены. Ищем изображения...")
        for folder in actual_folders:
            folder_path = os.path.join(Config.EXTRACTED_DIR, folder)
            if os.path.isdir(folder_path):
                images = [f for f in os.listdir(folder_path)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if images:
                    print(f"  Папка '{folder}': {len(images)} изображений")
                    if 'pered' in folder.lower() or 'перед' in folder.lower():
                        folder_mapping['pered'] = folder
                    elif 'zad' in folder.lower() or 'зад' in folder.lower():
                        folder_mapping['zad'] = folder
                    elif 'none' in folder.lower() or 'нет' in folder.lower():
                        folder_mapping['none'] = folder
    
    missing_classes = []
    for cls in Config.CLASS_NAMES:
        if cls not in folder_mapping:
            missing_classes.append(cls)
    
    if missing_classes:
        print(f"\n❌ Отсутствуют классы: {missing_classes}")
        return False
    
    print("\n✅ Все классы найдены!")
    print("\n📁 Создание структуры train/val...")
    for split in ['train', 'val']:
        for cls in Config.CLASS_NAMES:
            os.makedirs(os.path.join(Config.DATA_DIR, split, cls), exist_ok=True)
    
    print("📊 Разделение на train/val (80/20)...")
    total_images = 0
    
    for target_class, source_folder in folder_mapping.items():
        source_dir = os.path.join(Config.EXTRACTED_DIR, source_folder)
        if not os.path.exists(source_dir):
            continue
        
        images = [f for f in os.listdir(source_dir)
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not images:
            continue
        
        print(f"\n📂 Обрабатываем {source_folder} → {target_class}:")
        print(f"  Найдено {len(images)} изображений")
        
        train_imgs, val_imgs = train_test_split(images, test_size=0.2, random_state=42)
        
        print(f"  Копируем {len(train_imgs)} в train...")
        for img in tqdm(train_imgs, desc=f"  {target_class} train"):
            src = os.path.join(source_dir, img)
            dst = os.path.join(Config.DATA_DIR, 'train', target_class, img)
            shutil.copy2(src, dst)
        
        print(f"  Копируем {len(val_imgs)} в val...")
        for img in tqdm(val_imgs, desc=f"  {target_class} val"):
            src = os.path.join(source_dir, img)
            dst = os.path.join(Config.DATA_DIR, 'val', target_class, img)
            shutil.copy2(src, dst)
        
        total_images += len(images)
        print(f"  ✓ {target_class}: {len(train_imgs)} train, {len(val_imgs)} val")
    
    print(f"\n✅ Готово! Всего {total_images} изображений")
    return True

# ================================================
# ОБУЧЕНИЕ
# ================================================
def train_simple_model():
    """Основная функция обучения"""
    print("\n" + "="*60)
    print("🏋️‍♂️ НАЧИНАЕМ ОБУЧЕНИЕ")
    print("=" * 60)
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    Config.print_info()
    
    train_transform, val_transform = get_transforms()
    
    print("\n📥 Загрузка данных...")
    train_dataset = RobustWagonDataset(Config.DATA_DIR, transform=train_transform, mode='train')
    val_dataset = RobustWagonDataset(Config.DATA_DIR, transform=val_transform, mode='val')
    
    if len(train_dataset) == 0:
        print("❌ Обучающие данные не найдены!")
        return None, None
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    print("\n🧠 Создание модели...")
    model = create_simple_model()
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
    
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
        
        # Обучение
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        train_bar = tqdm(train_loader, desc='Training')
        for images, labels in train_bar:
            images = images.to(Config.DEVICE)
            labels = labels.to(Config.DEVICE)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
            
            train_bar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100.*train_correct/train_total:.1f}%'
            })
        
        avg_train_loss = train_loss / len(train_loader)
        train_accuracy = train_correct / train_total
        
        # Валидация
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
        
        scheduler.step()
        
        history['train_loss'].append(avg_train_loss)
        history['train_acc'].append(train_accuracy)
        history['val_loss'].append(avg_val_loss)
        history['val_acc'].append(val_accuracy)
        
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
        
        print(f"📊 Результаты эпохи {epoch + 1}:")
        print(f"  Train Loss: {avg_train_loss:.4f}, Acc: {train_accuracy:.4f}")
        print(f"  Val Loss: {avg_val_loss:.4f}, Acc: {val_accuracy:.4f}")
    
    print("\n" + "="*60)
    print("🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    print(f"🏆 Лучшая точность на валидации: {best_val_acc:.4f}")
    print(f"💾 Модель сохранена: {Config.MODEL_SAVE_PATH}")
    
    return model, history

# ================================================
# ГЛАВНОЕ МЕНЮ
# ================================================
def main_menu():
    """Главное меню для обучения"""
    print("\n" + "="*60)
    print("🚂 КЛАССИФИКАТОР ВАГОНОВ - ОБУЧЕНИЕ")
    print("="*60)
    
    while True:
        print("\n" + "="*60)
        print("ГЛАВНОЕ МЕНЮ:")
        print("1. 📊 Подготовить данные")
        print("2. 🏋️‍♂️ Обучить модель")
        print("3. 🧹 Очистить кэш")
        print("0. ❌ Выход")
        print("="*60)
        
        choice = input("\nВыберите действие (0-3): ").strip()
        
        if choice == '1':
            success = prepare_data_simple()
            if success:
                print("\n✅ Данные готовы к обучению!")
            else:
                print("\n❌ Ошибка при подготовке данных")
        
        elif choice == '2':
            if not os.path.exists(Config.DATA_DIR):
                print("\n❌ Данные не подготовлены! Сначала выполните шаг 1.")
                continue
            try:
                model, history = train_simple_model()
                if model is not None:
                    print("\n✅ Обучение успешно завершено!")
            except Exception as e:
                print(f"\n❌ Ошибка при обучении: {e}")
        
        elif choice == '3':
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("✅ Кэш GPU очищен!")
            else:
                print("⚠ GPU не доступна")
        
        elif choice == '0':
            print("\n👋 До свидания!")
            break
        
        else:
            print("\n❌ Неверный выбор")

if __name__ == "__main__":
    print("🚂 КЛАССИФИКАТОР ВАГОНОВ - ОБУЧЕНИЕ")
    print("=" * 60)
    main_menu()