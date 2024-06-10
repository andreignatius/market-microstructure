import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from enum import Enum
from threading import Thread
from urllib.parse import urlencode

import requests
import websockets
from binance import AsyncClient, Client
from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    level=logging.INFO,
)

# Side of an order or trade
class Side(Enum):
    BUY = 0
    SELL = 1


# Execution type
class ExecutionType(Enum):
    NEW = 0
    CANCELED = 1
    CALCULATED = 2
    EXPIRED = 3
    TRADE = 4


# Order status
class OrderStatus(Enum):
    PENDING_NEW = 0  # sent to exchange but has not received any status
    NEW = 1  # order accepted by exchange but not processed yet by the matching engine
    OPEN = 2  # order accepted by exchange and is active on order book
    CANCELED = 3  # order is cancelled
    PARTIALLY_FILLED = 4  # order is partially filled
    FILLED = 5  # order is fully filled and closed (i.e. not expecting any more fills)
    PENDING_CANCEL = 6  # cancellation sent to exchange but has not received any status
    FAILED = 7  # order failed


class OrderEvent:
    def __init__(
        self,
        contract_name: str,
        order_id: str,
        execution_type: ExecutionType,
        status: OrderStatus,
        canceled_reason=None,
        client_id=None,
    ):
        self.contract_name = contract_name
        self.order_id = order_id
        self.client_id = client_id
        self.execution_type = execution_type
        self.status = status
        self.canceled_reason = canceled_reason

        # the following fields will be populated if matched
        self.side = None
        self.order_type = None
        self.limit_price = None
        self.last_filled_time = None
        self.last_filled_price = 0
        self.last_filled_quantity = 0

    def __str__(self):
        return f"Order events [contract={self.contract_name}, order_id={self.order_id}, status={self.status}, type={self.execution_type}, side={self.side}, last_filled_price={self.last_filled_price}, last_filled_qty={self.last_filled_quantity}, canceled_reason={self.canceled_reason}]"

    def __repr__(self):
        return str(self)


