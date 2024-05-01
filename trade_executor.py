class TradeExecutor:
    '''
    - acts as the interface between TradingStrategy decisions and Binance exchange
    - perfoming trades based on other factors like account balance from BookKeeper
    - observing risk limits from RiskManager class
    '''
    def __init__(self, book_keeper):
        self.book_keeper = book_keeper

    def execute_trade(self, trade):
        # Execute trade based on strategy decision
        pass

    def check_risk_limits(self):
        # Check risk limits before executing trades
        pass