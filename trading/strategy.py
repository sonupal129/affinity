import pandas as pd
from icecream import ic
import numpy as np
from ta.trend import *
from ta.momentum import *


# CODE
class BaseStrategy:
    name = "base_strategy"
    description = ""
    

    def __init__(self, **kwargs) -> None:
        self.__dataframe = kwargs.get("dataframe", None)
        self.__entry_signal = kwargs.get("signal", None)
        self.stoploss = kwargs.get("stoploss", None)
        self.target = kwargs.get("target", None)
        if not self.name:
            raise AttributeError("strategy name is mandatory")
    
    @property
    def dataframe(self):
        return self.__dataframe
    
    @dataframe.setter
    def dataframe(self, dataframe):
        if not isinstance(dataframe, pd.DataFrame):
                raise TypeError("not valid dataframe")
        try:
            delattr(self, "df_validated")
        except:
            pass
        self.__dataframe = dataframe.copy()
        
    @property
    def entry_signal(self):
        return self.__entry_signal

    @entry_signal.setter
    def entry_signal(self, signal):
        self.__entry_signal = signal

    def strategy(self):
        raise NotImplementedError('`strategy()` must be implemented')
    
    
    def clean_dataframe(self):
        self.dataframe = self.dataframe.dropna()

    def apply_indicator(self):
        """apply technical indicatory on dataframe for further strategy build or technical analysis"""
        self.dataframe["max_bid"] = self.dataframe[["bidopen","bidclose","bidlow","bidhigh"]].max(axis=1)
        self.dataframe["min_bid"] = self.dataframe[["bidopen","bidclose","bidlow","bidhigh"]].min(axis=1)


    @staticmethod
    def get_target_price(price:float, target_amount:float, entry_type:str="BUY"):
        """ by default entry type is buy"""
        if entry_type.upper() in ["SELL", "S"]:
            return price - target_amount
        return price + target_amount

    @staticmethod
    def get_stoploss_price(price:float, stoploss_amount:float, entry_type:str="BUY"):
        """ by default entry type is buy"""
        if entry_type.upper() in ["SELL", "S"]:
            return price + stoploss_amount
        return price - stoploss_amount


    def is_valid_dataframe(self):
        if self.dataframe is None:
            raise AttributeError("dataframe value must be passed")
        if len(self.dataframe.index) > 50:
            setattr(self, "df_validated", True)
            self.apply_indicator()
            self.clean_dataframe()
            return True
        return False
    
    def get_signal(self):
        # Need to look at it later
        # assert hasattr(self, "df_validated"), (
        #     "Dataframe validation not done, kindly call `is_valid_dataframe()` function first"
        # )
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
    


