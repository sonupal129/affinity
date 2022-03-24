from authenticate import CreateConnection
from strategy import *
from settings import *
import numpy as np
import pandas as pd
from icecream import ic
from tqdm.notebook import trange, tqdm
import time
# Code Below

class BackTestStrategy:

    def __init__(self, entry_strategy, dataframe, **kwargs) -> None:
        self.entry_strategy = entry_strategy
        self.exit_strategy = kwargs.get("exit_strategy", DefaultExitStrategy)
        self.df = dataframe.copy()
        self.stoploss = kwargs.get("stoploss", DEFAULT_STOPLOSS)
        self.target = kwargs.get("target", DEFAULT_TARGET)
        self.kwargs = kwargs
        self.__backtest_complete = False
        self.__report = pd.DataFrame()
        self.__signal_data = None

    @property
    def signal_data(self):
        return self.__signal_data

    def push_signal_data(self, data:dict):
        if self.__signal_data is None:
            self.__signal_data = data
        else:
            for d in self.__signal_data.keys():
                for key, value in data[d].items():
                    self.__signal_data[d][key] = value
        return True

    def start_backtesting(self, *args, **kwargs):
        strategy = self.entry_strategy()
        for row_number in trange(1,len(self.df)):
            time.sleep(0.01)
            strategy.dataframe = self.df.head(row_number)
            if strategy.is_valid_dataframe():
                signal = strategy.get_signal()
                if signal:
                    self.push_signal_data(signal)
        self.__backtest_complete = True
        return "backtesting has been completed, please generate report"                

    @property
    def backtest_complete(self):
        return self.__backtest_complete

    def run_exit_strategy(self, signal_df, main_df):
        exit_details = []
        exit_strategy = self.exit_strategy(stoploss=self.stoploss, target=self.target)
        exit_strategy.dataframe = main_df


        for signal in signal_df.itertuples():
            exit_strategy.entry_signal = signal
            if exit_strategy.is_valid_dataframe():
                exit_details.append(exit_strategy.get_signal())
        
        signal_df["exit_price"] = [detail[0] for detail in exit_details]
        signal_df["exit_time"] = [detail[1] for detail in exit_details]
        signal_df["status"] = [detail[2] for detail in exit_details]
        return signal_df
        

    def is_valid_signal_df(self, column_names:list, signal_df):
        signal_column = signal_df.columns
        for column in column_names:
            if column not in signal_column:
                raise AttributeError(f"{column} is mandatory")
        return True

    def clean_report(self, report):
        cleaned_data = []
        for r in report.itertuples():
            if len(cleaned_data) == 0:
                cleaned_data.append(r)
                continue
            last_row = cleaned_data[-1]
            if r.exit_time == 0 or last_row.exit_time == 0:
                cleaned_data.append(r)
                continue
            if r.Index < last_row.exit_time:
                continue
            else:
                cleaned_data.append(r)
        df = report
        # df = pd.DataFrame(cleaned_data)
        qty = self.kwargs.get("order_quantity", 0)
        conditions = [
                ((df['status'] == "SL") | (df['status'] == "SLP") | (df['status'] == "SLPR")) & (df["entry_signal"] == "BUY"),
                ((df['status'] == "TG") | (df['status'] == "TGP")) & (df["entry_signal"] == "BUY"),
                ((df['status'] == "SL") | (df['status'] == "SLP") | (df['status'] == "SLPR")) & (df["entry_signal"] == "SELL"),
                ((df['status'] == "TG") | (df['status'] == "TGP")) & (df["entry_signal"] == "SELL"),
                ]
        values = [
                    df["exit_price"] - df["entry_price"],
                    df["exit_price"] - df["entry_price"],
                    df["entry_price"] - df["exit_price"],
                    df["entry_price"] - df["exit_price"]
                ]
        df["pip"] = np.select(conditions, values)
        df["pl"] = df["pip"] * qty
        return df

    def get_report(self):
        if self.__backtest_complete:
            if not self.__report.empty:
                return self.__report
            signal_df = pd.DataFrame.from_dict(self.signal_data)
            self.is_valid_signal_df(["entry_price", "entry_signal"], signal_df)
            df = self.df
            df["max_bid"] = df[["bidopen","bidclose","bidlow","bidhigh"]].max(axis=1)
            df["min_bid"] = df[["bidopen","bidclose","bidlow","bidhigh"]].min(axis=1)
            signal_df["max_bid"] = signal_df[["bidopen","bidclose","bidlow","bidhigh"]].max(axis=1)
            signal_df["min_bid"] = signal_df[["bidopen","bidclose","bidlow","bidhigh"]].min(axis=1)
            report = self.run_exit_strategy(signal_df, df)
            self.__report = self.clean_report(report)
            return self.__report
        return "Report not available yet"
