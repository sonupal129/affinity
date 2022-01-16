import pandas as pd
from icecream import ic
from settings import *

# CODE
class BaseStrategy:
    name = "base_strategy"
    description = ""
    df_validated = False
    validation_initiated = False
    

    def __init__(self, **kwargs) -> None:
        self.__dataframe = kwargs.get("dataframe", None)
        self.__entry_signal = kwargs.get("signal", None)
        self.stoploss = kwargs.get("stoploss", DEFAULT_STOPLOSS)
        self.target = kwargs.get("target", DEFAULT_TARGET)
        if self.df_validated or self.validation_initiated:
            raise AttributeError("df_validated, or validation_initiated can not be true by default")
        if not self.name:
            raise AttributeError("strategy name is mandatory")
    
    @property
    def dataframe(self):
        return self.__dataframe
    
    @dataframe.setter
    def dataframe(self, dataframe):
        if not isinstance(dataframe, pd.DataFrame):
                raise TypeError("not valid dataframe")
        self.__dataframe = dataframe.copy()
        
    @property
    def entry_signal(self):
        return self.__entry_signal

    @entry_signal.setter
    def entry_signal(self, signal):
        self.__entry_signal = signal

    def strategy(self):
        print("this is valid")
        pass
    
    
    def clean_dataframe(self):
        self.dataframe = self.dataframe.dropna()

    def apply_indicator(self):
        """apply technical indicatory on dataframe for further strategy build or techni
        cal analysis"""
        self.dataframe["max_bid"] = self.dataframe[["bidopen","bidclose","bidlow","bidhigh"]].max(axis=1)
        self.dataframe["min_bid"] = self.dataframe[["bidopen","bidclose","bidlow","bidhigh"]].min(axis=1)

    @classmethod
    def dataframe_validation_done(cls):
        cls.validation_initiated = True
        cls.df_validated = True

    @staticmethod
    def get_target_price(price:float, target_amount:float, entry_type:str="BUY") -> float:
        """ by default entry type is buy"""
        if entry_type.upper() in ["SELL", "S"]:
            return price - target_amount
        return price + target_amount

    @staticmethod
    def get_stoploss_price(price:float, stoploss_amount:float, entry_type:str="BUY") -> float:
        """ by default entry type is buy"""
        if entry_type.upper() in ["SELL", "S"]:
            return price + stoploss_amount
        return price - stoploss_amount


    def is_valid_dataframe(self):
        if self.dataframe is None:
            raise AttributeError("dataframe value must be passed")
        if len(self.dataframe.index) > 50:
            self.__class__.dataframe_validation_done()
            self.apply_indicator()
            self.clean_dataframe()
            return True
        return False
    
    def get_signal(self):
        if not all([self.df_validated, self.validation_initiated]) or self.dataframe is None:
            print("please validate dataframe first by calling is_valid_dataframe function")
            return None
        return self.strategy()


class DefaultExitStrategy(BaseStrategy):
    name = "default exit strategy"

    def __init__(self, **kwargs) -> None:
        print(f"running {self.__class__.name} for the evaluation")
        super().__init__(**kwargs)

    def strategy(self):
        last_df_date = self.dataframe.tail(1).index[0]
        target_price = self.__class__.get_target_price(self.entry_signal.entry_price, self.target, self.entry_signal.entry_signal)
        stoploss_price = self.__class__.get_stoploss_price(self.entry_signal.entry_price, self.stoploss, self.entry_signal.entry_signal)
        filtered_df = self.dataframe[self.entry_signal.Index:last_df_date]

        def exit_price_fetcher(sl_hit_row, target_hit_row, entry_price:float, entry_type:str="BUY"):
            entry_row = pd.DataFrame()
            if sl_hit_row.empty and not target_hit_row.empty:
                entry_row = target_hit_row
            elif target_hit_row.empty and not sl_hit_row.empty:
                entry_row = sl_hit_row
            elif not all([target_hit_row.empty, sl_hit_row.empty]):
                row = min(target_hit_row, sl_hit_row, key= lambda k: k.index[0])
                entry_row = row
            
            # Need to check in which case rows are coming blank
            if entry_row.empty:
                return 0,0,0

            row_output_detail = [entry_row[["bidopen","bidclose","bidlow","bidhigh"]].max(axis=1).iloc[0], entry_row[["bidopen","bidclose","bidlow","bidhigh"]].min(axis=1).iloc[0], entry_row.iloc[0].name]
            if entry_type.upper() == "BUY":
                if row_output_detail[0] >= target_price:
                    del row_output_detail[1]
                    row_output_detail.append("TG")
                    return row_output_detail
                elif row_output_detail[1] <= stoploss_price:
                    del row_output_detail[0]
                    row_output_detail.append("SL")
                    return row_output_detail
            elif entry_type.upper() == "SELL":
                if row_output_detail[1] <= target_price:
                    del row_output_detail[0]
                    row_output_detail.append("TG")
                    return row_output_detail
                elif row_output_detail[0] >= stoploss_price:
                    del row_output_detail[1]
                    row_output_detail.append("SL")
                    return row_output_detail
            # need to check what else condition are left
            return 0,0,0
        
        if self.entry_signal.entry_signal == "BUY":
            target_hit = filtered_df.loc[(filtered_df["max_bid"] >= target_price)].head(1)
            sl_hit = filtered_df.loc[(filtered_df["min_bid"] <= stoploss_price)].head(1)
            return exit_price_fetcher(target_hit, sl_hit, self.entry_signal.entry_price, self.entry_signal.entry_signal)
        elif self.entry_signal.entry_signal == "SELL":
            target_hit = filtered_df.loc[(filtered_df["min_bid"]) <= target_price].head(1)
            sl_hit = filtered_df.loc[(filtered_df["max_bid"]) >= stoploss_price].head(1)
            return exit_price_fetcher(target_hit, sl_hit, self.entry_signal.entry_price, self.entry_signal.entry_signal)
    