class SMAStrategy3Exit(BaseStrategy):
    name = "smacrossover_with_smahit_strategy"
    description = """7,10 SMA"""  
    
    def signal_found(self, data):
        return data.to_dict()
    
    def strategy(self):
        """optimization required"""
        df = self.dataframe
        signal = self.entry_signal
        target = self.__class__.get_target_price(signal.entry_price, self.target, signal.entry_signal)
        stoploss = self.__class__.get_stoploss_price(signal.entry_price, self.stoploss, signal.entry_signal)
        df_last_date = df.tail(1).index[0]
        temp_df = df[:signal.Index][-10:]
        rows_min = min(temp_df.min_bid)
        rows_max = max(temp_df.max_bid)
        slp_price= 0.0002
        tgp_price = 0.0002
        new_df = df[signal.Index:df_last_date].iloc[1: , :][:100]
        exit_price = 0
        exit_time = None
        status = ""
        rsi_high_hit = 0
        rsi_low_hit = 0
        
        def last_prices_fetcher(price:float, storage:list):
            if len(storage) == 4:
                storage.append(price)
                storage.pop(0)
            else:
                storage.append(price)
            return storage
        
        def get_trend(price_list:list):
            avr = round(sum(price_list) / len(price_list), 5)
            # ic(price_list[-1] - avr)
            if price_list[-1] > avr:
                return "UP"
            elif price_list[-1] < avr:
                return "DOWN"
            else:
                return "SIDE"
        
        if signal.entry_signal == "BUY":
            last_row = None
            new_sl = min(signal.bidopen - slp_price, rows_min)
            new_tgp_row = None
            last_prices = []
            down_trend_counter = 0
            target_hit = False
            last_trend = ""
            for row in new_df.itertuples():
                last_prices_fetcher(row.bidclose, last_prices)
                trend = get_trend(last_prices)
                if last_row == None:
                    last_row = row
                if last_row.rsi > 70 and row.rsi < 70:
                    rsi_high_hit += 1
                if last_row.rsi < 30 and row.rsi > 30:
                    rsi_low_hit += 1
                
                # ic(last_row.rsi > 70 and row.rsi < 70)
                # ic(row.max_bid >= target)
                # ic(row)
                # ic(target)
                if new_tgp_row == None:
                    if row.max_bid >= signal.bidclose + tgp_price:
                        new_tgp_row = row  
                elif row.max_bid >= target:
                    target_hit = True
                    if row.rsi < 67:
                        exit_price = row.bidclose
                        exit_time = row.Index
                        status = "TG"
                        break
                elif row.min_bid <= new_sl:
                    exit_price = row.bidclose
                    exit_time = row.Index
                    status = "SLPR"
                    break
                elif row.bidclose <= stoploss:
                    exit_price = row.bidclose
                    exit_time = row.Index
                    status = "SL"
                    break
                # elif last_row.rsi > 71:
                #     tgp_broken = True
                # elif tgp_broken:
                #     if row.rsi < 50:
                #         exit_price = row.bidclose
                #         exit_time = row.Index
                #         status = "TGP"
                
                elif last_row.rsi > 70 and row.rsi < 70:
                    exit_price = row.bidclose
                    exit_time = row.Index
                    status = "TGP"
                    break
                last_row = row
                last_trend = trend
        elif signal.entry_signal == "SELL":
            last_row = None
            new_sl = max(rows_max, signal.bidopen + slp_price)
            new_tgp_row = None
            last_prices = []
            down_trend_counter = 0
            target_hit = False
            last_trend = ""
            for row in new_df.itertuples():
                last_prices_fetcher(row.bidclose, last_prices)
                trend = get_trend(last_prices)
                if last_row == None:
                    last_row = row
                if last_row.rsi > 30 and row.rsi < 30:
                    rsi_high_hit += 1
                if last_row.rsi < 70 and row.rsi > 70:
                    rsi_low_hit += 1
                if new_tgp_row == None:
                    if row.min_bid <= signal.bidclose - tgp_price:
                        new_tgp_row = row 
                elif row.min_bid <= target:
                    target_hit = True
                    if row.rsi > 33:
                        exit_price = row.bidclose
                        exit_time = row.Index
                        status = "TG"
                        break
                elif row.max_bid >= new_sl:
                    exit_price = row.bidclose
                    exit_time = row.Index
                    status = "SLPR"
                    break
                elif row.bidclose >= stoploss:
                    exit_price = row.bidclose
                    exit_time = row.Index
                    status = "SL"
                    break
                # elif last_row.rsi < 29:
                #     tgp_broken = True
                # elif tgp_broken:
                #     if row.rsi > 50:
                #         exit_price = row.bidclose
                #         exit_time = row.Index
                #         status = "TGP"
                elif last_row.rsi < 30 and row.rsi > 30:
                    exit_price = row.bidclose
                    exit_time = row.Index
                    status = "TGP"
                    break
                last_row = row
                last_trend = trend
        if all([exit_price, status, exit_time]):
            return exit_price, exit_time, status
        return 0,0,0

    
    def apply_indicator(self):
        super(self.__class__, self).apply_indicator()
        self.dataframe["small_sma"]=SMAIndicator(self.dataframe.bidclose, window=7).sma_indicator()
        self.dataframe["large_sma"]=SMAIndicator(self.dataframe.bidclose, window=10).sma_indicator()
        self.dataframe["rsi"] = rsi(self.dataframe.bidclose, 10)
        self.dataframe = self.dataframe.replace({np.nan: None})
        self.dataframe["rsi_signal"] = list(self.rsi_signal_maker())
        self.dataframe["sma_signal"] = list(self.sma_signal_maker())
        
        
                
    def sma_signal_maker(self):
        """function required more optimized logic"""
        last_row = None
        for row in self.dataframe.itertuples():
            if last_row == None:
                last_row = row
            if not all([row.small_sma, row.large_sma, last_row.small_sma, last_row.large_sma]):
                yield ""
                last_row = row
                continue
            elif row.small_sma < row.large_sma and last_row.small_sma > last_row.large_sma:
                yield "DOWN_CROSSOVER"
            elif row.small_sma > row.large_sma and last_row.small_sma < last_row.large_sma:
                yield "UP_CROSSOVER"
            else:
                yield ""
            last_row = row

        
    def rsi_signal_maker(self):
        last_value = 0
        for value in self.dataframe.rsi:
            if value == None:
                yield ""
                continue
            if last_value <= 30 and value > 30:
                yield "UP_REVERSE"
            elif last_value >=70 and value < 70:
                yield "DOWN_REVERSE"
            else:
                yield ""
            last_value = value
            
    

    
