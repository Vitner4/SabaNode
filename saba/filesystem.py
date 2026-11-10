import os
import json
import shutil
import hashlib

from pathlib import Path
from typing import Iterator

from saba.policy import Policy


class File:
    def __init__(self):
        self._format = _JSON()

    # Сохранение обычного словаря в JSON
    def save(self, path: str, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as file:
            self._format.encode(data, file)

    # Потоковое сохранение снимка
    def save_snapshot(
        self,
        node: dict,
        path: str,
        entries: Iterator[dict]
    ) -> None:
        
        target = Path(path)
        temporary = target.with_name(target.name + ".tmp")

        try:
            with open(temporary, "w", encoding="utf-8") as file:
                self._format.encode_snapshot(file, node, entries)

            # Заменяем целевой файл только после успешной записи
            temporary.replace(target)

        except Exception:
            # Удаляем незавершённый временный файл
            temporary.unlink(missing_ok=True)
            raise

    # Чтение JSON-файла
    def load(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as file:
            return self._format.decode(file)

    # Удаление файла или директории
    def remove(self, path: str) -> None:
        target = Path(path)

        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()

    # Перемещение файла или директории
    def move(self, source: str, destination: str) -> None:
        shutil.move(source, destination)

    # Обновление файла
    def update(self):       
        ...


class _JSON:
    # Обычная JSON-сериализация
    def encode(self, data: dict, file) -> None:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Десериализация JSON
    def decode(self, file) -> dict:
        return json.load(file)

    # Потоковая запись снимка
    def encode_snapshot(
        self,
        file,
        node: dict,
        entries: Iterator[dict]
    ) -> None:
        
        file.write('{\n    "node": ')
        json.dump(node["name"], file, ensure_ascii=False)

        file.write(',\n    "path": ')
        json.dump(node["path"], file, ensure_ascii=False)

        file.write(',\n    "structure": [\n')

        first = True

        for entry in entries:
            if not first:
                file.write(',\n')

            file.write('        ')

            json.dump(
                entry,
                file,
                ensure_ascii=False
            )

            first = False

        file.write('\n    ]\n}')


class FileIdentity:
    # Генерация Hash
    @staticmethod
    def get_hash(path: str) -> str:
            sha256 = hashlib.sha256()

            with open(path, "rb") as file:
                for chunk in iter(lambda: file.read(65536), b""):
                    sha256.update(chunk)

            return sha256.hexdigest()


class Snapshot:
    def __init__(self):
        self.sync_plan = []
        self.round = _Round()
        self.file = File()
        self.policy = Policy().policy

    # Создание снимка файловой структуры
    def create(self, node: dict, path: str) -> None: 
        root = Path(node["path"])

        if not root.is_dir():
            raise NotADirectoryError(node)

        # Scanner передаёт записи постепенно
        entries = self.round.scan(root)

        # File записывает их непосредственно на диск
        self.file.save_snapshot(
            path=path,
            node=node,
            entries=entries
        )

    # Сравнение снимков и подготовка к синхронизации
    def compare(self, snapshots: list):
            ...

    # Решение конфликтов
    def conflictResolver(self):
        ...


class _Round:
    # Рекурсивное сканирование директории
    def scan(self, node_path: str) -> Iterator[dict]:
        root = Path(node_path)

        for current_root, dirs, files in os.walk(root):
            current_path = Path(current_root)
            relative_path = current_path.relative_to(root)

            # Записываем найденные директории
            for directory in dirs:
                yield {
                    "path": (relative_path / directory).as_posix(),
                    "type": "directory",
                }

            # Записываем найденные файлы
            for filename in files:
                file_path = current_path / filename

                yield {
                    "path": file_path.relative_to(root).as_posix(),
                    "type": "file",
                    "size": file_path.stat().st_size,
                    "mtime": file_path.stat().st_mtime,
                    "hash": FileIdentity.get_hash(str(file_path)),
                }


class Sync:
    # Синхронизация данных
    def synchronize(self, plan):
        ...