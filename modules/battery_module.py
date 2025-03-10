import pandas as pd
import numpy as np
from typing import Dict

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
            enable_solar_arbitrage: Whether to enable solar arbitrage optimization
            charge_efficiency: Energy retained during charging (1.0 = 100%)
            discharge_efficiency: Energy available during discharge (1.0 = 100%)
            min_state_of_charge: Minimum battery level as percentage (0.0-1.0)
            max_cycle_fraction: Max fraction of battery capacity per interval (C-rate)
            maximum_charge_rate_kw: Max charge rate in kW (calculated from capacity if None)
        """
        self.battery_capacity = battery_capacity
        self.enable_solar_arbitrage = enable_solar_arbitrage
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency  
        self.min_state_of_charge = min_state_of_charge
        self.max_cycle_fraction = max_cycle_fraction
        
        # Calculate maximum charge rate based on battery capacity and C-rate if not provided
        if maximum_charge_rate_kw is None:
            self.maximum_charge_rate_kw = self.battery_capacity * self.max_cycle_fraction
        else:
            self.maximum_charge_rate_kw = maximum_charge_rate_kw
        
        # Combined efficiency for full charge-discharge cycle
        self.combined_efficiency = self.charge_efficiency * self.discharge_efficiency

    def arbitrage(self, energy_usage: pd.DataFrame, energy_prices: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Calculate potential savings through battery storage optimization.
        
        This method simulates battery operation day by day to maximize savings by:
        1. Storing excess solar generation instead of feeding it back to the grid
        2. Discharging stored energy during high-price periods
        3. Tracking detailed energy flows for analysis
        
        Args:
            energy_usage: DataFrame with columns [timestamp, type, value]
                where type is either 'return' (solar generation) or 'supply' (consumption)
            energy_prices: DataFrame with columns [timestamp, price]
                
        Returns:
            Dictionary with two keys:
                'savings': DataFrame with daily savings metrics
                'energy_flows': DataFrame with detailed energy flows by timestamp
        """
        # Initialize empty result DataFrames
        total_savings = pd.DataFrame({
            'timestamp': pd.Series(dtype='datetime64[ns]'),
            'gross_savings': pd.Series(dtype='float64'),
            'lost_revenue': pd.Series(dtype='float64'),
            'net_savings': pd.Series(dtype='float64'),
        })
        
        # Early return if solar arbitrage is disabled
        if not self.enable_solar_arbitrage:
            return {'savings': None, 'energy_flows': None}

        # Prepare input data
        energy_usage = energy_usage.copy()
        energy_prices = energy_prices.copy()
        energy_usage.to_csv("energy.csv")
        energy_prices.to_csv("pri")
        
        # Convert timestamps to datetime and add date column
        energy_usage['timestamp'] = pd.to_datetime(energy_usage['timestamp'])
        energy_prices['timestamp'] = pd.to_datetime(energy_prices['timestamp'])
        energy_usage['date'] = energy_usage['timestamp'].dt.date
        energy_prices['date'] = energy_prices['timestamp'].dt.date

        # Create a combined DataFrame with generation, consumption and prices
        energy_pivot = pd.pivot_table(
            energy_usage, 
            values='value',
            index=['timestamp', 'date'],
            columns='type',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Ensure required columns exist
        if 'return' not in energy_pivot.columns:
            energy_pivot['return'] = 0
        if 'supply' not in energy_pivot.columns:
            energy_pivot['supply'] = 0
            
        # Add energy prices
        energy_pivot = pd.merge(
            energy_pivot,
            energy_prices[['timestamp', 'price']],
            on='timestamp',
            how='left'
        ).sort_values('timestamp')
        
        # Define fixed 15-minute interval (0.25 hours)
        interval_fraction = 0.25
        max_power_per_interval = self.maximum_charge_rate_kw * interval_fraction
        
        # Initialize battery state
        min_battery_level = self.battery_capacity * self.min_state_of_charge
        max_battery_level = self.battery_capacity
        current_battery_level = min_battery_level
        
        # Track energy sources in battery (for tax calculations)
        solar_energy_in_battery = current_battery_level
        grid_energy_in_battery = 0.0
        
        # Initialize metrics and energy flows tracking
        daily_metrics = {}
        energy_flows = []
        
        # Process each day in chronological order
        all_dates = sorted(energy_pivot['date'].unique())
        for i in range(len(all_dates)):
            current_date = all_dates[i]
            current_day_data = energy_pivot[energy_pivot['date'] == current_date]
            
            # Initialize daily metrics
            if current_date not in daily_metrics:
                daily_metrics[current_date] = {
                    'gross_savings': 0,
                    'lost_revenue': 0,
                    'net_savings': 0,
                    'stored_solar_value': 0,
                    'solar_energy_used': 0
                }
            
            # Get next day's data for planning if available
            next_day_data = None
            if i + 1 < len(all_dates):
                next_date = all_dates[i + 1]
                next_day_data = energy_pivot[energy_pivot['date'] == next_date]
                
                # Initialize next day's metrics
                if next_date not in daily_metrics:
                    daily_metrics[next_date] = {
                        'gross_savings': 0,
                        'lost_revenue': 0,
                        'net_savings': 0,
                        'stored_solar_value': 0,
                        'solar_energy_used': 0
                    }
            
            # Plan battery operations for the day
            solar_plan = self._plan_solar_arbitrage(
                current_day_data, 
                max_power_per_interval,
                current_battery_level - min_battery_level,  # Available energy
                next_day_data
            )
            
            # Process each timestamp in chronological order
            for _, row in current_day_data.iterrows():
                timestamp = row['timestamp']
                current_price = row['price']
                solar_return = row['return']
                house_consumption = row['supply']
                net_energy = solar_return - house_consumption
                
                # Initialize energy flows for this timestamp
                solar_to_house = min(solar_return, house_consumption)
                solar_to_grid = 0
                solar_to_battery = 0
                grid_to_house = max(0, house_consumption - solar_return)
                grid_to_battery = 0
                battery_to_house = 0
                actions = []
                
                # Execute plan for this timestamp if it exists
                if timestamp in solar_plan:
                    action = solar_plan[timestamp]
                    
                    if action['type'] == 'charge' and net_energy > 0:
                        # Store excess solar in battery
                        available_solar = net_energy
                        space_in_battery = max_battery_level - current_battery_level
                        
                        # Calculate and apply charge
                        charge_amount = min(available_solar, max_power_per_interval, space_in_battery)
                        if charge_amount > 0:
                            solar_to_battery = charge_amount
                            current_battery_level += charge_amount * self.charge_efficiency
                            solar_energy_in_battery += charge_amount * self.charge_efficiency
                            
                            # Track stored solar value
                            daily_metrics[current_date]['stored_solar_value'] += charge_amount * current_price
                            actions.append('solar_to_battery')
                        
                        # Remaining solar goes to grid
                        solar_to_grid = available_solar - solar_to_battery
                        
                    elif action['type'] == 'discharge' and net_energy < 0:
                        # Use battery to meet house demand during high-price periods
                        energy_needed = abs(net_energy)
                        available_battery = (current_battery_level - min_battery_level) * self.discharge_efficiency
                        
                        # Calculate and apply discharge
                        discharge_amount = min(energy_needed, max_power_per_interval, available_battery)
                        if discharge_amount > 0:
                            battery_to_house = discharge_amount
                            
                            # Calculate proportion from solar vs grid
                            solar_percentage = solar_energy_in_battery / current_battery_level if current_battery_level > 0 else 0
                            
                            # Update battery level and composition
                            actual_discharge = discharge_amount / self.discharge_efficiency
                            current_battery_level -= actual_discharge
                            
                            # Reduce solar and grid energy proportionally
                            solar_from_battery = actual_discharge * solar_percentage
                            grid_from_battery = actual_discharge - solar_from_battery
                            
                            solar_energy_in_battery = max(0, solar_energy_in_battery - solar_from_battery)
                            grid_energy_in_battery = max(0, grid_energy_in_battery - grid_from_battery)
                            
                            # Calculate savings from using battery instead of grid
                            date_for_metrics = pd.to_datetime(timestamp).date()
                            daily_metrics[date_for_metrics]['gross_savings'] += battery_to_house * current_price
                            
                            # Track solar energy used from battery
                            if solar_percentage > 0:
                                solar_energy_used = battery_to_house * solar_percentage
                                daily_metrics[date_for_metrics]['solar_energy_used'] += solar_energy_used
                            
                            actions.append('battery_to_house')
                
                # If no plan for this timestamp, excess solar goes to grid
                elif net_energy > 0:
                    solar_to_grid = net_energy
                
                # Record energy flows for this timestamp
                energy_flows.append({
                    'timestamp': timestamp,
                    'solar_to_house': solar_to_house,
                    'solar_to_grid': solar_to_grid,
                    'solar_to_battery': solar_to_battery,
                    'grid_to_house': grid_to_house,
                    'grid_to_battery': grid_to_battery,
                    'battery_to_house': battery_to_house,
                    'battery_level': current_battery_level,
                    'price': current_price,
                    'actions': ','.join(actions) if actions else 'none'
                })
        
        # Calculate final metrics and build result DataFrames
        for date, metrics in daily_metrics.items():
            # Calculate lost revenue (stored solar that wasn't used)
            stored_value = metrics.get('stored_solar_value', 0)
            avg_price = energy_pivot[energy_pivot['date'] == date]['price'].mean()
            used_value = metrics.get('solar_energy_used', 0) * avg_price
            metrics['lost_revenue'] = max(0, stored_value - used_value)
            
            # Calculate net savings
            metrics['net_savings'] = metrics['gross_savings'] - metrics['lost_revenue'] 
            
            # Add to total savings DataFrame
            total_savings = pd.concat([
                total_savings,
                pd.DataFrame({
                    'timestamp': [pd.to_datetime(date)],
                    'gross_savings': [metrics['gross_savings']],
                    'lost_revenue': [metrics['lost_revenue']],
                    'net_savings': [metrics['net_savings']],
                })
            ], ignore_index=True)
        
        # Create energy flows DataFrame
        energy_flows_df = pd.DataFrame(energy_flows)

        total_savings.to_csv("savings.csv")
        
        return {
            'savings': total_savings,
            'energy_flows': energy_flows_df
        }

    def _plan_solar_arbitrage(self, day_data, max_power_per_interval, initial_energy_available=0, next_day_data=None):
        """
        Plan optimal solar arbitrage strategy for the day.
        
        Creates a charging/discharging plan to maximize savings by:
        1. Storing excess solar energy during generation periods
        2. Discharging stored energy during high-price periods
        
        Args:
            day_data: DataFrame with timestamp, price, return (solar generation), and supply (consumption)
            max_power_per_interval: Maximum power that can be charged/discharged per interval
            initial_energy_available: Energy already available in battery at start of day (kWh)
            next_day_data: Optional data for next day (for overnight planning)
            
        Returns:
            Dictionary mapping timestamps to charge/discharge actions
        """
        solar_plan = {}
        
        # First pass: identify all excess solar periods for charging
        charging_periods = []
        for idx, row in day_data.iterrows():
            timestamp = row['timestamp']
            solar_return = row['return']
            house_consumption = row['supply']
            net_energy = solar_return - house_consumption
            
            if net_energy > 0:
                # Store excess solar production
                charge_amount = min(net_energy, max_power_per_interval)
                charging_periods.append({
                    'timestamp': timestamp,
                    'amount': charge_amount,
                    'price': row['price'],
                    'index': idx
                })
        
        # Second pass: identify all energy deficit periods for potential discharge
        discharge_candidates = []
        for idx, row in day_data.iterrows():
            timestamp = row['timestamp']
            solar_return = row['return']
            house_consumption = row['supply']
            net_energy = solar_return - house_consumption
            
            if net_energy < 0:
                discharge_candidates.append({
                    'timestamp': timestamp,
                    'deficit': abs(net_energy),
                    'price': row['price'],
                    'index': idx
                })
        
        # Add next morning periods to discharge candidates if available
        if next_day_data is not None:
            morning_cutoff = pd.Timestamp(next_day_data['date'].iloc[0]).replace(hour=10)
            next_day_morning = next_day_data[next_day_data['timestamp'] < morning_cutoff]
            
            for idx, row in next_day_morning.iterrows():
                timestamp = row['timestamp']
                solar_return = row['return']
                house_consumption = row['supply']
                net_energy = solar_return - house_consumption
                
                if net_energy < 0:
                    discharge_candidates.append({
                        'timestamp': timestamp,
                        'deficit': abs(net_energy),
                        'price': row['price'],
                        'index': idx + 1000  # Offset to ensure these come after current day
                    })
        
        # Sort charging periods chronologically
        charging_periods.sort(key=lambda x: x['index'])
        
        # Calculate total energy available after all charging
        energy_stored = initial_energy_available
        for period in charging_periods:
            timestamp = period['timestamp']
            charge_amount = period['amount']
            
            solar_plan[timestamp] = {
                'type': 'charge',
                'amount': charge_amount,
                'price': period['price']
            }
            
            energy_stored += charge_amount * self.charge_efficiency
        
        # Prioritize discharge during highest-price periods
        discharge_candidates.sort(key=lambda x: x['price'], reverse=True)
        energy_available = energy_stored
        allocated_timestamps = []
        
        # Allocate energy to highest-price periods first
        for period in discharge_candidates:
            timestamp = period['timestamp']
            deficit = period['deficit']
            price = period['price']
            idx = period['index']
            
            # Skip periods before any charging if no initial energy is available
            if (len(charging_periods) == 0 or idx <= charging_periods[0]['index']) and initial_energy_available <= 0:
                continue
                
            discharge_amount = min(
                deficit, 
                max_power_per_interval,
                energy_available / self.discharge_efficiency
            )
            
            if discharge_amount > 0:
                solar_plan[timestamp] = {
                    'type': 'discharge',
                    'amount': discharge_amount,
                    'price': price
                }
                
                energy_available -= discharge_amount / self.discharge_efficiency
                allocated_timestamps.append(timestamp)
        
        # If energy remains, perform a chronological pass to allocate remaining energy
        if energy_available > 0:
            energy_accumulated = initial_energy_available
            all_data = day_data.copy()
            
            if next_day_data is not None:
                morning_cutoff = pd.Timestamp(next_day_data['date'].iloc[0]).replace(hour=10)
                next_day_morning = next_day_data[next_day_data['timestamp'] < morning_cutoff]
                all_data = pd.concat([all_data, next_day_morning])
            
            # Process timestamps chronologically
            for _, row in sorted(all_data.iterrows(), key=lambda x: x[1]['timestamp']):
                timestamp = row['timestamp']
                net_energy = row['return'] - row['supply']
                
                # Update accumulated energy from charging events
                if timestamp in solar_plan and solar_plan[timestamp]['type'] == 'charge':
                    energy_accumulated += solar_plan[timestamp]['amount'] * self.charge_efficiency
                
                # If deficit period not already allocated and energy available, discharge
                if (net_energy < 0 and 
                    timestamp not in allocated_timestamps and 
                    timestamp not in solar_plan and
                    energy_accumulated > 0):
                    
                    discharge_amount = min(
                        abs(net_energy),
                        max_power_per_interval,
                        energy_accumulated / self.discharge_efficiency
                    )
                    
                    if discharge_amount > 0:
                        solar_plan[timestamp] = {
                            'type': 'discharge',
                            'amount': discharge_amount,
                            'price': row['price']
                        }
                        
                        energy_accumulated -= discharge_amount / self.discharge_efficiency
        
        return solar_plan


