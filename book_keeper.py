class BookKeeper:
    ''' 
    - stores all open trades and executed trades as well as technical indicator values 
      surrounding trade at the time of execution
    - will interact with ML modeling in ReviewEngine class for review to assess effectiveness
      and for parameter tuning where applicable
    - will interact with UI LivePlotter for user to monitor MTM / PnL on demand
    '''
    def __init__(self):
        self.open_trades = []
        self.executed_trades = []
        self.indicator_values = {}  # Store technical indicator values

    def store_trade(self, trade):
        # Store trade information
        pass

    def update_indicator_values(self, indicators):
        # Update technical indicator values
        pass

    def calculate_pnl(self):
        # Calculate profit and loss
        pass