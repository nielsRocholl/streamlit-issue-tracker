import pandas as pd
from utils.plotting.e_chart_options import get_price_flow_options, get_savings_bar_options


def price_flow_plot(usage_df, price_df):
    """Create an interactive plot showing energy flow and prices with echarts"""
    
    # Split usage data into supply and return
    supply_df = usage_df[usage_df['type'] == 'supply']
    return_df = usage_df[usage_df['type'] == 'return']
    
    # Merge supply, return and price data based on timestamp
    merged_df = pd.merge(
        pd.merge(
            supply_df.rename(columns={'value': 'supply'})[['timestamp', 'supply']], 
            return_df.rename(columns={'value': 'return'})[['timestamp', 'return']], 
            on='timestamp', how='outer'
        ),
        price_df[['timestamp', 'price']], 
        on='timestamp', how='outer'
    ).fillna(0)
   
    # Format timestamps for display
    x_data = [ts.strftime('%H:%M') for ts in merged_df['timestamp']]
    
    # Convert numeric data to lists, ensuring each value is a simple number
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    supply_data = safe_list(merged_df['supply'])
    return_data = safe_list(merged_df['return'])
    price_data = safe_list(merged_df['price'])
    
    # Get chart options from the options module
    options = get_price_flow_options(x_data, supply_data, return_data, price_data)
    
    return options

def savings_bar_plot(cost_without_battery, cost_with_battery, dates):
    """Create an enhanced visualization of cost savings using ECharts with new data structure"""
   
    # Get chart options from the options module
    options = get_savings_bar_options(dates, cost_without_battery, cost_with_battery)
    
    return options

