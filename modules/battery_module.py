import pandas as pd
import numpy as np
from typing import Dict
from modules.tax_module import NetworkTaxCalculator

class Battery:
    def __init__(self, capacity=100.0, initial_charge=0.0, c_rate=1.0):
        """
        Initialize a battery with capacity, initial charge, and c-rate.
        
        Args:
            capacity: Maximum energy storage in kWh
            initial_charge: Initial energy stored in kWh
            c_rate: The rate at which the battery can charge/discharge relative to its capacity
                    (e.g., 1.0 means full capacity in 1 hour, 0.5 means full capacity in 2 hours)
        """
        self.capacity = capacity
        self._charge = min(max(initial_charge, 0.0), capacity)
        self.c_rate = c_rate
        # Initialize history tracking with timestamp and charge level
        self.history = []
        
    def record_state(self, timestamp):
        """Record the current state of the battery at the given timestamp."""
        self.history.append({
            'timestamp': timestamp,
            'charge': self._charge,
            'percent': self.percent
        })
        
    @property
    def charge(self):
        return self._charge
    
    @property
    def percent(self):
        return (self._charge / self.capacity) * 100
    
    @property
    def max_charge_rate_per_interval(self):
        """Maximum amount that can be charged in a 15-minute interval based on c-rate."""
        # c_rate is capacity per hour, so for 15 minutes (0.25 hours)
        return self.capacity * self.c_rate * 0.25
    
    def charge_battery(self, amount, timestamp=None):
        if amount < 0:
            return self.discharge(abs(amount), timestamp)
        
        # Calculate the c-rate limitation for this 15-minute interval
        max_charge_rate = self.max_charge_rate_per_interval
        
        # Determine limiting factor: c-rate or available capacity
        available_capacity = self.capacity - self._charge
        c_rate_limited = amount > max_charge_rate
        capacity_limited = amount > available_capacity
        
        # Determine actual amount to charge
        actual_amount = min(amount, available_capacity, max_charge_rate)
        self._charge += actual_amount
        
        # Record the state if timestamp is provided
        if timestamp is not None:
            self.record_state(timestamp)
        
        # Calculate amount that couldn't be charged
        excess_amount = amount - actual_amount
        
        return {
            'amount_charged': actual_amount,
            'excess_amount': excess_amount,
            'error': capacity_limited or c_rate_limited,
            'reason': 'Battery full' if capacity_limited else ('C-rate limited' if c_rate_limited else None)
        }
    
    def discharge(self, amount, timestamp=None):
        if amount < 0:
            return self.charge_battery(abs(amount), timestamp)
        
        # Calculate the c-rate limitation for this 15-minute interval
        max_discharge_rate = self.max_charge_rate_per_interval
        
        # Determine limiting factor: c-rate or available charge
        c_rate_limited = amount > max_discharge_rate
        charge_limited = amount > self._charge
        
        # Determine actual amount to discharge
        actual_amount = min(amount, self._charge, max_discharge_rate)
        self._charge -= actual_amount
        
        # Record the state if timestamp is provided
        if timestamp is not None:
            self.record_state(timestamp)
        
        # Calculate amount that couldn't be discharged
        unmet_amount = amount - actual_amount
        
        return {
            'amount_discharged': actual_amount,
            'unmet_amount': unmet_amount,
            'error': charge_limited or c_rate_limited,
            'reason': 'Battery empty' if charge_limited else ('C-rate limited' if c_rate_limited else None)
        }
        
    def get_history_dataframe(self):
        """Convert the history to a pandas DataFrame for easier plotting."""
        if not self.history:
            return pd.DataFrame(columns=['timestamp', 'charge', 'percent'])
        return pd.DataFrame(self.history)

