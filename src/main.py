import argparse
import gzip
import lzma
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


MIN_DEPTH = 1


def positive_int(value):
    """Проверяет, что число является положительным."""

    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "значение должно быть целым числом"
        )

    if number < MIN_DEPTH:
        raise argparse.ArgumentTypeError(
            "значение должно быть больше нуля"
        )

    return number


def valid_package_name(value):
    """Проверяет имя пакета."""

    if not value.strip():
        raise argparse.ArgumentTypeError(
            "имя пакета не может быть пустым"
        )

    if any(char.isspace() for char in value):
        raise argparse.ArgumentTypeError(
            "имя пакета не должно содержать пробелы"
        )

    return value


def valid_repository(value):
    """Проверяет URL или путь к репозиторию."""

    if not value.strip():
        raise argparse.ArgumentTypeError(
            "путь или URL не может быть пустым"
        )

    parsed = urlparse(value)

    if parsed.scheme:
        if parsed.scheme not in ("http", "https"):
            raise argparse.ArgumentTypeError(
                "поддерживаются только URL с http или https"
            )

        if not parsed.netloc:
            raise argparse.ArgumentTypeError(
                "указан некорректный URL"
            )
    else:
        if not os.path.exists(value):
            raise argparse.ArgumentTypeError(
                "указанный путь не существует"
            )

        if not os.path.isfile(value) and not os.path.isdir(value):
            raise argparse.ArgumentTypeError(
                "путь должен указывать на файл или каталог"
            )

    return value


def parse_arguments():
    """Парсинг аргументов командной строки"""

    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей пакетов"
    )

    parser.add_argument(
        "--package",
        required=True,
        type=valid_package_name,
        help="имя анализируемого пакета"
    )

    parser.add_argument(
        "--repository",
        required=True,
        type=valid_repository,
        help="URL репозитория или путь к тестовому репозиторию"
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="режим работы с тестовым репозиторием"
    )

    parser.add_argument(
        "--max-depth",
        type=positive_int,
        default=3,
        help="максимальная глубина анализа (по умолчанию: 3)"
    )

    return parser.parse_args()


def load_repository(repository, test_mode):
    """Загружает индекс пакетов из локального файла или URL."""

    if not test_mode:
        try:
            with urlopen(repository, timeout=30) as response:
                return response.read()

        except Exception as error:
            raise RuntimeError(
                f"Ошибка загрузки репозитория: {error}"
            )

    path = Path(repository)

    if path.is_dir():
        candidates = [
            path / "Packages.xz",
            path / "Packages.gz",
            path / "Packages"
        ]

        file_path = next(
            (item for item in candidates if item.is_file()),
            None
        )

        if file_path is None:
            raise RuntimeError(
                "В указанном каталоге не найден файл Packages"
            )
    else:
        file_path = path

    try:
        return file_path.read_bytes()
    except OSError as error:
        raise RuntimeError(
            f"Ошибка чтения файла: {error}"
        )


def decompress_repository(data, repository):
    """Распаковывает индекс пакетов при необходимости."""

    path = urlparse(repository).path.lower()

    try:
        if path.endswith(".xz"):
            data = lzma.decompress(data)

        elif path.endswith(".gz"):
            data = gzip.decompress(data)

        return data.decode("utf-8")

    except (lzma.LZMAError, gzip.BadGzipFile,
            EOFError, UnicodeDecodeError) as error:
        raise RuntimeError(
            f"Ошибка распаковки индекса пакетов: {error}"
        )


def parse_packages(data):
    """Разбирает записи пакетов из индекса Packages."""

    packages = {}
    current_package = {}
    current_field = None

    for line in data.splitlines():
        if not line:
            if "Package" in current_package:
                packages[current_package["Package"]] = current_package

            current_package = {}
            current_field = None
            continue

        if line.startswith((" ", "\t")):
            if current_field and current_field in current_package:
                current_package[current_field] += " " + line.strip()
            continue

        if ":" in line:
            field, value = line.split(":", 1)
            current_field = field
            current_package[field] = value.strip()

    if "Package" in current_package:
        packages[current_package["Package"]] = current_package

    return packages


def extract_dependencies(package_info):
    dependencies = []

    for field in ("Pre-Depends", "Depends"):
        value = package_info.get(field, "")

        if not value:
            continue

        groups = value.split(",")

        for group in groups:
            alternatives = group.split("|")

            for alternative in alternatives:
                match = re.match(
                    r"\s*([a-z0-9][a-z0-9+.-]*)",
                    alternative
                )

                if match:
                    name = match.group(1)

                    if name not in dependencies:
                        dependencies.append(name)

    return dependencies


def main():
    """Основная программа"""

    args = parse_arguments()
    try:
        if args.test_mode:
            if urlparse(args.repository).scheme:
                raise RuntimeError(
                    "В локальном режиме необходимо указать путь к файлу"
                )
        elif not urlparse(args.repository).scheme:
            raise RuntimeError(
                "В удалённом режиме необходимо указать URL"
            )
        raw_data = load_repository(args.repository, args.test_mode)
        data = decompress_repository(raw_data, args.repository)

        packages = parse_packages(data)

        if args.package not in packages:
            raise RuntimeError(
                f"Пакет '{args.package}' не найден в репозитории"
            )

        dependencies = extract_dependencies(packages[args.package])

        print(f"Прямые зависимости пакета {args.package}:")

        if dependencies:
            for dependency in dependencies:
                print(f"- {dependency}")
        else:
            print("Зависимости отсутствуют.")

    except RuntimeError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
