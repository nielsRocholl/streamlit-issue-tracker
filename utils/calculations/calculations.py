import numpy as np
import pandas as pd


def calculate_cost_with_and_without_battery(daily_costs=None, transaction_history_discharge=None):
        
    # Add date column to both dataframes
    daily_costs['date'] = daily_costs['timestamp'].dt.date
    transaction_history_discharge['date'] = transaction_history_discharge['timestamp'].dt.date
    
    # Group by date to get daily totals
    daily_costs_grouped = daily_costs.groupby('date')['cost'].sum().reset_index()
    daily_savings = transaction_history_discharge.groupby('date')['saved'].sum().reset_index()
    
    # Merge daily costs and savings
    merged_data = pd.merge(
        daily_costs_grouped,
        daily_savings,
        on='date',
        how='outer'
    )
    
    # Fill NaN values with 0
    merged_data = merged_data.fillna(0)
    
    # Calculate cost with battery
    merged_data['final_cost'] = merged_data['cost'] - merged_data['saved']

    # remove very last row
    merged_data = merged_data.iloc[:-1]
    
    # Format dates for display
    dates = [d.strftime('%b %d') for d in merged_data['date']]
    
    # Convert numeric data to lists, ensuring each value is a simple number 
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    cost_without_battery = safe_list(merged_data['cost'])
    cost_with_battery = safe_list(merged_data['final_cost'])
    
    return cost_without_battery, cost_with_battery, dates
    