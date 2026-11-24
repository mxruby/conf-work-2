import argparse
import gzip
import lzma
import re
import sys
from collections import deque
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
    if not value.strip():
        raise argparse.ArgumentTypeError(
            "источник репозитория не может быть пустым"
        )

    parsed = urlparse(value)

    if parsed.scheme:
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise argparse.ArgumentTypeError("некорректный URL")
    elif not Path(value).exists():
        raise argparse.ArgumentTypeError(
            "указанный файл не существует"
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


def load_remote_repository(url):
    try:
        with urlopen(url, timeout=30) as response:
            data = response.read()

    except Exception as error:
        raise RuntimeError(
            f"Ошибка загрузки репозитория: {error}"
        )

    try:
        path = urlparse(url).path.lower()

        if path.endswith(".gz"):
            data = gzip.decompress(data)
        elif path.endswith(".xz"):
            data = lzma.decompress(data)

        return data.decode("utf-8")

    except (OSError, EOFError, UnicodeDecodeError) as error:
        raise RuntimeError(
            f"Ошибка обработки индекса: {error}"
        )


def load_test_repository(path):
    """Читает тестовый репозиторий в формате Packages."""

    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(
            f"Ошибка чтения тестового репозитория: {error}"
        )


def validate_test_repository(packages):
    """Проверяет формат тестового репозитория."""

    for package, info in packages.items():
        if not re.fullmatch(r"[A-Z]+", package):
            raise RuntimeError(
                f"Некорректное имя пакета: {package}"
            )

        dependencies = extract_dependencies(info)

        for dependency in dependencies:
            if not re.fullmatch(r"[A-Z]+", dependency):
                raise RuntimeError(
                    f"Некорректное имя зависимости: {dependency}"
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


def get_dependencies(package, repository):
    if package not in repository:
        return []

    return extract_dependencies(repository[package])


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
                    r"\s*([A-Za-z0-9][A-Za-z0-9+.-]*)",
                    alternative
                )

                if match:
                    name = match.group(1)

                    if name not in dependencies:
                        dependencies.append(name)

    return dependencies


def build_graph(start_package, repository, max_depth):
    graph = {}

    queue = deque()
    queue.append((start_package, 0))

    visited = {start_package}

    while queue:
        current_package, depth = queue.popleft()

        graph[current_package] = []

        if depth >= max_depth:
            continue

        dependencies = get_dependencies(
            current_package,
            repository
        )

        graph[current_package] = dependencies

        for dependency in dependencies:
            if dependency not in visited:
                visited.add(dependency)
                queue.append((dependency, depth + 1))

    return graph


def print_graph(graph):
    print("\nГраф зависимостей:")

    for package, dependencies in graph.items():
        if dependencies:
            print(f"{package} -> {', '.join(dependencies)}")
        else:
            print(f"{package} -> нет зависимостей")


def main():
    """Основная программа"""

    args = parse_arguments()
    try:
        if args.test_mode:
            if urlparse(args.repository).scheme:
                raise RuntimeError(
                    "В тестовом режиме необходимо указать путь к файлу"
                )

            if not Path(args.repository).is_file():
                raise RuntimeError(
                    "Тестовый репозиторий должен быть файлом"
                )

            data = load_test_repository(args.repository)
            repository = parse_packages(data)

            validate_test_repository(repository)

            if not re.fullmatch(r"[A-Z]+", args.package):
                raise RuntimeError(
                    "В тестовом режиме имя пакета должно состоять "
                    "из больших латинских букв"
                )

        else:
            if not urlparse(args.repository).scheme:
                raise RuntimeError(
                    "В удалённом режиме необходимо указать URL"
                )

            data = load_remote_repository(args.repository)
            repository = parse_packages(data)

        if args.package not in repository:
            raise RuntimeError(
                f"Пакет {args.package} не найден в репозитории"
            )

        graph = build_graph(
            args.package,
            repository,
            args.max_depth
        )

        print_graph(graph)

    except RuntimeError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
