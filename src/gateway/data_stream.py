import asyncio
import logging
from threading import Thread

from binance import AsyncClient, BinanceSocketManager, Client

logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    level=logging.INFO,
)


class DataStream:
    def __init__(self, symbol: str, api_key=None, api_secret=None):
        self._api_key = api_key
        self._api_secret = api_secret
        self._symbol = symbol

        # binance async client
        self._client = None
        self._async_client = None
        self._binance_socket_manager = None  # BinanceSocketManager
        self._multi_socket = None  # binance multi socket session

        # market cache
        self._market_cache = None

        # this is a loop and dedicated thread to run all async concurrent tasks
        self._loop = asyncio.new_event_loop()
        self._loop_thread = Thread(target=self._run_async_tasks, daemon=True)

        # callbacks
        self._tick_callbacks = []

        self.output = {
            "lastprice": "",
            "lastquantity": "",
            "bestbidprice": "",
            "bestbidquantity": "",
            "bestaskprice": "",
            "bestaskquantity": "",
        }

    """
        Connect method to start exchange connection
    """

    def connect(self):
        logging.info("Initializing connection")

        self._loop.run_until_complete(self._reconnect_ws())

        logging.info("starting event loop thread")
        self._loop_thread.start()

        # synchronous client
        self._client = Client(self._api_key, self._api_secret)

    # an internal method to reconnect websocket
    async def _reconnect_ws(self):
        logging.info("reconnecting websocket")
        self._async_client = await AsyncClient.create(self._api_key, self._api_secret)

    # an internal method to runs tasks in parallel
    def _run_async_tasks(self):
        """Run the following tasks concurrently in the current thread"""
        self._loop.create_task(self._listen_market_forever())
        self._loop.run_forever()

    # an internal async method to listen to depth stream
    async def _listen_market_forever(self):
        logging.info("Subscribing to depth events")

        while True:
            if not self._multi_socket:
                logging.info("depth socket not connected, reconnecting")
                self._binance_socket_manager = BinanceSocketManager(self._async_client)
                self._multi_socket = (
                    self._binance_socket_manager.multiplex_socket(
                        [self._symbol.lower()+"@trade", self._symbol.lower() + "@bookTicker"]
                    )
                )

            # wait for depth update
            try:

                async with self._multi_socket as ms:
                    self._market_cache = await ms.recv()

                    if "@trade" in self._market_cache["stream"]:
                        self.output["lastprice"] = self._market_cache["data"]["p"]
                        self.output["lastquantity"] = self._market_cache["data"]["q"]
                    else:
                        self.output["bestbidprice"] = self._market_cache["data"]["b"]
                        self.output["bestbidquantity"] = self._market_cache["data"]["B"]

                        self.output["bestaskprice"] = self._market_cache["data"]["a"]
                        self.output["bestaskquantity"] = self._market_cache["data"]["A"]

                    print(self.output)
                    if self._tick_callbacks:
                        # notify callbacks
                        for _callback in self._tick_callbacks:
                            _callback(self.output)

            except Exception as e:
                logging.exception("encountered issue in depth processing")
                # reset socket and reconnect
                self._multi_socket = None
                await self._reconnect_ws()

    def register_tick_callback(self, callback):
        self._tick_callbacks.append(callback)


# callback on order book update
def on_tick(s):
    return s


if __name__ == "__main__":
    # get api key and secret
    api_key = ""
    api_secret = ""

    # create a binance gateway object
    stream = DataStream("BTCUSDT", api_key, api_secret)

    # register callbacks
    stream.register_tick_callback(on_tick)

    # start connection
    stream.connect()

    while True:
        pass
