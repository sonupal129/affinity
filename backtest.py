from .authenticate import CreateConnection
from .strategy import *
from settings import API_KEY, SERVER
# Code Below

class BackTestStrategy:

    def __init__(self, strategy, dataframe) -> None:
        self.strategy = strategy
        self.df = dataframe
        self.__backtest_complete = False
        self.__report = None
        self.__signal_data = []

    def start_backtesting(self, *args, **kwargs):
        for frame in self.df:
            signal_found = self.strategy(frame, *args, **kwargs).get_signal()
            if signal_found:
                self.__signal_data.append(signal_found)
                
        self.__report = "Report"

    @property
    def backtest_complete(self):
        return self.__backtest_complete

    @backtest_complete.setter
    def backtest_complete(self, completed:bool):
        self.__backtest_complete = completed

    def get_report(self):
        if self.backtest_complete:
            return self.__report
        return None
    
