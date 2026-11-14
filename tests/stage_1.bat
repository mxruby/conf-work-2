@echo off
chcp 65001 > nul

echo Тест 1: Корректный запуск (обычный режим)
python src/main.py --package example --repository https://example.com/repository --max-depth 4
echo.

echo Тест 2: Не указано имя пакета
python src/main.py --repository ./tests --test-mode
echo.

echo Тест 3: Отрицательная глубина
python src/main.py --package example --repository ./tests --test-mode --max-depth -1
echo.

echo Тест 4: Несуществующий путь
python src/main.py --package example --repository ./missing_repo --test-mode
echo.