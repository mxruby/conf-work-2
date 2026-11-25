@echo off
chcp 65001 > nul

echo Тест 1: Поиск обратных зависимостей пакета D
python .\src\main.py --package D --repository .\test_repo\Packages --test-mode --reverse
echo.

echo Тест 2: Пакет без обратных зависимостей
python .\src\main.py --package E --repository .\test_repo\Packages --test-mode --reverse
echo.

echo Тест 3: Циклические зависимости
python .\src\main.py --package G --repository .\test_repo\Packages --test-mode --reverse
echo.