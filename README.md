# PP-2.0
Версия Python: 3.9
Установить CUDA:
```Command Prompt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 --force-reinstall
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --force-reinstall #если ваша ОС не хочет работать с версией 128 
```



Проверка параметров вашего устройства для работы с CUDA:
```Command Prompt
nvidia-smi
```



Можно создать тестовый файл и проверить наличие возможности работы с GPU:
```
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Простой тест
    x = torch.randn(3, 3).cuda()
    y = torch.randn(3, 3).cuda()
    z = x @ y
    print(f"Тест умножения матриц на GPU прошел успешно!")
    print(f"Результат:\n{z}")
```


Войти в папку:
```Command Prompt
cd PP-2.0
```



Установка библиотек:
```Command Prompt
pip install -r requirements.txt
```



Запуск обучения:
```Command Prompt
python train_model.py
```



Запуск API:
```Command Prompt
uvicorn app.main:app --reload
```