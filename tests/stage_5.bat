@echo off
chcp 65001 > nul

echo Тест 1: bash
python src/main.py --package bash --repository https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --max-depth 5 --visualize
echo.

echo Тест 2: logwatch
python src/main.py --package logwatch --repository https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --max-depth 10 --visualize
echo.

echo Тест 3: cdebconf
python src/main.py --package cdebconf --repository https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz --max-depth 10 --visualize
echo.