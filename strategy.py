import pandas as pd

class BaseStrategy:
    name = "base_strategy"
    description = ""
    df_validated = False
    validation_initiated = False
    

    def __init__(self, *args, **kwargs) -> None:
        self.__dataframe = kwargs.get("dataframe", None)
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
        
    
    def strategy(self):
        print("this is valid")
        pass
    
    
    def clean_dataframe(self):
        self.dataframe = self.dataframe.dropna()

    def apply_indicator(self):
        """apply technical indicatory on dataframe for further strategy build or techni
        cal analysis"""
        pass

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


