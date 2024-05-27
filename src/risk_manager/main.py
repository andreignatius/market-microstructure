import sys
import os
from datetime import datetime as dt

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from book_keeper.main import BookKeeper


class RiskManager:
    """
    - monitors PnL / MTM and the greeks and updates VaR / ES values
    - interacts w Strategy engine to trigger stop losses where applicable
    """

    def __init__(self, book_keeper, trial):
        self.book_keeper = book_keeper
        self.risk_metrics = {}
        self.greeks = {}  # Options trading might require tracking of Greeks
        self.trial = False  # if trial is set to true, means it is running Test Mode, false it is Actual mode
        self.signal_to_process = None  # refers to nothing

    def get_signal(self, signal):
        # if trial = true then work with trial setup, if not true means it is live.
        if self.trial:
            print("***** RUNNING TRIAL MODE *****")
            self.signal_to_process = signal
        else:
            pass

    def update_risk_metrics(self):
        """
        Update and calculate risk metrics based on current market data and portfolio positions.
        """
        # TODO: Implement the calculations for updating risk metrics like VaR, CVaR, etc.
        pass

    def evaluate_trade_risk(self):
        """
        Evaluate the risk of a proposed trade to ensure it does not exceed predefined limits.
        """
        # TODO: Implement logic to evaluate trade risk based on current risk metrics
        if self.trial:
            if not (self.signal_to_process == None):
                print("***** EVALUATING RISK ON TRIAL SIGNAL *****")

                # 1. check action buy or sell
                if self.signal_to_process["buy"]:
                    print("check inventory, maybe self.book_keeper.")
                elif self.signal_to_process["sell"]:
                    print("short allowed? If not the block if no inventory")
                else:
                    print("do nothing")
                # 2. check amount
            else:
                print("There is no signal to work with !")
        else:
            return True

    def perform_stress_test(self):
        """
        Conduct stress tests and scenario analyses to assess potential impact of extreme market events.
        """
        # TODO: Implement stress testing logic
        pass

    def monitor_positions(self):
        """
        Continuously monitor open positions to ensure they remain within risk limits.
        """
        # TODO: Implement position monitoring logic
        pass

    def handle_breach(self, breach_details):
        """
        Handle breaches of risk limits, including logging the breach and taking corrective actions.
        """
        # TODO: Implement breach handling procedures
        pass

    def generate_risk_reports(self):
        """
        Generate detailed risk reports for internal review or regulatory compliance.
        """
        # TODO: Implement risk reporting logic
        pass

    def adjust_risk_limits(self):
        """
        Dynamically adjust risk limits based on latest market conditions and portfolio performance.
        """
        # TODO: Implement dynamic risk limit adjustments
        pass

    def monitor_pnl(self):
        """
        Continuously monitor profit and loss of the trading portfolio to identify trends and outliers.
        """
        # TODO: Implement the logic to calculate and monitor P&L
        pass

    def update_greeks(self):
        """
        Update the Greeks for options trading, crucial for managing derivatives positions.
        """
        # TODO: Implement logic to calculate and update Greeks like Delta, Gamma, Theta, Vega, Rho
        pass

    def update_var_es(self):
        """
        Update the Value at Risk (VaR) and Expected Shortfall (ES) calculations periodically.
        """
        # TODO: Implement the updates for VaR and ES based on latest data and statistical methods
        pass

    def trigger_stop_loss(self):
        """
        Automatically trigger stop losses for positions that exceed predefined loss thresholds.
        """
        # TODO: Implement the logic to execute stop-loss orders based on risk parameters
        pass


if __name__ == "__main__":
    print("trial the risk manager module independently")
    # Trading will send the following signal, for now i will assume how the signal is sent
    #
    # 1. buy/sell
    # 2. price
    # 3. timestamp
    #
    # i only rmb these

    # create the class
    btcusd_book = BookKeeper("BTCUSD")
    myriskmanager = RiskManager(book_keeper=btcusd_book, trial=True)

    myriskmanager.evaluate_trade_risk

    # 1. TRIAL EXAMPLE 1
    from_trading = {
        "action": "buy",
        "price": 68000,
        "timestamp": dt(2024, 5, 26, 20, 30, 10),
    }

    myriskmanager.get_signal(signal=from_trading)
    myriskmanager.evaluate_trade_risk()
