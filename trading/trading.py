from multiprocessing.sharedctypes import Value
import os, fxcmpy, json, logging, requests, schedule
from fxcmpy.fxcmpy import ServerError
import os, json, logging, requests, schedule
from socketIO_client.exceptions import ConnectionError
from fxcmpy.fxcmpy_open_position import fxcmpy_open_position
import datetime
from django.utils import timezone
# import time as gtime
from trading.strategy import SMAExitLevel1, SMAStrategy3Level1
from trading.models import *
import pandas as pd
import time

# CODE BLOCK

TOKEN = "5b6de8dc3b260ab0fab6e007bf21c43ee4fc7a27"


def get_logger(level):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger = logging.getLogger("Affinity")
    logger.setLevel(level)
    return logger


logger = get_logger("DEBUG")

class Connection:

    def __init__(self):
        self.token = os.getenv("FXCM_TOKEN")
        self.connection = None

    def connect(self):
        con = fxcmpy.fxcmpy(access_token=TOKEN, log_level=os.getenv("LOG_LEVEL", "error").lower(), \
                            server=os.getenv("SERVER", "demo").lower())
        if con.is_connected():
            if not con.is_subscribed('EUR/USD'):
                con.subscribe_market_data('EUR/USD')
                con.set_max_prices(500)
        self.connection = con
        return con

    def disconnect(self):
        try:
            self.connection.unsubscribe_market_data('EUR/USD')
        except:
            pass
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
        if order_type.lower() == "entry" and (datetime.datetime.strptime(str(_entry_order.Index), '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes=5)) > datetime.datetime.today():
            order, is_created = Order.objects.get_or_create(
                order_time=_entry_order.Index
            )
            if is_created:
                print('Order has been created for new entry')
                print('Updating order information')
                order._entry = OrderBook.jsonize_entry(entry_order)
                order.save()
                return True
            return False
        if exit_signal:
            print('exit signal details updating')
            order = Order.objects.get(order_time=_entry_order.Index)
            if order.has_exit_signal:
                return False
            order.exit_price, order.exit_time, order.pl_status = exit_signal
            order.exit_price = str(order.exit_price)
            order.save()
            return False
        print("No Condition found for updating/creating a order")
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
    
    def __init__(self, **kwargs):
        self._candle_data = None
        self.__connection = None
        print("Initiating Connection....")
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.__create_connection__()

    def __create_connection__(self):
        retry = True
        retry_counter = 0
        while retry and retry_counter < 100:
            try:
                print("Connecting.........")
                self.__connection = Connection().connect()
                break
            except Exception as e:
                print("Unable to connect, retrying after 5 seconds")
                print(e)
                print("Sleeping before reconnection.......")
                time.sleep(5)
                retry_counter += 5
            
            if retry_counter > 100:
                raise ServerError("Unable to connect with server try after sometime with manual request")

    def __reconnect_connection__(self):
        self.__create_connection__()
    
    def create_order(self, **kwargs):
        last_row = self.__connection.get_last_price('EUR/USD')
        up_range = kwargs["rate"] + 0.00003
        down_range = kwargs["rate"] - 0.00003
        if kwargs["is_buy"] == True:
            if last_row["Bid"] < kwargs["rate"]: 
                kwargs["order_type"] = "AtMarket"
                return self.__connection.open_trade(**kwargs)
            elif down_range < last_row["Bid"] < up_range:
                kwargs["order_type"] = "AtMarket"
                return self.__connection.open_trade(**kwargs)
            else:
                return self.__connection.create_entry_order(**kwargs)
        if kwargs["is_buy"] == False:
            if last_row["Bid"] > kwargs["rate"]:
                kwargs["order_type"] = "AtMarket"
                return self.__connection.open_trade(**kwargs)
            elif up_range > last_row["Bid"] > down_range:
                kwargs["order_type"] = "AtMarket"
                return self.__connection.open_trade(**kwargs)
            else:
                return self.__connection.create_entry_order(**kwargs)

    def start_entry_trading(self, entry_strategy,  **kwargs):
        entry_signal = FindEntry().find_entry(entry_strategy, **kwargs)
        order = None
        if entry_signal:
            order_book = OrderBook()
            print("Latest Entry Signal Data %s" % (entry_signal))
            _entry_signal = next(pd.DataFrame(entry_signal).itertuples())
            last_order = order_book.last_order()
            AMOUNT = kwargs.get("AMOUNT", 5) # this is lot size
            pip_profit = kwargs.get("pip_profit", 0.004)
            LIMIT_PRICE = _entry_signal.entry_price + pip_profit if _entry_signal.entry_signal == "BUY" else _entry_signal.entry_price - pip_profit
            data = {
                        "symbol":'EUR/USD',
                        "is_buy":True if _entry_signal.entry_signal == "BUY" else False,
                        "amount":AMOUNT,
                        "order_type":"Entry",
                        "rate":_entry_signal.entry_price,
                        "limit":LIMIT_PRICE,
                        "is_in_pips":False,
                        "time_in_force":'GTC',
                    }
            if last_order and order_book.is_last_order_open():
                last_order_df = next(pd.DataFrame(last_order.entry).itertuples())
                if last_order_df.entry_signal == _entry_signal.entry_signal and order_book.update_order(entry_signal):
                    print("Entry signal found placing a new order")
                    print(entry_signal)
                    order = self.create_order(**data)
                elif last_order_df.entry_signal != _entry_signal.entry_signal:
                    if order_book.update_order(entry_signal):
                        print(f"Sending Order for {entry_signal}")
    #                 Comment in below code when exit signal function is ready
                        order = self.create_order(**data)
            else:
                if order_book.update_order(entry_signal):
                    print("Entry signal found placing a new order!....")
                    order = self.create_order(**data)
            if order:
                if OrderBook.last_order():
                    od = OrderBook.last_order()
                    od.orderId = order.get_orderId()
                    od.save()
                    print("Order placed successfully!")
        else:
            print("no signal found for entry")


    def close_order(self, order_obj, exit_signal:list):
        if not order_obj.has_exit_signal and exit_signal != (0,0,0):
            associated_trade = None
            try:
                order = self.__connection.get_order(order_obj.orderId)
                associated_trade = order.get_associated_trade()
            except ValueError as e:
                print("Error raised while searching for order for making exit")
                print(e)
                positions = self.__connection.get_open_positions()
                position = positions[positions.orderId == str(order_obj.orderId)]
                if not position.empty:
                    position = dict(position.iloc[0])
                associated_trade = fxcmpy_open_position(self.__connection, position)
            except Exception as e:
                print(e)
                print("Unexpected error arrvied, stopping this function for further debug")
                
            
            tradeId = order_obj.tradeId
            if associated_trade and tradeId:
                request_data = {
                    "trade_id": tradeId,
                    "amount": associated_trade.get_amount(),
                    "order_type": "AtMarket",
                    "time_in_force": "FOK",
                    "rate": exit_signal[0],
                    "at_market": 0
                }
                print('order closing data: %s' % request_data)
                res = requests.post('%s:443/%s' % (self.__connection.trading_url, "trading/close_trade") ,headers=self.__connection.request_headers, data=request_data)
            else:
                print("Order not created yet")


    def start_exit_trading(self, exit_strategy, **kwargs):
        order_book = OrderBook()
        open_orders = [order for order in Order.objects.filter(pl_status=None).exclude(tradeId=None) if not order.has_exit_signal]
        if open_orders:
            print("Some open orders found for exit trading.....")
            print(open_orders)
        for order in open_orders:
            if order.orderId:
                exit_signal = FindExit().find_exit(exit_strategy, order.entry, **kwargs)
                _entry_signal = next(pd.DataFrame(order.entry).itertuples())
                if exit_signal != (0,0,0):
                    print("Exit signal found placing a exit order")
                    self.close_order(order, exit_signal)
                    order.exit_price, order.exit_time, order.pl_status = exit_signal
                    order.exit_price = str(order.exit_price)
                    order.save()
                    return order
                else:
                    print(f"no exit signal found aginst entry: {order.entry}")


    def start_trading(self):
        if datetime.datetime.today().isoweekday() in list(range(1,6)):
            try:
                today_date = datetime.datetime.today()
                start_time = datetime.time(0,10)
                end_time = datetime.time(20,49)
                start_trading = False
                if today_date.isoweekday() in list(range(1,6)):
                    if today_date.isoweekday() == 1 and today_date.time() > start_time:
                        print("it is a trading day")
                        start_trading = True
                    elif today_date.isoweekday() == 5 and today_date.time() > end_time:
                        start_trading = False
                    else:
                        print("it is a trading day")
                        start_trading = True

                if start_trading:
                    print("permitted for trading")
                    print("fetching data from server")
                    
                    print("DEBUG")
                    print(f"connection is connected {self.__connection.is_connected()}")
                    df = self.__connection.get_candles('EUR/USD', period='m1', number=250)
                    if df.empty:
                        print("Expecting connection has been broken, trying to reconnect")
                        self.__reconnect_connection__()

                    self._candle_data = df
                    print("candles data fetched successfully!")
                    print("last candle: %s" % df.iloc[-1])
                    
                    self.start_entry_trading(SMAStrategy3Level1, stoploss=self.stoploss, target=self.target, df=df)
                    self.start_exit_trading(SMAExitLevel1, stoploss=self.stoploss, target=self.target, df=df)
            except Exception as e:
                print(str(e))
                print(e)
                pass

    def __update_trade_detail__(self, **kwargs):
        for order in Order.objects.filter(pl_status=None, tradeId=None).exclude(orderId=None):
            try:
                fxcm_order = self.__connection.get_order(order.orderId)
            except ValueError as e:
                print(str(e))
            except Exception as e:
                print(str(e))
            else:
                if fxcm_order.get_associated_trade() != None:
                    order.tradeId = fxcm_order.get_tradeId()
                    order.save()

    def __delete_none_orders__(self):
        for order in Order.objects.filter(orderId=None):
            if order.order_time + datetime.timedelta(minutes=10) <= timezone.now():
                order.delete()      
    
    def __remove_not_executed_orders__(self):
        """_summary_
            remove orders which has not been executed from more than 30 minute
        """
        for order in Order.objects.filter(tradeId=None, pl_status=None).exclude(orderId=None):
            fxcm_order = self.__connection.get_order(order.orderId)
            if fxcm_order.get_associated_trade() == None and order.order_time + datetime.timedelta(minutes=15) <= timezone.now():
                print(f"deleting order {order.__dict__}")
                self.__connection.delete_order(order.orderId)
                order.exit_time = order.order_time
                order.exit_price= order.entry_price
                order.pl_status = "CANCELLED"
                order.save()


    def __create_orders_from_trading_dashboard__(self):
        try:
            positions = self.__connection.get_open_positions()
            if not positions.empty:
                for i in range(0, len(positions)):
                    position = positions.iloc[i]
                    open_position = fxcmpy_open_position(self.__connection, position)
                    try:
                        order = Order.objects.get(orderId=position["orderId"])
                    except:
                        order = Order.objects.create(orderId=position["orderId"], tradeId=position["tradeId"],\
                                                    order_time=open_position.get_time())
                    finally:
                        if not order.tradeId:
                            order.tradeId = position["tradeId"]
                        if order._entry == {}:
                            data = self._candle_data
                            candle = data[open_position.get_time() - datetime.timedelta(minutes=1): ].head(1)
                            if not candle.empty:
                                serialize_data = candle.to_dict()
                                order_time = list(serialize_data["bidclose"])[0]
                                serialize_data["entry_price"] = {order_time: open_position.get_open()}
                                serialize_data["entry_signal"] = {order_time: "BUY" if open_position.get_isBuy() else "SELL"}
                                order._entry = OrderBook.jsonize_entry(serialize_data)
                        order.save()
        except KeyError:
            print("Connection broken, trying to reconnect")
            self.__reconnect_connection__()
        except Exception as e:
            print(e)



# Initialize Trader Class
trader = Trader(stoploss=0.0005, target=0.0008)



# Schedule Tasks
schedule.every().minute.at(":03").do(trader.start_trading)
schedule.every(1).minutes.do(trader.__update_trade_detail__)
schedule.every(2).minutes.do(trader.__delete_none_orders__)
schedule.every(2).minutes.do(trader.__create_orders_from_trading_dashboard__)
schedule.every(3).minutes.at(":15").do(trader.__remove_not_executed_orders__)