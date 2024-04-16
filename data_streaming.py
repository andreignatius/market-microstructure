import websocket
import json

def on_message(ws, message):
    print("Received Message:")
    data = json.loads(message)
    print(data)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    # Subscribe to the BTCUSDT trade stream
    params = {
        "method": "SUBSCRIBE",
        "params": [
            "btcusdt@trade"
        ],
        "id": 1
    }
    ws.send(json.dumps(params))

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
