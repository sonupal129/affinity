import os, fxcmpy, json, logging, requests
import datetime
import time as gtime
from trading.strategy import SMAExitLevel1, SMAStrategy3Level1
from trading.models import *
import pandas as pd
import time

# CODE BLOCK

TOKEN = "5b6de8dc3b260ab0fab6e007bf21c43ee4fc7a27"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
class Connection:

    def __init__(self):
        self.token = os.getenv("FXCM_TOKEN")
        self.__connection = None

    @property
    def connection(self):
        if self.__connection and self.__connection.is_connected():
            return self.__connection
        return self.connect()

    @connection.setter
    def connection(self, con):
        self.__connection = con

    def connect(self):
        con = fxcmpy.fxcmpy(access_token=TOKEN, log_level=os.getenv("LOG_LEVEL", "error").lower(), \
                            server=os.getenv("SERVER", "demo").lower())
        while not con.is_connected():
            con = fxcmpy.fxcmpy(access_token=TOKEN, log_level=os.getenv("LOG_LEVEL", "error").lower(), \
                            server=os.getenv("SERVER", "demo").lower())
        self.connection = con
        logging.info('Connection established with server')
        logging.debug(con)
        return con

    def disconnect(self):
        self.connection.close()
        return True
    

class FindEntry(object):

    def __init__(self):
        pass

    def find_entry(self, entry_strategy, df, **kwargs):
        strategy = entry_strategy(stoploss=kwargs.get("stoploss"), target=kwargs.get("target") \
                    )
        strategy.dataframe = df
        strategy.is_valid_dataframe()
        signal = strategy.get_signal()
        return signal

class FindExit(FindEntry):

    def find_exit(self, exit_strategy, entry_signal, df, **kwargs):
        entry_signal = next(pd.DataFrame(entry_signal).itertuples())
        strategy = exit_strategy(stoploss=kwargs.get("stoploss"), target=kwargs.get("target") \
                    )
        strategy.dataframe = df
        strategy.entry_signal = entry_signal
        strategy.is_valid_dataframe()
        signal = strategy.get_signal()
        return signal


