---
title: Wagon Classification API
emoji: 🚂
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: API для классификации вагонов по изображениям
---

# Wagon Classification API

API для классификации вагонов по изображениям. Определяет переднюю и заднюю часть вагона на фотографии.

## Использование

- 📡 API документация: `/docs`
- 🩺 Health check: `/health`
- 🖥️ Веб-интерфейс: `/`

## Локальная разработка

```bash
docker build -t wagon-classifier .
docker run -p 7860:7860 wagon-classifier