"""
Тесты для FileAnalyzer
"""
import os
import tempfile
import json
import pytest
from file_analyzer.analyzer import FileAnalyzer


class TestFileAnalyzer:
    """Тесты для класса FileAnalyzer."""

    @pytest.fixture
    def temp_dir_with_files(self):
        """Создает временную директорию с тестовыми файлами."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовые файлы
            files_to_create = [
                ("test.py", "print('hello')\n" * 100),  # Python файл
                ("data.txt", "Some text data\n" * 50),  # Текстовый файл
                ("config.json", '{"key": "value"}'),  # JSON файл
                ("large_file.log", "Log entry\n" * 10000),  # Большой файл
                ("no_extension", "File without extension")  # Файл без расширения
            ]

            for filename, content in files_to_create:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Создаем подпапку с файлом
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "nested.py"), 'w') as f:
                f.write("# nested file")

            yield temp_dir

    def test_init_valid_directory(self, temp_dir_with_files):
        """Тест успешной инициализации с существующей директорией."""
        analyzer = FileAnalyzer(temp_dir_with_files)
        assert analyzer.directory == temp_dir_with_files

    def test_init_nonexistent_directory(self):
        """Тест инициализации с несуществующей директорией."""
        with pytest.raises(ValueError, match="не существует"):
            FileAnalyzer("/nonexistent/directory")

    def test_init_file_instead_of_directory(self, temp_dir_with_files):
        """Тест инициализации с файлом вместо директории."""
        file_path = os.path.join(temp_dir_with_files, "test.py")
        with pytest.raises(ValueError, match="не является директорией"):
            FileAnalyzer(file_path)

    def test_get_files_by_extension_all(self, temp_dir_with_files):
        """Тест получения всех файлов по расширениям."""
        analyzer = FileAnalyzer(temp_dir_with_files)
        files_by_ext = analyzer.get_files_by_extension()

        # Проверяем, что есть файлы разных типов
        assert '.py' in files_by_ext
        assert '.txt' in files_by_ext
        assert '.json' in files_by_ext
        assert '.log' in files_by_ext
        assert '' in files_by_ext  # Файл без расширения

        # Проверяем количество Python файлов (включая в подпапке)
        assert len(files_by_ext['.py']) == 2

    def test_get_files_by_extension_filtered(self, temp_dir_with_files):
        """Тест фильтрации файлов по расширениям."""
        analyzer = FileAnalyzer(temp_dir_with_files)
        python_files = analyzer.get_files_by_extension(['.py'])

        # Должны быть только Python файлы
        assert len(python_files) == 1
        assert '.py' in python_files
        assert len(python_files['.py']) == 2

    def test_get_file_stats(self, temp_dir_with_files):
        """Тест сбора статистики по файлам."""
        analyzer = FileAnalyzer(temp_dir_with_files)
        stats = analyzer.get_file_stats()

        # Проверяем структуру ответа
        required_keys = ['total_files', 'total_size_bytes', 'total_size_mb', 'extensions_count']
        for key in required_keys:
            assert key in stats

        # Проверяем типы данных
        assert isinstance(stats['total_files'], int)
        assert isinstance(stats['total_size_bytes'], int)
        assert isinstance(stats['total_size_mb'], float)
        assert isinstance(stats['extensions_count'], dict)

        # Проверяем логичность данных
        assert stats['total_files'] > 0
        assert stats['total_size_bytes'] > 0
        assert stats['total_size_mb'] == round(stats['total_size_bytes'] / (1024 * 1024), 2)

    def test_find_large_files(self, temp_dir_with_files):
        """Тест поиска больших файлов."""
        analyzer = FileAnalyzer(temp_dir_with_files)

        # Ищем файлы больше 0.01 МБ (очень маленький порог для теста)
        large_files = analyzer.find_large_files(0.01)

        assert isinstance(large_files, list)

        # Проверяем структуру данных о файле
        if large_files:
            file_info = large_files[0]
            required_keys = ['path', 'size_bytes', 'size_mb']
            for key in required_keys:
                assert key in file_info

            # Проверяем, что размеры согласованы
            expected_mb = round(file_info['size_bytes'] / (1024 * 1024), 2)
            assert file_info['size_mb'] == expected_mb

            # Проверяем сортировку (от большего к меньшему)
            if len(large_files) > 1:
                for i in range(len(large_files) - 1):
                    assert large_files[i]['size_bytes'] >= large_files[i + 1]['size_bytes']

    def test_generate_report(self, temp_dir_with_files):
        """Тест генерации отчета."""
        analyzer = FileAnalyzer(temp_dir_with_files)
        report_path = analyzer.generate_report('test_report.json')

        # Проверяем, что файл создан
        assert os.path.exists(report_path)
        assert report_path.endswith('test_report.json')

        # Проверяем содержимое отчета
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        required_keys = ['directory', 'statistics', 'files_by_extension', 'large_files']
        for key in required_keys:
            assert key in report_data

        # Проверяем, что directory совпадает
        assert report_data['directory'] == temp_dir_with_files

        # Проверяем, что large_files не больше 10 (согласно коду)
        assert len(report_data['large_files']) <= 10

    def test_empty_directory(self):
        """Тест работы с пустой директорией."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = FileAnalyzer(temp_dir)

            stats = analyzer.get_file_stats()
            assert stats['total_files'] == 0
            assert stats['total_size_bytes'] == 0
            assert stats['total_size_mb'] == 0.0
            assert stats['extensions_count'] == {}

            files_by_ext = analyzer.get_files_by_extension()
            assert files_by_ext == {}

            large_files = analyzer.find_large_files()
            assert large_files == []


# Функциональные тесты (интеграционные)
class TestFileAnalyzerIntegration:
    """Интеграционные тесты для FileAnalyzer."""

    def test_analyze_current_directory(self):
        """Тест анализа текущей директории проекта."""
        # Анализируем текущую директорию
        current_dir = "."
        if os.path.exists(current_dir):
            analyzer = FileAnalyzer(current_dir)

            # Основные методы должны работать без ошибок
            stats = analyzer.get_file_stats()
            assert isinstance(stats, dict)

            files_by_ext = analyzer.get_files_by_extension(['.py'])
            assert isinstance(files_by_ext, dict)

            large_files = analyzer.find_large_files(0.1)
            assert isinstance(large_files, list)


if __name__ == "__main__":
    pytest.main([__file__])