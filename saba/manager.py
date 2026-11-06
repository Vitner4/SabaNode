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
        node = {
            "name": "PC",
            "path": "YOUR_PATH",
        }
        snapshot_path = "./snapshot_now.json"

        self.snapshot.create(node, snapshot_path)



        