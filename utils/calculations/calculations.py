import numpy as np
import pandas as pd
import streamlit as st
from modules.kenter_module import KenterAPI
from modules.tax_module import GovernmentTaxCalculator


def calc_tax_scenarios(usage_df, transaction_history_discharge, connection_id, main_meter):
    """Calculate government tax in both scenarios: with and without battery"""
    # Filter and prepare dataframes
    usage_supply = usage_df[usage_df['type'] == 'supply'].copy()
    discharge_df = transaction_history_discharge[['timestamp', 'amount']].copy()
    
    # Create usage_with_battery by merging and subtracting battery discharge
    usage_with_battery = pd.merge(usage_supply, discharge_df, on='timestamp', how='left')
    usage_with_battery['amount'] = usage_with_battery['amount'].fillna(0)
    usage_with_battery['value_with_battery'] = usage_with_battery['value'] - usage_with_battery['amount']
    usage_with_battery['value_with_battery'] = usage_with_battery['value_with_battery'].clip(lower=0)
    
    # Create battery usage df in same format as original
    battery_usage_df = usage_df.copy()
    battery_usage_df.loc[battery_usage_df['type'] == 'supply', 'value'] = \
        usage_with_battery['value_with_battery'].values
    
    # Calculate tax for both scenarios
    tax_without_battery = calculate_covernment_tax(usage_df, connection_id, main_meter)
    tax_with_battery = calculate_covernment_tax(battery_usage_df, connection_id, main_meter)
    
    # Combine results
    tax_data = pd.merge(
        tax_without_battery[['timestamp', 'type', 'gov_tax']].rename(columns={'gov_tax': 'tax_without_battery'}),
        tax_with_battery[['timestamp', 'type', 'gov_tax']].rename(columns={'gov_tax': 'tax_with_battery'}),
        on=['timestamp', 'type']
    )
    
    return tax_data


def calculate_cost_with_and_without_battery(daily_costs, transaction_history_discharge, transaction_history_charge, transaction_history_solar_export, usage_df, main_meter, connection_id):
    # Calculate government tax with/without battery
    tax_data = calc_tax_scenarios(usage_df, transaction_history_discharge, connection_id, main_meter)
    
    # Add date column to tax_data and group by date
    tax_data['date'] = tax_data['timestamp'].dt.date
    # Only consider supply type for tax totals
    supply_tax = tax_data[tax_data['type'] == 'supply']
    daily_tax = supply_tax.groupby('date').agg({
        'tax_without_battery': 'sum',
        'tax_with_battery': 'sum'
    }).reset_index()
    daily_tax.to_csv("tax.csv")
    
    # NOTE from here on, you need to add the tax and check if it is correct. 


    
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
    
    # Format dates for display
    dates = [d.strftime('%b %d') for d in merged_data['date']]
    
    # Convert numeric data to lists, ensuring each value is a simple number 
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    cost_without_battery = safe_list(merged_data['cost'])
    cost_with_battery = safe_list(merged_data['cost_with_battery'])

    
    return cost_without_battery, cost_with_battery, dates


def calculate_covernment_tax(usage_df, connection_id, main_meter):
    """
    Calculate government tax for each interval in the usage dataframe.
    
    The tax bracket is determined by cumulative usage from January 1st to current timestamp,
    with the counter resetting each January 1st. First calculates usage from Jan 1st to start date,
    then applies correct tax rate to each interval based on running total.
    
    Args:
        usage_df (DataFrame): DataFrame with 'timestamp' and 'value' columns
        connection_id (str): The connection ID for the Kenter API
        main_meter (str): The metering point ID for the Kenter API
        
    Returns:
        DataFrame: Original usage_df with 'gov_tax' column added
    """
    # Get the start and end dates from usage_df - make sure they're timezone naive
    start_date = usage_df['timestamp'].min().replace(tzinfo=None)
    end_date = usage_df['timestamp'].max().replace(tzinfo=None)
    
    if not connection_id or not main_meter:
        raise ValueError("Connection ID and metering point must be provided")
    
    # Initialize KenterAPI
    api = KenterAPI(connection_id=connection_id, metering_point=main_meter)
    
    # Create a copy of usage_df to avoid modifying the original
    result_df = usage_df.copy()
    
    # Filter only supply type entries
    supply_df = result_df[result_df['type'] == 'supply'].copy()
    
    # Initialize gov_tax column
    result_df['gov_tax'] = 0.0
    
    # Initialize the GovernmentTaxCalculator
    tax_calculator = GovernmentTaxCalculator()
    
    # Group the data by year to handle year transitions
    supply_df['year'] = supply_df['timestamp'].dt.year
    years = sorted(supply_df['year'].unique())
    
    for year in years:
        # Reset cumulative usage for each new year
        cumulative_usage = 0
        
        # For the first year, calculate usage from January 1st to start date
        if year == start_date.year:
            # Create timezone naive January 1st
            jan_first = pd.Timestamp(f"{year}-01-01").replace(tzinfo=None)
            
            # Calculate the month before the start date - keep timezone naive
            month_before_start = (start_date.replace(day=1) - pd.Timedelta(days=1))
            
            # If start date is in January, we don't need to get monthly data
            if month_before_start.year == year:
                # Get monthly data from January to the month before start date
                for year_month in pd.date_range(jan_first, month_before_start, freq='MS'):
                    month_data = api._get_month_data(year_month.year, year_month.month)
                    
                    # Extract supply data (16180 is the channel ID for supply)
                    for channel in month_data:
                        if channel['channelId'] == '16180':  # Supply channel
                            for measurement in channel.get('Measurements', []):
                                cumulative_usage += measurement['value']
            
            # Get daily data from start of month to day before start date
            start_of_month = start_date.replace(day=1)
            if start_date.day > 1:  # Only if start date is not the 1st of the month
                for day in pd.date_range(start_of_month, start_date - pd.Timedelta(days=1), freq='D'):
                    # Convert to datetime for API call
                    day_dt = day.to_pydatetime().replace(tzinfo=None)
                    day_data = api._get_day_data(day_dt)
                    
                    # Extract supply data
                    for channel in day_data:
                        if channel['channelId'] == '16180':  # Supply channel
                            for measurement in channel.get('Measurements', []):
                                cumulative_usage += measurement['value']
        
        # Process intervals for this year
        year_supply = supply_df[supply_df['year'] == year].sort_values('timestamp')
        
        for idx, row in year_supply.iterrows():
            current_tax_rate = tax_calculator.get_tax_rate(cumulative_usage)
            result_df.loc[idx, 'gov_tax'] = row['value'] * current_tax_rate
            cumulative_usage += row['value']
    
    
    return result_df
    