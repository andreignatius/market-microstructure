import websocket
import json
import datetime

class MarketDataStream:
    '''
    - interfaces with market data gateway
    - for now we interact with market data stream via websocket for TradingStrategy to avoid overloading API limit
    '''
    def __init__(self, queue):
        self.queue = queue

    def fetch_data(self):
        """WebSocket communication in the background thread."""
        def on_message(ws, message):
            data = json.loads(message)
            if 'p' in data:
                price = float(data['p'])
                timestamp = datetime.datetime.now()
                self.queue.put((timestamp, price))
        
        def on_open(ws):
            params = {"method": "SUBSCRIBE", "params": ["btcusdt@trade"], "id": 1}
            ws.send(json.dumps(params))
        
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                    on_message=on_message,
                                    on_open=on_open)
        ws.run_forever()
