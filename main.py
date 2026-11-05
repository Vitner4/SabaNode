from saba import Manager
from saba.filesystem import *
from saba.lib.MicroLog.microlog import Logger


class Main:
    def __init__(self):
        self.manager = Manager()
        self.log = Logger()

    def main(self):
        try:      
            self.manager.run()

        except Exception as e:
            self.log.error(e)

        
if __name__ == "__main__":
    Main().main()