class OrderBook:

    @staticmethod
    def update_order(entry_order, order_type="entry", exit_signal=None):
        _entry_order = next(pd.DataFrame(entry_order).itertuples())
        if order_type.lower() == "entry" and (datetime.datetime.strptime(str(_entry_order.Index), '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes=5)) >= datetime.datetime.today():
            order, is_created = Order.objects.get_or_create(
                order_time=_entry_order.Index
            )
            if is_created:
                logging.info('Order has been created for new entry')
                logging.info('Updating order information')
                order._entry = OrderBook.jsonize_entry(entry_order)
                order.save()
                return True
            return False
        if exit_signal:
            logging.info('exit signal details updaing')
            order = Order.objects.get(order_time=_entry_order.Index)
            if order.has_exit_signal:
                return False
            order.exit_price, order.exit_time, order.pl_status = exit_signal
            order.exit_price = str(order.exit_price)
            order.save()
            return False
            
    @staticmethod
    def jsonize_entry(entry_order):
        output = {}
        for name, tdata in entry_order.items():
            tstamp = list(tdata.keys())[0]
            value = list(tdata.values())[0]
            output[name] = {str(tstamp): value}
        return output

    @staticmethod
    def last_order():
        return Order.objects.order_by("-order_time").first()
        
    @staticmethod
    def is_last_order_open():
        last_order = OrderBook.last_order()
        if last_order:
            return False if last_order.has_exit_signal else True
        return False


class Trader(object):
    __connection = Connection().connect()

    def __init__(self, **kwargs):
        print("Initiating Connection....")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def start_entry_trading(self, entry_strategy,  **kwargs):
        entry_signal = FindEntry().find_entry(entry_strategy, **kwargs)
        order_book = OrderBook()
        order = None
        if entry_signal:
            _entry_signal = next(pd.DataFrame(entry_signal).itertuples())
            last_order = order_book.last_order()
            AMOUNT = kwargs.get("AMOUNT", 5) # this is lot size
            pip_profit = kwargs.get("pip_profit", 0.004)
            LIMIT_PRICE = _entry_signal.entry_price + pip_profit if _entry_signal.entry_signal == "BUY" else _entry_signal.entry_price - pip_profit
            if last_order and order_book.is_last_order_open():
                last_order_df = next(pd.DataFrame(last_order.entry).itertuples())
                if last_order_df.entry_signal == _entry_signal.entry_signal and order_book.update_order(entry_signal):
                    logging.info("Entry signal found placing a new order")
                    order = self.__connection.create_entry_order(
                                symbol='EUR/USD',
                                is_buy=True if _entry_signal.entry_signal == "BUY" else False,
                                amount=AMOUNT,
                                order_type="Entry",
                                rate=_entry_signal.entry_price,
                                limit=LIMIT_PRICE,
                                is_in_pips=False,
                                time_in_force='GTC',
                            )
                elif last_order_df.entry_signal != _entry_signal.entry_signal:
                    if order_book.update_order(entry_signal):
                        logging.info(f"Sending Order for {entry_signal}")
    #                 Comment in below code when exit signal function is ready
                        order = self.__connection.create_entry_order(
                                symbol='EUR/USD',
                                is_buy=True if _entry_signal.entry_signal == "BUY" else False,
                                amount=AMOUNT,
                                order_type="Entry",
                                rate=_entry_signal.entry_price,
                                limit=LIMIT_PRICE,
                                is_in_pips=False,
                                time_in_force='GTC',
                            )
            else:
                if order_book.update_order(entry_signal):
                    logging.info("Entry signal found placing a new order!....")
                    order = self.__connection.create_entry_order(
                                symbol='EUR/USD',
                                is_buy=True if _entry_signal.entry_signal == "BUY" else False,
                                amount=AMOUNT,
                                order_type="Entry",
                                rate=_entry_signal.entry_price,
                                limit=LIMIT_PRICE,
                                is_in_pips=False,
                                time_in_force='GTC',
                            )
            if order:
                if OrderBook.last_order():
                    od = OrderBook.last_order()
                    od.orderId = order.get_orderId()
                    od.save()
                    logging.info("Order placed successfully!")
        else:
            logging.info("no signal found for entry")


    def close_order(self, order_obj, exit_signal:list):
        if not order_obj.has_exit_signal and exit_signal != (0,0,0):
            order = self.__connection.get_order(order_obj.orderId)
            tradeId = order.get_tradeId()
            if tradeId:
                request_data = {
                    "trade_id": tradeId,
                    "amount": order.get_associated_trade().get_amount(),
                    "order_type": "AtMarket",
                    "time_in_force": "FOK",
                    "rate": exit_signal[0],
                    "at_market": 0
                }
                logging.info('order closing data: %s' % request_data)
                res = requests.post('%s:443/%s' % (self.__connection.trading_url, "trading/close_trade") ,headers=self.__connection.request_headers, data=request_data)
            else:
                logging.info("Order not created yet")


    def start_exit_trading(self, exit_strategy, **kwargs):
        order_book = OrderBook()
        last_order = order_book.last_order()
        open_orders = [order for order in Order.objects.filter(order_time__date=datetime.datetime.today().date()) if not order.has_exit_signal]
        
        for order in open_orders:
            exit_signal = FindExit().find_exit(exit_strategy, order.entry, **kwargs)
            _entry_signal = next(pd.DataFrame(order.entry).itertuples())
            if exit_signal != (0,0,0):
                logging.info("Exit signal found placing a exit order")
                self.close_order(order, exit_signal)
                order.exit_price, order.exit_time, order.pl_status = exit_signal
                order.exit_price = str(order.exit_price)
                order.save()
                return order
            else:
                logging.info(f"no exit signal found aginst entry: {order.entry}")


    def start_trading(self):
        while datetime.datetime.today().isoweekday() in list(range(1,6)):
            try:
                today_date = datetime.datetime.today()
                start_time = datetime.time(0,10)
                end_time = datetime.time(20,49)
                start_trading = False
                if today_date.isoweekday() in list(range(1,6)):
                    if today_date.isoweekday() == 1 and today_date.time() > start_time:
                        logging.info("it is a trading day")
                        start_trading = True
                    elif today_date.isoweekday() == 5 and today_date.time() > end_time:
                        start_trading = False
                    else:
                        logging.info("it is a trading day")
                        start_trading = True

                if start_trading:
                    logging.info("permitted for trading")
                    logging.info("sleeping for next 25 seconds")
                    gtime.sleep(25)
                    df = self.__connection.get_candles('EUR/USD', period='m1', number=250)
                    logging.info("candles data fetched successfully!")
                    logging.info("last candle updated of time frame %s" % df.iloc[-1].name)
                    self.start_entry_trading(SMAStrategy3Level1, stoploss=self.stoploss, target=self.target, df=df)
                    self.start_exit_trading(SMAExitLevel1, stoploss=self.stoploss, target=self.target, df=df)
            except Exception as e:
                logging.debug(str(e))
                logging.error(e)
                logging.info(e)
                continue