class SMAExitLevel1(BaseStrategy):
    
    def get_next_entry_signal(self):
        strategy = SMAStrategy3Level1(stoploss=self.stoploss, target=self.target)
        df = self.dataframe.copy()
        new_df = df[self.entry_signal.Index:]
        if new_df.empty:
            return None
        # this is temporary code for testing it need optimization
        for date_index in new_df.index:
            strategy.dataframe = df[:date_index]
            strategy.is_valid_dataframe()
            signal = strategy.get_signal()
            if signal:
                signal_df = pd.DataFrame(signal).iloc[0]
                if signal_df.name <= self.entry_signal.Index:
                    continue
                return signal
        return None
    
    def strategy(self):
        df = self.dataframe.copy()
        stoploss_price = self.__class__.get_stoploss_price(self.entry_signal.entry_price, self.stoploss, self.entry_signal.entry_signal)
        exit_strategy = SMAStrategy3Exit(target=self.target, stoploss=self.stoploss)
        exit_strategy.dataframe = df
        exit_strategy.entry_signal = self.entry_signal
        exit_strategy.is_valid_dataframe()
        exit_signal = exit_strategy.get_signal()
        
        # return exit_signal
        next_entry_signal = self.get_next_entry_signal()
        # ic(next_entry_signal)
        if next_entry_signal:
            next_entry_signal = pd.DataFrame(next_entry_signal).iloc[0]
        else:
            next_entry_signal = pd.DataFrame()
        
        if exit_signal == (0,0,0):
            new_df = self.dataframe[self.entry_signal.Index:]
            counter = 0
            for frame in new_df.itertuples():
                if self.entry_signal.entry_signal == "BUY" and frame.bidclose <= stoploss_price:
                    return frame.bidclose, frame.Index, "SL"
                elif self.entry_signal.entry_signal == "SELL" and frame.bidclose >= stoploss_price:
                    return frame.bidclose, frame.Index, "SL"
        elif exit_signal == (0,0,0) and not next_entry_signal.empty:
            next_entry_time = next_entry_signal.name
            signal_entry_time = self.entry_signal.Index
            if next_entry_time > signal_entry_time:
                if self.entry_signal.entry_signal == "SELL" and next_entry_signal.entry_signal == "SELL":
                    if self.entry_signal.bidclose - next_entry_signal.bidclose < -0.0002:
                        return next_entry_signal.bidclose, next_entry_time, "SLPR"
                elif self.entry_signal.entry_signal == "SELL" and next_entry_signal.entry_signal == "BUY":
#                     for time being exit all entry
                    return next_entry_signal.bidclose, next_entry_time, "TGP"
                elif self.entry_signal.entry_signal == "BUY" and next_entry_signal.entry_signal == "BUY":
                    if self.entry_signal.bidclose - next_entry_signal.bidclose > 0.0002:
                        return next_entry_signal.bidclose, next_entry_time, "SLPR"
                elif self.entry_signal.entry_signal == "BUY" and next_entry_signal.entry_signal == "SELL":
                # for time being exit and take new entry      
                    return next_entry_signal.bidclose, next_entry_time, "SLPR"
        return exit_signal


