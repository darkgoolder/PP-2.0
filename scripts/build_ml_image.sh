#!/bin/bash
# scripts/build_ml_image.sh

echo "🐳 Сборка ML образа для Docker Operator..."

docker build -f docker/ml.Dockerfile -t wagon-ml-trainer:latest .

echo "✅ Образ wagon-ml-trainer:latest собран"