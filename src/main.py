
import argparse
import os
import sys
from urllib.parse import urlparse


def positive_int(value):
    """Проверяет, что число является положительным."""

    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "значение должно быть целым числом"
        )

    if number < 1:
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


def main():
    args = parse_arguments()

    print("Параметры запуска:")
    print(f"package = {args.package}")
    print(f"repository = {args.repository}")
    print(f"test_mode = {args.test_mode}")
    print(f"max_depth = {args.max_depth}")


if __name__ == "__main__":
    main()
