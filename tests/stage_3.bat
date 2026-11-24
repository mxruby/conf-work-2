@echo off
chcp 65001 > nul

echo Тест 1: Обычный граф
python .\src\main.py --package A --repository .\test_repo\Packages --test-mode --max-depth 3
echo.

echo Тест 2: Ограничение глубины
python .\src\main.py --package A --repository .\test_repo\Packages --test-mode --max-depth 1
echo.

echo Тест 3: Циклические зависимости
python .\src\main.py --package G --repository .\test_repo\Packages --test-mode --max-depth 5
echo.

echo Тест 4: Несуществующий пакет
python .\src\main.py --package Z --repository .\test_repo\Packages --test-mode
echo.