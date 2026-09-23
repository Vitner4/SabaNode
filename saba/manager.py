from lib.MicroLog.microlog import Logger


class Manager:
    def __init__(self):
        self.log = Logger()

    def run(self):   
        self.log.info("Запуск программы!")
        
