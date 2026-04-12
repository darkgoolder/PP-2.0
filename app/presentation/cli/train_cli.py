"""
CLI интерфейс для обучения модели
"""

import argparse
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.config import settings
from app.use_cases.train_model import TrainingConfig, TrainModelUseCase


def main():
    parser = argparse.ArgumentParser(description="Обучение классификатора вагонов")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Путь к директории с данями (должна содержать train/val папки)",
    )
    parser.add_argument("--epochs", type=int, default=15, help="Количество эпох")
    parser.add_argument("--batch-size", type=int, default=32, help="Размер батча")
    parser.add_argument("--lr", type=float, default=1e-4, help="Скорость обучения")

    args = parser.parse_args()

    config = TrainingConfig(
        num_epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr
    )

    use_case = TrainModelUseCase(
        data_dir=args.data_dir,
        model_save_path=str(settings.MODEL_PATH),
        class_names=settings.CLASS_NAMES,
    )

    print("\n🚂 Запуск обучения модели...")
    print(f"📁 Данные: {args.data_dir}")
    print(f"💾 Модель будет сохранена: {settings.MODEL_PATH}")
    print(f"📊 Конфигурация: эпох={args.epochs}, batch={args.batch_size}, lr={args.lr}")
    print("-" * 50)

    try:
        history = use_case.execute(config)
        print("\n" + "=" * 50)
        print("✅ Обучение завершено успешно!")
        print(f"🏆 Лучшая точность на валидации: {history.best_val_acc:.4f}")
        print(f"💾 Модель сохранена: {settings.MODEL_PATH}")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Ошибка при обучении: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
