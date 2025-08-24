# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt requirements-dev.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Копируем исходный код
COPY file_analyzer/ ./file_analyzer/
COPY tests/ ./tests/

# ВАЖНО: Добавляем текущую папку в PYTHONPATH
ENV PYTHONPATH=/app

# Создаем непривилегированного пользователя
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Команда по умолчанию: запуск тестов
CMD ["pytest", "tests/", "-v"]

# Альтернативные команды:
# Для запуска анализатора: docker run myapp python -m file_analyzer.analyzer /path
# Для интерактивной работы: docker run -it myapp bash