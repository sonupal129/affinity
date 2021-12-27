

class BaseStrategy:
    name = "base_strategy"
    description = ""
    df_validated = False
    validation_initiated = False
    

    def __init__(self, *args, **kwargs) -> None:
        self.__dataframe = None
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
        self.__dataframe = dataframe
        
    
    def __strategy(self):
        pass
    
    @classmethod
    def dataframe_validation_done(cls):
        cls.validation_initiated = True
        cls.df_validated = True
    
    def is_valid_dataframe(self):
        if self.dataframe is None:
            raise AttributeError("dataframe value must be passed")
        if len(self.dataframe.index) > 50:
            self.__class__.dataframe_validation_done()
            return True
        print("dataframe should have minimum 50 rows")
        return False
    
    def get_signal(self):
        if not all([self.df_validated, self.validation_initiated]):
            print("please validate dataframe first by calling validate_dataframe function")
            return None
        return self.__strategy()


class SMAStrategy(BaseStrategy):
    name = "smarsistochastic_strategy"
    description = """7,10 SMA, 7,3,3 Stochastic and RSI Strategy"""

    def get_cleaned_dataframe(self):
        dataframe = super().get_cleaned_dataframe()
        return dataframe

    def strategy(self):
        return None