class SMAStrategy3Level1(BaseStrategy):
    name = "smacrossover_with_smahit_strategy"
    description = """7,10 SMA"""
    
    
    def signal_found(self, data):
        return data.to_dict()
    
    
    def create_signal(self, data, **kwargs):
        d_date = data.index[0]
        d = data.to_dict()
        d["entry_price"] = d["bidclose"]
        d["entry_signal"] = {d_date: kwargs.get("signal")}
        current_signal_df = pd.DataFrame(d).iloc[0]
        return d
    
    def strategy1(self):
        """optimization required"""
        df = self.dataframe
        last_sma_crossover = df.loc[(df["rsi_signal"] == "UP_REVERSE") | (df["rsi_signal"] == "DOWN_REVERSE")].iloc[-1]
        second_last_sma_crossover = df.loc[(df["rsi_signal"] == "UP_REVERSE") | (df["rsi_signal"] == "DOWN_REVERSE")].iloc[-2]
        new_df = df[second_last_sma_crossover.name:last_sma_crossover.name]
        new_df = new_df.iloc[::-1]
        signal = None
        data = pd.DataFrame()
        last_entry_signal = self.get_last_signal()
        last_entry_signal = next(pd.DataFrame(last_entry_signal).itertuples())
        tragedy = SMAStrategy3Exit(target=self.target, stoploss=self.stoploss)
        tragedy.dataframe = df
        tragedy.entry_signal = last_entry_signal
        tragedy.is_valid_dataframe()
        last_exit_signal= tragedy.get_signal()
        # ic(last_exit_signal)
        # ic(last_entry_signal.Index, last_entry_signal.bidclose)
        def get_trend(df):
            last_row_price = df.iloc[0].bidclose
            avr = round(df.iloc[:6].bidclose.sum() / 6, 5)
            if last_row_price > avr:
                return "UP"
            elif last_row_price < avr:
                return "DOWN"
            else:
                return "SIDE"
        
        if last_sma_crossover.rsi_signal == "UP_REVERSE" and not new_df.empty:
            signal = "BUY"
            valid_row = 0
            for row in new_df[1:4].itertuples():
                if max(row.bidopen, row.bidclose) < row.small_sma:
                    valid_row += 1
            if valid_row >= 2:
                data = new_df[last_sma_crossover.name : last_sma_crossover.name]
        elif last_sma_crossover.rsi_signal == "DOWN_REVERSE" and not new_df.empty:
            signal = "SELL"
            valid_row = 0
            for row in new_df[1:4].itertuples():
                if min(row.bidopen, row.bidclose) > row.small_sma:
                    valid_row += 1
            if valid_row >= 2:
                data = new_df[last_sma_crossover.name : last_sma_crossover.name]
        sma_crossover_counter = 0
        try:
            last_crossover = new_df.loc[(new_df["sma_signal_1"] == "UP_CROSSOVER") | (new_df["sma_signal_1"] == "DOWN_CROSSOVER")].iloc[-0]
        except:
            last_crossover = pd.DataFrame()
        for row in new_df.itertuples():
            if row.sma_signal_1.endswith("CROSSOVER"):
                break
            else:
                sma_crossover_counter += 1
                
        if not data.empty and signal == last_entry_signal.entry_signal:
            if "SLPR" in last_exit_signal:
                if (pd.Timestamp(data.index[0]) - pd.Timestamp(last_exit_signal[1])) / pd.Timedelta(minutes=1) < 13:
                    return None
                elif not last_crossover.empty:
                    if signal == "SELL" and last_crossover.sma_signal_1 == "UP_CROSSOVER" and sma_crossover_counter > 14:
                        return None
                    elif signal == "BUY" and last_crossover.sma_signal_1 == "DOWN_CROSSOVER" and sma_crossover_counter > 14:
                        return None
            elif last_exit_signal == (0,0,0):
                if (pd.Timestamp(data.index[0]) - pd.Timestamp(last_entry_signal.Index)) / pd.Timedelta(minutes=1) < 13:
                    return None

        if last_exit_signal[2] == "TG" and not data.empty:
            entry_diff = (pd.Timestamp(data.iloc[0].name) - pd.Timestamp(last_exit_signal[1])) / pd.Timedelta(minutes=1)
            if signal != last_entry_signal.entry_signal and entry_diff <= 15:
                ic(last_exit_signal)
                ic(last_entry_signal)
                return self.create_signal(data, signal=last_entry_signal.entry_signal)
        
        
        if not last_crossover.empty:
            if signal == "SELL" and last_crossover.sma_signal_1 == "UP_CROSSOVER" and sma_crossover_counter > 14:
                return None
            elif signal == "BUY" and last_crossover.sma_signal_1 == "DOWN_CROSSOVER" and sma_crossover_counter > 14:
                return None
        
        if signal and not data.empty:
            return self.create_signal(data, signal=signal)
        return None
       
    
    def get_previous_signal(self):
        negative_looper = list(range(-9,-1))[::-1]
        first_num = negative_looper[0]
        for n in negative_looper[1:]:
            signal = self.get_current_signal(last_signal_value=first_num, second_last_signal_value=n)
            if signal:
                return signal
            first_num = n
        return None

    
    def get_current_signal(self, **kwargs):
        """optimization required"""
        df = kwargs.get("dataframe", self.dataframe)
        last_sma_crossover = df.loc[(df["rsi_signal"] == "UP_REVERSE") | (df["rsi_signal"] == "DOWN_REVERSE")].iloc[kwargs.get("last_signal_value", -1)]
        second_last_sma_crossover = df.loc[(df["rsi_signal"] == "UP_REVERSE") | (df["rsi_signal"] == "DOWN_REVERSE")].iloc[kwargs.get("second_last_signal_value", -2)]
        new_df = df[:last_sma_crossover.name]
        new_df = new_df.iloc[::-1]
        signal = None
        data = pd.DataFrame()
        
        if last_sma_crossover.rsi_signal == "UP_REVERSE" and not new_df.empty:
            signal = "BUY"
            valid_row = 0
            for row in new_df[1:4].itertuples():
                if max(row.bidopen, row.bidclose) < row.small_sma:
                    valid_row += 1
            if valid_row >= 2:
                data = new_df[last_sma_crossover.name : last_sma_crossover.name]
        elif last_sma_crossover.rsi_signal == "DOWN_REVERSE" and not new_df.empty:
            signal = "SELL"
            valid_row = 0
            for row in new_df[1:4].itertuples():
                if min(row.bidopen, row.bidclose) > row.small_sma:
                    valid_row += 1
            if valid_row >= 2:
                data = new_df[last_sma_crossover.name : last_sma_crossover.name]
        
        if signal and not data.empty:
            return self.create_signal(data, signal=signal)
        return None
    
    def strategy(self, **kwargs):
        df = self.dataframe
        last_sma_crossover = df.loc[(df["rsi_signal"] == "UP_REVERSE") | (df["rsi_signal"] == "DOWN_REVERSE")].iloc[-1]
        second_last_sma_crossover = df.loc[(df["rsi_signal"] == "UP_REVERSE") | (df["rsi_signal"] == "DOWN_REVERSE")].iloc[-2]
        new_df = df[second_last_sma_crossover.name:last_sma_crossover.name]
        new_df = new_df.iloc[::-1]
        signal = None
        data = pd.DataFrame()
        
        if last_sma_crossover.rsi_signal == "UP_REVERSE" and not new_df.empty:
            signal = "BUY"
            valid_row = 0
            for row in new_df[1:4].itertuples():
                if max(row.bidopen, row.bidclose) < row.small_sma:
                    valid_row += 1
            if valid_row >= 2:
                data = new_df[last_sma_crossover.name : last_sma_crossover.name]
        elif last_sma_crossover.rsi_signal == "DOWN_REVERSE" and not new_df.empty:
            signal = "SELL"
            valid_row = 0
            for row in new_df[1:4].itertuples():
                if min(row.bidopen, row.bidclose) > row.small_sma:
                    valid_row += 1
            if valid_row >= 2:
                data = new_df[last_sma_crossover.name : last_sma_crossover.name]
        
        if signal and not data.empty:
            return self.create_signal(data, signal=signal)
        return None
        

    
    def apply_indicator(self):
        super(self.__class__, self).apply_indicator()
        self.dataframe["small_sma"]=SMAIndicator(self.dataframe.bidclose, window=7).sma_indicator()
        self.dataframe["large_sma"]=SMAIndicator(self.dataframe.bidclose, window=10).sma_indicator()
        self.dataframe["rsi"] = rsi(self.dataframe.bidclose, 10)
        self.dataframe = self.dataframe.replace({np.nan: None})
        self.dataframe["rsi_signal"] = list(self.rsi_signal_maker())
        self.dataframe["sma_signal"] = list(self.sma_signal_maker())
        
    
                
    def sma_signal_maker(self):
        """function required more optimized logic"""
        last_row = None
        for row in self.dataframe.itertuples():
            if last_row == None:
                last_row = row
            if not all([row.small_sma, row.large_sma, last_row.small_sma, last_row.large_sma]):
                yield ""
                last_row = row
                continue
            elif row.small_sma < row.large_sma and last_row.small_sma > last_row.large_sma:
                yield "DOWN_CROSSOVER"
            elif row.small_sma > row.large_sma and last_row.small_sma < last_row.large_sma:
                yield "UP_CROSSOVER"
            else:
                yield ""
            last_row = row

        
    def rsi_signal_maker(self):
        last_value = 0
        for value in self.dataframe.rsi:
            if value == None:
                yield ""
                continue
            if last_value <= 30 and value > 30:
                yield "UP_REVERSE"
            elif last_value >=70 and value < 70:
                yield "DOWN_REVERSE"
            else:
                yield ""
            last_value = value

        


