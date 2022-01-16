from authenticate import CreateConnection
from strategy import *
from settings import *
import numpy as np
import pandas as pd
from icecream import ic
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
        for row_number in range(1,len(self.df)):
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
        exit_strategy = self.exit_strategy()
        # last_df_date = self.df.tail(1).index[0]
        exit_strategy.dataframe = main_df

        for signal in signal_df.itertuples():
            exit_strategy.entry_signal = signal
            if exit_strategy.is_valid_dataframe():
                exit_details.append(exit_strategy.get_signal())
        
        signal_df["exit_price"] = [detail[0] for detail in exit_details]
        signal_df["exit_time"] = [detail[1] for detail in exit_details]
        signal_df["status"] = [detail[2] for detail in exit_details]
        return signal_df
            # target_price = self.entry_strategy.get_target_price(signal.entry_price, self.target, signal.entry_signal)
            # stoploss_price = self.entry_strategy.get_stoploss_price(signal.entry_price, self.stoploss, signal.entry_signal)
            # filtered_df = main_df[signal.Index:last_df_date]
            # if signal.entry_signal == "BUY":
            #     target_hit = filtered_df.loc[(filtered_df["max_bid"] >= target_price)].head(1)
            #     sl_hit = filtered_df.loc[(filtered_df["min_bid"] <= stoploss_price)].head(1)
            #     exit_details.append(sl_target_comparer(target_hit, sl_hit, signal.entry_price, signal.entry_signal))
            # elif signal.entry_signal == "SELL":
            #     target_hit = filtered_df.loc[(filtered_df["min_bid"]) <= target_price].head(1)
            #     sl_hit = filtered_df.loc[(filtered_df["max_bid"]) >= stoploss_price].head(1)
            #     exit_details.append(sl_target_comparer(target_hit, sl_hit, signal.entry_price, signal.entry_signal))
        

    # def __exit_strategy(self, signal_df, main_df):
    #     exit_details = []
    #     def sl_target_comparer(sl_hit_row, target_hit_row, entry_price:float, entry_type:str="BUY"):
    #             target_price = self.entry_strategy.get_target_price(entry_price, self.target, entry_type)
    #             stoploss_price = self.entry_strategy.get_stoploss_price(entry_price, self.stoploss, entry_type)

    #             def exit_price_fetcher(row, entry_type:str="BUY"):
    #                 row_output_detail = [row[["bidopen","bidclose","bidlow","bidhigh"]].max(axis=1).iloc[0], row[["bidopen","bidclose","bidlow","bidhigh"]].min(axis=1).iloc[0], row.iloc[0].name]
    #                 if entry_type.upper() == "BUY":
    #                     if row_output_detail[0] >= target_price:
    #                         del row_output_detail[1]
    #                         row_output_detail.append("TG")
    #                         return row_output_detail
    #                     elif row_output_detail[1] <= stoploss_price:
    #                         del row_output_detail[0]
    #                         row_output_detail.append("SL")
    #                         return row_output_detail
    #                 elif entry_type.upper() == "SELL":
    #                     if row_output_detail[1] <= target_price:
    #                         del row_output_detail[0]
    #                         row_output_detail.append("TG")
    #                         return row_output_detail
    #                     elif row_output_detail[0] >= stoploss_price:
    #                         del row_output_detail[1]
    #                         row_output_detail.append("SL")
    #                         return row_output_detail
                                    
    #             if sl_hit_row.empty and not target_hit_row.empty:
    #                 return exit_price_fetcher(target_hit_row, entry_type)
    #             elif target_hit_row.empty and not sl_hit_row.empty:
    #                 return exit_price_fetcher(sl_hit_row, entry_type)
    #             elif not all([target_hit_row.empty, sl_hit_row.empty]):
    #                 row = min(target_hit_row, sl_hit_row, key= lambda k: k.index[0])
    #                 return exit_price_fetcher(row, entry_type)
    #             return 0,0,0


    #     for signal in signal_df.itertuples():
    #         target_price = self.entry_strategy.get_target_price(signal.entry_price, self.target, signal.entry_signal)
    #         stoploss_price = self.entry_strategy.get_stoploss_price(signal.entry_price, self.stoploss, signal.entry_signal)
    #         filtered_df = main_df[signal.Index:last_df_date]
    #         if signal.entry_signal == "BUY":
    #             target_hit = filtered_df.loc[(filtered_df["max_bid"] >= target_price)].head(1)
    #             sl_hit = filtered_df.loc[(filtered_df["min_bid"] <= stoploss_price)].head(1)
    #             exit_details.append(sl_target_comparer(target_hit, sl_hit, signal.entry_price, signal.entry_signal))
    #         elif signal.entry_signal == "SELL":
    #             target_hit = filtered_df.loc[(filtered_df["min_bid"]) <= target_price].head(1)
    #             sl_hit = filtered_df.loc[(filtered_df["max_bid"]) >= stoploss_price].head(1)
    #             exit_details.append(sl_target_comparer(target_hit, sl_hit, signal.entry_price, signal.entry_signal))
        
        # signal_df["exit_price"] = [detail[0] for detail in exit_details]
        # signal_df["exit_time"] = [detail[1] for detail in exit_details]
        # signal_df["status"] = [detail[2] for detail in exit_details]

        # return signal_df

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
        # df = report
        df = pd.DataFrame(cleaned_data)
        qty = self.kwargs.get("order_quantity", 0)
        conditions = [
                (df['status'] == "SL") & (df["entry_signal"] == "BUY"),
                (df['status'] == "TG") & (df["entry_signal"] == "BUY"),
                (df['status'] == "SL") & (df["entry_signal"] == "SELL"),
                (df['status'] == "TG") & (df["entry_signal"] == "SELL"),
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