class BatterySavingsCalculator:
    """
    Calculator for potential savings using a battery storage system.
    
    This class simulates battery behavior to maximize cost savings by:
    1. Storing excess solar energy instead of feeding it back to the grid
    2. Discharging stored energy during high-price periods
    3. Optimizing battery usage based on energy price arbitrage
    
    The calculator considers battery constraints like capacity, charge/discharge
    efficiency, minimum state of charge, and maximum charge/discharge rates.
    """
    
    def __init__(self, 
                 battery_capacity: float = 100.0, 
                 enable_solar_arbitrage: bool = True, 
                 charge_efficiency: float = 1.0, 
                 discharge_efficiency: float = 1.0, 
                 min_state_of_charge: float = 0.0,
                 max_cycle_fraction: float = 0.5,
                 maximum_charge_rate_kw: float = None):
        """
        Initialize the battery savings calculator with battery specifications.
        
        Args:
            battery_capacity: Battery capacity in kWh
        """
        self.battery_capacity = battery_capacity
        self.battery = Battery(battery_capacity)
        self.tax_calculator = NetworkTaxCalculator()

    def group_by_days(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Groups a dataframe with 15-minute interval timestamps into daily chunks.
        Each day starts at 00:15:00 and ends at 00:00:00 of the next day.
        
        Args:
            df: DataFrame with 'timestamp' column containing datetime values
            
        Returns:
            Dictionary with date strings as keys and dataframes of that day's intervals as values
        """
        # Create a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Create a day_key column that assigns 00:00:00 to the previous day
        df_copy['time'] = df_copy['timestamp'].dt.time
        df_copy['day_key'] = df_copy['timestamp'].dt.date
        
        # Adjust the day_key for 00:00:00 entries (they belong to the previous day)
        midnight_mask = df_copy['time'] == pd.Timestamp('00:00:00').time()
        df_copy.loc[midnight_mask, 'day_key'] = df_copy.loc[midnight_mask, 'timestamp'].dt.date - pd.Timedelta(days=1)
        
        # Group by the adjusted day_key
        result = {}
        for day, day_data in df_copy.groupby('day_key'):
            # Sort by timestamp to ensure chronological order
            day_data = day_data.sort_values('timestamp')
            # Convert day to string format for dictionary keys
            day_str = day.strftime('%Y-%m-%d')
            result[day_str] = day_data
        
        return result


    def arbitrage(self, energy_usage: pd.DataFrame, energy_prices: pd.DataFrame) -> Dict[str, pd.DataFrame]:

        # it could be some intervals have no data, due to several reasons, we cannot do anything about it.
        df = pd.merge(energy_usage, energy_prices, on='timestamp')
        # check if there is missing price data, to display it in the app.
        missing_price_intervals = df[df['price'].isna()]['timestamp'].tolist()
        # Group the data by day
        daily_data = self.group_by_days(df)

        transaction_history_charge = []
        transaction_history_discharge = []

        for _, day_df in daily_data.items():
            # first pass, charge the battery with excess solar
            for _, row in day_df[day_df['type'] == 'return'].iterrows():
                if row['value'] > 0 and self.battery.percent < 100:
                    result =self.battery.charge_battery(row['value'])
                    transaction_history_charge.append({
                        'timestamp': row['timestamp'],
                        'type': 'charge',
                        'amount': result['amount_charged'],
                        'price': row['price'],
                        'cost': result['amount_charged'] * row['price']
                    })
            
            # second pass, discharge the battery during high-price periods
            sorted_day_df = day_df[day_df['type'] == 'supply'].sort_values('price', ascending=False)
            for _, row in sorted_day_df.iterrows():
                if row['value'] > 0 and self.battery.percent > 0:
                    result = self.battery.discharge(row['value'])
                    transaction_history_discharge.append({
                        'timestamp': row['timestamp'],
                        'type': 'discharge',
                        'amount': result['amount_discharged'],
                        'price': row['price'],
                        'saved': (result['amount_discharged'] * row['price']) + (result['amount_discharged'] * self.tax_calculator.get_tax_per_kwh(row['timestamp']))
                    })
        return {
            'missing_intervals': True if len(missing_price_intervals) > 0 else False,
            'transaction_history_charge': pd.DataFrame(transaction_history_charge),
            'transaction_history_discharge': pd.DataFrame(transaction_history_discharge),
            'battery_history': self.battery.get_history_dataframe()
        }

