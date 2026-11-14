@echo off
chcp 65001 > nul

echo Тест 1: noble gz
python src/main.py --package bash --repository https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
echo.

echo Тест 2: stonking xz
python src/main.py --package accountsservice --repository https://archive.ubuntu.com/ubuntu/dists/stonking/main/binary-amd64/Packages.xz
echo.

echo Тест 3: Не найден пакет
python src/main.py --package bashhh --repository https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
echo.