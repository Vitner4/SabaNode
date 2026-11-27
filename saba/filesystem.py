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

    # Сохранение данных
    def save(self, path: str, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as file:
            self._format.encode(data, file)

    # Потоковое сохранение снимка
    def save_snapshot(
        self,
        header: dict, # метаданные (записываются один раз)
        path: str | Path, # путь к файлу
        entries: Iterator[dict] # поток данных через yield
    ) -> None:
        
        target = Path(path)
        temporary = target.with_name(target.name + ".tmp")

        try:
            with open(temporary, "w", encoding="utf-8") as file:
                self._format.encode_snapshot(file, header, entries)

            # Заменяем целевой файл только после успешной записи
            temporary.replace(target)

        except Exception:
            # Удаляем незавершённый временный файл
            temporary.unlink(missing_ok=True)
            raise

    # Потоковое сохранение плана
    def save_plan(
        self,
        path: str | Path, # путь к файлу
        entries: Iterator[dict], # поток задач через yield
    ) -> None:
          
        target = Path(path)

        temporary = target.with_name(target.name + ".tmp")

        try:
            with open(temporary, "w", encoding="utf-8") as file:
                self._format.encode_plan(file, entries)

            # Заменяем целевой файл только после успешной записи всего потока
            temporary.replace(target)

        except Exception:
            # Удаляем незавершённый временный файл при сбое
            temporary.unlink(missing_ok=True)
            raise

    # Загрузка данных
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

    # Сериализация снимка
    def encode_snapshot(
        self,
        file,
        header: dict,
        entries: Iterator[dict]
    ) -> None:
        
        file.write('{\n    "node": ')
        json.dump(header["name"], file, ensure_ascii=False)

        file.write(',\n    "path": ')
        json.dump(header["path"], file, ensure_ascii=False)

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

    # Сериализация плана
    def encode_plan(
        self,
        file,
        entries: Iterator[dict]
    ) -> None:

        first = True
        
        for entry in entries:
            if not first:
                file.write(',\n')

            json.dump(
                entry,
                file,
                ensure_ascii=False
            )

            first = False


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
            header=node,
            entries=entries
        )

    # Сравнение снимков и подготовка к синхронизации
    def compare(self, snapshots: list, plan_path: str):     
        # Получение политики
        source = self.policy["sync"]["source"]
        destination = self.policy["sync"]["destination"]
        actions = set(self.policy["actions"])

        # Списки snapshots
        source_snapshots = []
        destination_snapshots = []

        # Получаем и распределяем snapshots
        for snapshot in snapshots:

            if snapshot["role"] == source:
                source_snapshots.append(snapshot)

            elif snapshot["role"] == destination:
                destination_snapshots.append(snapshot)

        # Добавляем задачу в план синхронизации
        self.file.save_plan( 
            path=plan_path, 
            entries=self._make_plan(
                actions=actions, 
                source_snapshots=source_snapshots,
                destination_snapshots=destination_snapshots
            )
        )
            
    # Генерация потока задач плана синхронизации
    def _make_plan(self, actions: set, source_snapshots: list, destination_snapshots: list) -> Iterator[dict]:
        # Сборка плана синхронизации
        for src in source_snapshots:
            for dest in destination_snapshots:
                src_snap = self.file.load(src["path"])
                dest_snap = self.file.load(dest["path"])

                # Собираем множество кортежей (путь, тип, размер, хэш) из снимка
                src_set = { 
                    (
                        item["path"],
                        item["type"],
                        item.get("size"),
                        item.get("hash"),
                    )
                    for item in src_snap.get("structure", [])
                }
                
                dest_set = {
                    (
                        item["path"],
                        item["type"],
                        item.get("size"),
                        item.get("hash"),
                    )
                    for item in dest_snap.get("structure", [])
                }

                # Оставляем только элементы из источника, которых нет или которые отличаются в назначении
                diff = src_set - dest_set

                # Собираем файлы отдельно: относительный путь -> (размер, хэш)
                dest_files = {
                    rel_path: (item_size, item_hash)
                    for rel_path, item_type, item_size, item_hash in dest_set
                    if item_type == "file"
                }

                # Перебираем элементы из разницы множеств
                for rel_path, item_type, size, file_hash in diff:
                    # Пропускаем папку
                    if item_type != "file":
                        continue

                    action = None

                    # Явно проверяем добавление нового файла
                    if "add" in actions and rel_path not in dest_files:
                        action = "add"

                    # Явно проверяем обновление существующего файла
                    if "update" in actions and rel_path in dest_files:
                        dest_size, dest_hash = dest_files[rel_path]
                        if file_hash != dest_hash or size != dest_size:
                            action = "update"

                    if action is None:
                        continue

                    yield {
                        "action": action,
                        "source": f"{src_snap['path']}/{rel_path.lstrip("/\\")}",
                        "destination": f"{dest_snap['path']}/{rel_path.lstrip("/\\")}",
                    }
                                                     
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
                    "hash": FileIdentity.get_hash(str(file_path)),
                }


class Sync:
    # Синхронизация данных
    def synchronize(self, plan):
        ...