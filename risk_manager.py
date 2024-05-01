class RiskManager:
    '''
    - monitors PnL / MTM and the greeks and updates VaR / ES values
    - interacts w Strategy engine to trigger stop losses where applicable
    '''
    def __init__(self, book_keeper):
        self.book_keeper = book_keeper

    def monitor_pnl(self):
        # Monitor profit and loss
        pass

    def update_greeks(self):
        # Update greeks values
        pass

    def update_var_es(self):
        # Update Value at Risk (VaR) and Expected Shortfall (ES) values
        pass

    def trigger_stop_loss(self):
        # Trigger stop losses based on risk management rules
        pass