from typing import Protocol
from lib.MicroLog.microlog import Logger


class Snapshot:
    def __init__(self):
        self.log = Logger()
        self.file = File()

    def create(self, node: str) -> None:
        ...


class FileIdentity:
    def __init__(self):
        self.log = Logger()


class File:
    def __init__(self):
        self.log = Logger()

