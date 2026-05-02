#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚂 ЗАПУСК ПРОЕКТА WAGON CLASSIFIER${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Проверка и создание модели
echo -e "\n${GREEN}📋 Шаг 1/4: Проверка модели...${NC}"
if [ -f "models/best_model.pth" ]; then
    echo -e "${GREEN}✅ Модель найдена: models/best_model.pth${NC}"
    ls -lh models/best_model.pth
else
    echo -e "${YELLOW}⚠️ Модель не найдена. Создаю фиктивную модель...${NC}"
    python scripts/create_dummy_model.py
fi

# 2. Проверка .env файла
echo -e "\n${GREEN}📋 Шаг 2/4: Проверка конфигурации...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ .env файл не найден. Создаю из примера...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env файл создан${NC}"
else
    echo -e "${GREEN}✅ .env файл существует${NC}"
fi

# 3. Запуск Docker контейнеров
echo -e "\n${GREEN}📋 Шаг 3/4: Запуск Docker контейнеров...${NC}"
docker-compose up -d

# 4. Ожидание готовности
echo -e "\n${GREEN}📋 Шаг 4/4: Ожидание готовности сервисов...${NC}"
echo -e "${YELLOW}⏳ Подождите 15 секунд...${NC}"
sleep 15

# 5. Проверка API
echo -e "\n${GREEN}📋 Проверка работоспособности...${NC}"
HEALTH=$(curl -s http://localhost:8000/api/v1/health)

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API работает!${NC}"
else
    echo -e "${YELLOW}⚠️ API ещё не готов. Проверьте логи: docker logs wagon_api --tail 20${NC}"
fi

# 6. Вывод информации
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 ПРОЕКТ УСПЕШНО ЗАПУЩЕН! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}🌐 Доступные сервисы:${NC}"
echo -e "  API:        ${YELLOW}http://localhost:8000${NC}"
echo -e "  Swagger:    ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  Airflow:    ${YELLOW}http://localhost:8080${NC} (admin/admin)"
echo -e "  MinIO:      ${YELLOW}http://localhost:9001${NC} (minioadmin/minioadmin)"
echo ""
echo -e "${GREEN}📊 Проверка API:${NC}"
curl -s http://localhost:8000/api/v1/health | python -m json.tool
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Для остановки проекта: docker-compose down${NC}"