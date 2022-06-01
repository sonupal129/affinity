import os, fxcmpy, json
import pandas as pd
from settings import *
from datetime import datetime
# CODE BLOCK
class Connection:

    def __init__(self):
        self.token = os.getenv("FXCM_TOKEN")
        self.connection = fxcmpy.fxcmpy(access_token=TOKEN, log_level=os.getenv("LOG_LEVEL", "error").lower(), \
                            server=os.getenv("SERVER", "demo").lower())

    def __repr__(self):
        return self.connection

    def close(self):
        self.connection.close()
        return True
    

# connection = Connection()

class FindEntry(object):

    def __init__(self):
        pass

    def find_entry(self, entry_strategy, df, **kwargs):
        strategy = entry_strategy(stoploss=kwargs.get("stoploss", DEFAULT_STOPLOSS), target=kwargs.get("target", DEFAULT_TARGET) \
                    )
        strategy.dataframe = df
        strategy.is_valid_dataframe()
        signal = strategy.get_signal()
        return signal

class FindExit(FindEntry):

    def find_exit(self, exit_strategy, entry_signal, df, **kwargs):
        strategy = exit_strategy(stoploss=kwargs.get("stoploss", DEFAULT_STOPLOSS), target=kwargs.get("target", DEFAULT_TARGET) \
                    )
        strategy.dataframe = df
        strategy.entry_signal = entry_signal
        strategy.is_valid_dataframe()
        signal = strategy.get_signal()
        return signal


class OrderBook:

    def __init__(self):
        self.book_name = f"order_book_{str(datetime.today().date())}.json"

    def _update_order_book(self, data:list=None):
        default_data = {
            "book_date": str(datetime.today().date()),
            "orders": data
        }
        with open(self.book_name, "w+") as order_book:
            json.dump(default_data, order_book, default=str)
        return True

    def add_new_order(self, entry_order, order_type="ENTRY", exit_signal=None):
        if not os.path.exists(self.book_name):
           self._update_order_book()
        else:
            book_data = self.read_order_book()
            
            if not book_data:
                book_data = {
                    entry_order.time : [
                        entry_order,
                        order_type,
                        exit_signal
                    ]
                }
                self._update_order_book(book_data)
                return True
            else:
                if order_type.lower() == "entry":
                    if is_order_in_book(entry_order):
                        return False
                    book_data[entry_order.time] = [
                        entry_order,
                        order_type,
                        exit_signal
                    ]
                    self._update_order_book(book_data)
                    return True
                elif order_type.lower() == "exit":
                    if is_order_in_book(entry_order):
                        order = order_book[entry_order.time]
                        if order[2] == exit_signal:
                            return False
                        book_data[entry_order.time] = [
                            entry_order,
                            order_type,
                            exit_signal
                        ]
                        self._update_order_book(book_data)
                        return True
                    return False
            return False
                    

    def read_order_book(self):
        if not os.path.exists(self.book_name):
            self._update_order_book()
        with open(self.book_name, "r") as order_book:
            book = json.load(order_book)
        return book["orders"]

    def is_order_in_book(self, entry_order):
        book_data = self.read_order_book()
        if book_data:
            if entry_order.time in book_data.keys():
                True
        return False

    def get_last_order(self):
        if not os.path.exists(self.book_name):
            return None
        book_data = self.read_order_book()
        if not book_data:
            return None
        else:
            pass
            # Put code for sorting
        
    def is_last_order_open(self):
        last_order = self.get_last_order()
        if last_order[2]:
            return False
        return True

def start_entry_trading(entry,  **kwargs):
    df = connection.get_candles('EUR/USD', period='m1', number=250)
    entry_signal = FindEntry(entry, df, **kwargs)
    order_book = OrderBook()
    if entry_signal:
        last_order = order_book.get_last_order()
        if last_order_df.entry_signal == entry_signal.entry_signal and order_book.add_new_order(entry_signal):
            print("Entry signal found placing a new order")
            order = connection.create_entry_order(
                        symbol='EUR/USD',
                        is_buy=True if entry_signal.entry_signal == "BUY" else False
                        rate=entry_signal.entry_price
                        is_in_pips=False,
                        time_in_force='GTD'
                    )
        else:
            if order_book.is_last_order_open():
                pass
            else:
                if order_book.add_new_order(entry_signal):
                    print("Entry signal found placing a new order")
                    order = connection.create_entry_order(
                        symbol='EUR/USD',
                        is_buy=True if entry_signal.entry_signal == "BUY" else False
                        rate=entry_signal.entry_price
                        is_in_pips=False,
                        time_in_force='GTD'
                    )
    






    

        


