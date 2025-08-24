"""
File Analyzer - Утилита для анализа файлов
"""
import os
from typing import Dict, List, Optional, Any, DefaultDict
from collections import defaultdict
import json


class FileAnalyzer:
    """Класс для анализа файлов в директории."""

    def __init__(self, directory: str):
        """
        Инициализация анализатора.

        Args:
            directory: Путь к директории для анализа

        Raises:
            ValueError: Если директория не существует
        """
        if not os.path.exists(directory):
            raise ValueError(f"Директория {directory} не существует")

        if not os.path.isdir(directory):
            raise ValueError(f"{directory} не является директорией")

        self.directory = directory

    def get_files_by_extension(self, extensions: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Группирует файлы по расширениям.

        Args:
            extensions: Список расширений для фильтрации (например, ['.py', '.txt'])
                       Если None, возвращает все файлы

        Returns:
            Словарь {расширение: [список_файлов]}
        """
        files_by_ext = defaultdict(list)

        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                ext = ext.lower()

                # Если фильтр не задан или расширение в списке
                if extensions is None or ext in extensions:
                    files_by_ext[ext].append(file_path)

        return dict(files_by_ext)

    def get_file_stats(self) -> Dict[str, Any]:
        """
        Собирает статистику по файлам.

        Returns:
            Словарь со статистикой
        """
        total_files = 0
        total_size = 0
        extensions_count: DefaultDict[str, int] = defaultdict(int)

        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    total_files += 1

                    _, ext = os.path.splitext(file)
                    extensions_count[ext.lower()] += 1
                except OSError:
                    # Пропускаем файлы, к которым нет доступа
                    continue

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'extensions_count': dict(extensions_count)
        }

    def find_large_files(self, min_size_mb: float = 10.0) -> List[Dict[str, Any]]:
        """
        Находит большие файлы.

        Args:
            min_size_mb: Минимальный размер файла в МБ

        Returns:
            Список файлов с информацией о размере
        """
        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = []

        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size >= min_size_bytes:
                        large_files.append({
                            'path': file_path,
                            'size_bytes': file_size,
                            'size_mb': round(file_size / (1024 * 1024), 2)
                        })
                except OSError:
                    continue

        # Сортируем по размеру (от большего к меньшему)
        return sorted(large_files, key=lambda x: x['size_bytes'], reverse=True)

    def generate_report(self, output_file: str = 'file_report.json') -> str:
        """
        Генерирует полный отчет и сохраняет в файл.

        Args:
            output_file: Имя выходного файла

        Returns:
            Путь к созданному отчету
        """
        stats = self.get_file_stats()
        files_by_ext = self.get_files_by_extension()
        large_files = self.find_large_files()

        report = {
            'directory': self.directory,
            'statistics': stats,
            'files_by_extension': files_by_ext,
            'large_files': large_files[:10]  # Топ 10 самых больших файлов
        }

        output_path = os.path.join(self.directory, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_path


def main():
    """Пример использования."""
    import sys

    if len(sys.argv) != 2:
        print("Использование: python analyzer.py <путь_к_директории>")
        return

    directory = sys.argv[1]

    try:
        analyzer = FileAnalyzer(directory)

        print(f"Анализ директории: {directory}")
        print("-" * 50)

        stats = analyzer.get_file_stats()
        print(f"Всего файлов: {stats['total_files']}")
        print(f"Общий размер: {stats['total_size_mb']} МБ")

        print("\nТипы файлов:")
        for ext, count in stats['extensions_count'].items():
            ext_display = ext if ext else "без расширения"
            print(f"  {ext_display}: {count}")

        large_files = analyzer.find_large_files(5.0)  # Файлы больше 5 МБ
        if large_files:
            print("\nБольшие файлы (>5 МБ):")
            for file_info in large_files[:5]:  # Топ 5
                print(f"  {file_info['size_mb']} МБ: {file_info['path']}")

        report_path = analyzer.generate_report()
        print(f"\nОтчет сохранен: {report_path}")

    except ValueError as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()