class TradeExecutor:
    """
    - acts as the interface between TradingStrategy decisions and Binance exchange
    - perfoming trades based on other factors like account balance from BookKeeper
    - observing risk limits from RiskManager class
    """

    def __init__(self, manager, api_key, api_secret, name="Binance", testnet=True):
        self.manager = manager
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self._exchange_name = name
        # callbacks
        self._exec_callbacks = []

        # this is a loop and dedicated thread to run all async concurrent tasks
        self._loop = asyncio.new_event_loop()
        self._loop_thread = Thread(target=self._run_async_tasks, daemon=True, name=name)

    def signature(self, data: dict, secret: str) -> str:
        """
        signature is required to authenticate the request
        """
        postdata = urlencode(data)
        message = postdata.encode()
        byte_key = bytes(secret, "UTF-8")
        mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
        return mac

    def execute_trade(self, trade: dict, direction: str):
        """
        Executes a trade if it complies with risk management policies.
        """
        api_url = "https://testnet.binancefuture.com"
        uri_path = "/fapi/v1/order"  #### for testing add '/test'
        headers = {}
        headers["X-MBX-APIKEY"] = self.api_key
        signature = self.signature(trade, self.api_secret)

        if direction == "trade":
            """
            trade = {
                "symbol": symbol,
                "side": side,
                "type": type,
                "price": 69000, REQUIRED FOR LIMIT ORDERS
                "timeinforce": 'GTC', REQUIRED FOR LIMIT ORDERS
                "quantity": quantity,
                "timestamp": int(time.time() * 1000),
                "recvWindow": 60000
            }
            """
            payload = {
                **trade,
                "signature": signature,
            }
            req = requests.post(
                (api_url + uri_path), headers=headers, data=payload, timeout=1
            )  # post trade
            result = req.json()  # response
            (
                self.log_trade_execution(result, "submitted")
                if "code" not in result.keys()
                else self.log_trade_execution(result["msg"], "failed")
            )
            return True

        elif direction == "cancel":
            """
            trade = {
            "orderId": orderId,
            "symbol": symbol,
            "timestamp": int(time.time() * 1000),
            "recvWindow": 60000
            }
            """
            params = {
                **trade,
                "signature": signature,
            }
            req = requests.delete((api_url + uri_path), params=params, headers=headers)
            result = req.json()  # response
            (
                self.log_trade_execution(result, "submitted")
                if "code" not in result.keys()
                else self.log_trade_execution(result["msg"], "failed")
            )
            return True

    def log_trade_execution(self, result, status):
        """
        Log details of the executed trade for auditing and monitoring purposes.
        """
        if status == "submitted":
            order_id = result.get("orderId")
            symbol = result.get("symbol")
            status = result.get("status")
            side = result.get("side")
            type = result.get("type")

            order_event = OrderEvent(
                symbol, order_id, ExecutionType[status], OrderStatus[status]
            )
            order_event.side = Side[side]
            if type == "MARKET":
                order_event.last_filled_quantity = result.get("origQty")
                logging.info(order_event)
                return True

            elif type == "LIMIT":
                price = result.get("price")
                order_event.limit_price = price
                logging.info(order_event)
                return True

        elif status == "failed":
            logging.info(result)
            return True

        elif status == "filled":
            logging.info(result)
            return True

    ############## self.manager.give_trade(result) # give trade back to manager

    def connect(self):
        """
        Connect method to start exchange connection
        """
        logging.info("Initializing connection")

        self._loop.run_until_complete(self._reconnect_ws())

        logging.info("starting event loop thread")
        self._loop_thread.start()

        # synchronous client
        self._client = Client(self.api_key, self.api_secret, testnet=self.testnet)

    # an internal method to reconnect websocket
    async def _reconnect_ws(self):
        logging.info("reconnecting websocket")
        self._async_client = await AsyncClient.create(
            self.api_key, self.api_secret, testnet=self.testnet
        )

    def _run_async_tasks(self):
        """Run the following tasks concurrently in the current thread"""
        self._loop.create_task(self._listen_execution_forever())
        self._loop.run_forever()

    async def _listen_execution_forever(self):
        """
        An internal async method to listen to user data stream
        """
        logging.info("Subscribing to user data events")
        _listen_key = await self._async_client.futures_stream_get_listen_key()
        if self.testnet:
            url = "wss://stream.binancefuture.com/ws/" + _listen_key
        else:
            url = "wss://fstream.binance.com/ws/" + _listen_key

        conn = websockets.connect(url)
        ws = await conn.__aenter__()
        while ws.open:
            message = await ws.recv()
            # logging.info(_message)

            # convert to json
            data = json.loads(message)
            update_type = data.get("e")

            if update_type == "ORDER_TRADE_UPDATE":
                trade_data = data.get("o")
                order_id = trade_data.get("i")
                symbol = trade_data.get("s")
                execution_type = trade_data.get("x")
                order_status = trade_data.get("X")
                side = trade_data.get("S")
                last_filled_price = float(trade_data.get("L"))
                last_filled_qty = float(trade_data.get("l"))

                # create an order event
                order_event = OrderEvent(
                    symbol,
                    order_id,
                    ExecutionType[execution_type],
                    OrderStatus[order_status],
                )
                order_event.side = Side[side]
                if execution_type == "TRADE":
                    order_event.last_filled_price = last_filled_price
                    order_event.last_filled_quantity = last_filled_qty
                    self.log_trade_execution(order_event, "filled")

                # should have a callback just in case
                if self._exec_callbacks:
                    # notify callbacks
                    for _callback in self._exec_callbacks:
                        print(
                            "****************** EXECUTING CALLBACK ******************"
                        )
                        _callback()

    def register_exec_callback(self, callback):
        print("################ REGISTERING CALLBACK ################")
        self._exec_callbacks.append(callback)


load_dotenv(dotenv_path="../.env")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

load_dotenv(dotenv_path="../.env")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if __name__ == "__main__":
    api_key = API_KEY
    api_secret = API_SECRET

    TradeExecutor("", api_key, api_secret).connect()
    time.sleep(5)
    # data = {
    # "symbol": 'BTCUSDT',
    # "side": 'BUY',
    # "type": 'LIMIT',
    # "price": 60000,
    # "timeinforce": 'GTC',
    # "quantity": 0.002,
    # "timestamp": int(time.time() * 1000),
    # "recvWindow": 60000
    # }
    data = {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "type": "MARKET",
        "quantity": 0.002,
        "timestamp": int(time.time() * 1000),
        "recvWindow": 60000,
    }
    cancel_data = {
        "orderId": 4036972677,
        "symbol": "BTCUSDT",
        "timestamp": int(time.time() * 1000),
        "recvWindow": 60000,
    }
    trader = TradeExecutor("", api_key, api_secret)
    while True:
        time.sleep(1)
        trader.execute_trade(data, "trade")
    # TradeExecutor('',api,secret).execute_trade(cancel_data, 'cancel')
