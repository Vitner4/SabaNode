from saba.filesystem import *
from saba.lib.MicroLog.microlog import Logger


class Manager:
    def __init__(self):
        self.log = Logger()
        self.snapshot = Snapshot()
        self.file = File()

    def run(self):   
        self.log.info("Запуск программы!")
        # Test #


        # ДАННЫЕ #


        # node1 (main)
        node1 = {
            "name": "PC",
            "path": str(Path("~/.test-saba/PC").expanduser())
        }
        snapshot_path_node1 = "./snapshot_PC.json" # Путь до snapshot от node1

        # node2 (child)
        node2 = {
            "name": "Phone",
            "path": str(Path("~/.test-saba/Phone").expanduser())
        }
        snapshot_path_node2 = "./snapshot_Phone.json" # Путь до snapshot от node2

        # Данные о nodes, их ролях и путях к снимкам для сравнения (имитация получения данных из project.py)
        snapshots = [
            {
                "role": "Main",
                "path": snapshot_path_node1
            },
            {
                "role": "Child",
                "path": snapshot_path_node2
            }
        ]

        # ДЕЙСТВИЯ #

        # Создание Snapshots
        # self.snapshot.create(node1, snapshot_path_node1)
        # self.snapshot.create(node2, snapshot_path_node2)

        # Сравнение Snapshots
        self.snapshot.compare(snapshots)


        



        