class Level3(BaseStrategy):
        
    def get_current_signal(self, df, **kwargs):
        df1 = df.copy()
        df2 = df.copy()
        strategy = SMAStrategy3Level1(stoploss=self.stoploss, target=self.target)
        strategy.dataframe = df1
        strategy.is_valid_dataframe()
        current_signal = strategy.get_current_signal()
        previous_signal = strategy.get_previous_signal()
        if kwargs.get("need_previous_signal"):
            setattr(self, "_previous_signal", previous_signal)
        exit_strategy = SMAStrategy3Exit(stoplos=self.stoploss, target=self.target)
        exit_strategy.dataframe = df2
        exit_strategy.entry_signal = next(pd.DataFrame(previous_signal).itertuples())
        exit_strategy.is_valid_dataframe()
        last_exit_signal= exit_strategy.get_signal()
        # print(last_exit_signal, "exit signal for last entry siignal")
        # print(current_signal, "current signal")
        # print(previous_signal, "last signal")
        try:
            current_signal_df = next(pd.DataFrame(current_signal).itertuples())
        except:
            current_signal_df = pd.DataFrame()
            
        try:
            last_signal_df = next(pd.DataFrame(previous_signal).itertuples())
        except:
            last_signal_df = pd.DataFrame()
            
        if last_exit_signal and last_exit_signal[2] == "TG" and current_signal:
            entry_diff = (pd.Timestamp(current_signal_df.Index) - pd.Timestamp(last_exit_signal[1])) / pd.Timedelta(minutes=1)
            if current_signal_df.entry_signal != last_signal_df.entry_signal and entry_diff <= 15:
                sig_time, entry = list(*current_signal["entry_signal"].items())
                current_signal["entry_signal"] = {sig_time:last_signal_df.entry_signal}
                return current_signal
        if last_exit_signal == (0,0,0) and current_signal:
            last_entry_signal_price = last_signal_df.bidclose
            current_entry_signal_price = current_signal_df.bidclose
            diff = 0
            if last_signal_df.entry_signal == "BUY":
                diff = current_entry_signal_price - last_entry_signal_price
            else:
                diff = last_entry_signal_price - current_entry_signal_price
            
            if diff <= -0.0003:
                return None
            elif diff >= 0.0003:
                sig_time, entry = list(*current_signal["entry_signal"].items())
                current_signal["entry_signal"] = {sig_time:last_signal_df.entry_signal}
        return current_signal
    
    def strategy(self):
        df = self.dataframe.copy()
        current_signal = self.get_current_signal(df, need_previous_signal=True)
        # sig_time, entry = list(*self._previous_signal["entry_signal"].items())
        # previous_signal = self.get_current_signal(df[:sig_time])
        # print(previous_signal)
        # actual_previous_signal = 
        
        return current_signal