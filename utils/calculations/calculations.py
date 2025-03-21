import numpy as np
import pandas as pd


def calculate_cost_with_and_without_battery(daily_costs=None, transaction_history_discharge=None, transaction_history_charge=None, transaction_history_solar_export=None):

    # to calculate the true cost, we need to subtract the money we could have made by selling our excess solar.
    
    # Add date column to both dataframes
    daily_costs['date'] = daily_costs['timestamp'].dt.date
    transaction_history_discharge['date'] = transaction_history_discharge['timestamp'].dt.date
    transaction_history_charge['date'] = transaction_history_charge['timestamp'].dt.date
    transaction_history_solar_export['date'] = transaction_history_solar_export['timestamp'].dt.date

    
    # Group by date to get daily totals
    daily_costs_grouped = daily_costs.groupby('date')['cost'].sum().reset_index()
    daily_savings = transaction_history_discharge.groupby('date')['saved'].sum().reset_index()
    daily_lost_revenue_not_sold_solar = transaction_history_charge.groupby('date')['lost_revenue'].sum().reset_index()
    daily_revenue_selling_all_solar = transaction_history_solar_export.groupby('date')['revenue'].sum().reset_index()
    
    # Calculate revenue from uncharged solar
    daily_revenue_selling_uncharged_solar = pd.DataFrame({
        'date': daily_revenue_selling_all_solar['date'],
        'revenue_selling_uncharged_solar': daily_revenue_selling_all_solar['revenue'] - daily_lost_revenue_not_sold_solar['lost_revenue']
    })
    
    # Merge daily costs and savings
    merged_data = pd.merge(
        daily_costs_grouped,
        pd.merge(
            daily_savings,
            pd.merge(
                daily_lost_revenue_not_sold_solar,
                pd.merge(
                    daily_revenue_selling_all_solar,
                    daily_revenue_selling_uncharged_solar,
                    on='date'
                ),
                on='date'
            ),
            on='date'
        ),
        on='date',
        how='outer'
    )
    
    # Fill NaN values with 0
    merged_data = merged_data.fillna(0)
    
    # Calculate cost with battery
    merged_data['cost_with_battery'] = merged_data['cost'] - merged_data['saved'] - merged_data['revenue_selling_uncharged_solar']

    # update the original cost to include revenue of selling solar
    merged_data['cost'] = merged_data['cost'] - merged_data['revenue']

    # remove very last row
    merged_data = merged_data.iloc[:-1]

    merged_data.to_csv('merged.csv')
    
    # Format dates for display
    dates = [d.strftime('%b %d') for d in merged_data['date']]
    
    # Convert numeric data to lists, ensuring each value is a simple number 
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    cost_without_battery = safe_list(merged_data['cost'])
    cost_with_battery = safe_list(merged_data['cost_with_battery'])

    
    return cost_without_battery, cost_with_battery, dates
    