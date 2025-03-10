from datetime import datetime
import pandas as pd
import streamlit as st
from modules.kenter_module import KenterAPI
from modules.battery_module import BatterySavingsCalculator

def recalculate_savings(battery_capacity, enable_solar_arbitrage):
    """Recalculate savings without fetching new data"""
    if 'report_data' not in st.session_state:
        return
    
    # Get cached data
    usage_df = st.session_state.report_data['usage_df']
    price_df = st.session_state.report_data['price_df']
    tax_df = st.session_state.report_data['tax_df']
    
    # Apply settings from admin page if available
    battery_params = {}
    if 'battery_settings' in st.session_state:
        settings = st.session_state['battery_settings']
        battery_params = {
            'charge_efficiency': settings.get('charge_efficiency', 0.95),
            'discharge_efficiency': settings.get('discharge_efficiency', 0.95),
            'min_state_of_charge': settings.get('min_state_of_charge', 0.1),
            'max_cycle_fraction': settings.get('max_cycle_fraction', 1.0),
            'maximum_charge_rate_kw': settings.get('maximum_charge_rate_kw', None)
        }
    
    # Recalculate savings with the enhanced battery module
    battery_calculator = BatterySavingsCalculator(
        battery_capacity=battery_capacity,
        enable_solar_arbitrage=enable_solar_arbitrage,
        **battery_params
    )
    
    battery_results = battery_calculator.arbitrage(usage_df, price_df)
    savings = battery_results['savings']
    energy_flows_df = battery_results['energy_flows']
    
    # Recalculate daily costs with proper tax application
    daily_costs = calculate_daily_costs(
        usage_df, 
        price_df, 
        tax_df,
        energy_flows_df  # Pass energy flow data to properly apply tax only to grid energy
    )
    
    # Update session state
    st.session_state.report_data['savings'] = savings
    st.session_state.report_data['energy_flows_df'] = energy_flows_df
    st.session_state.report_data['daily_costs'] = daily_costs

def determine_time_grouping(start_date, end_date):
    """Determine appropriate time grouping based on date range"""
    days_difference = (end_date - start_date).days
    
    if days_difference <= 30:  # Less than a month
        return 'day', 'Daily'
    elif days_difference <= 90:  # 1-3 months
        return 'week', 'Weekly'
    else:  # More than 3 months
        return 'month', 'Monthly'

def group_data_by_time(df, time_unit, date_column='date'):
    """Group data by specified time unit (day, week, month)"""
    if df is None or df.empty or date_column not in df.columns:
        return df
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])
    
    # Create a copy to avoid modifying the original
    grouped_df = df.copy()
    
    if time_unit == 'day':
        # Already daily, no grouping needed
        return grouped_df
    elif time_unit == 'week':
        # Add week start date
        grouped_df['period'] = grouped_df[date_column].dt.to_period('W').dt.start_time
    elif time_unit == 'month':
        # Add month start date
        grouped_df['period'] = grouped_df[date_column].dt.to_period('M').dt.start_time
    
    # Group by the period
    numeric_columns = grouped_df.select_dtypes(include=['number']).columns
    
    # Group and aggregate
    result = grouped_df.groupby('period')[numeric_columns].sum().reset_index()
    
    # Rename period back to original date column
    result.rename(columns={'period': date_column}, inplace=True)
    
    return result


def validate_dates(start_date, end_date):
    """Validate date range."""
    today = datetime.now().date()
    
    if start_date > end_date:
        return False, "Start date must be before end date"
    
    if end_date >= today or start_date >= today:
        return False, "Dates need to be before today"
    
    date_diff = end_date - start_date
    if date_diff.days > 365:
        return False, "Date range cannot exceed 1 year"
    
    return True, ""


def calculate_daily_costs(usage_df, price_df, tax_df=None, energy_flows_df=None):
    """
    Calculate the daily energy costs including network tax if provided.
    
    Args:
        usage_df: DataFrame with energy usage data
        price_df: DataFrame with energy prices
        tax_df: Optional DataFrame with tax rates
        energy_flows_df: Optional DataFrame with detailed energy flow information from battery simulation
    
    Returns:
        DataFrame with daily costs
    """
    # Ensure we're working with copies
    usage_df = usage_df.copy()
    price_df = price_df.copy()
    
    # Convert timestamps to datetime
    usage_df['timestamp'] = pd.to_datetime(usage_df['timestamp'])
    price_df['timestamp'] = pd.to_datetime(price_df['timestamp'])
    
    # Get only supply data (energy consumed)
    supply_df = usage_df[usage_df['type'] == 'supply'].copy()
    
    # Merge with prices for energy cost calculation
    costs = pd.merge(supply_df, price_df[['timestamp', 'price']], on='timestamp', how='left')
    costs['energy_cost'] = costs['value'] * costs['price']
    
    # Add tax if provided - but only on grid-sourced energy
    if tax_df is not None and not tax_df.empty:
        tax_df = tax_df.copy()
        tax_df['timestamp'] = pd.to_datetime(tax_df['timestamp'])
        
        if energy_flows_df is not None and 'grid_origin_to_house' in energy_flows_df.columns:
            # Use the simplified approach with grid_origin_to_house field
            energy_flows_df = energy_flows_df.copy()
            energy_flows_df['timestamp'] = pd.to_datetime(energy_flows_df['timestamp'])
            
            # Create a DataFrame with only grid-sourced energy for tax calculation
            taxable_supply = pd.DataFrame({
                'timestamp': energy_flows_df['timestamp'],
                'value': energy_flows_df['grid_origin_to_house'],
                'type': 'grid_supply'
            })
            
            # Only keep rows with positive grid energy
            taxable_supply = taxable_supply[taxable_supply['value'] > 0]
        else:
            # Without energy flow data, assume all supply is taxable
            taxable_supply = supply_df.copy()
            taxable_supply['type'] = 'grid_supply'
        
        # Merge tax data with taxable supply
        tax_calc = pd.merge(taxable_supply, tax_df[['timestamp', 'tax_rate']], on='timestamp', how='left')
        
        # Calculate tax
        tax_calc['tax'] = tax_calc['value'] * (tax_calc['tax_rate'] / 100)  # Convert tax rate from cents to EUR
        
        # Aggregate tax by timestamp
        tax_by_timestamp = tax_calc.groupby('timestamp')['tax'].sum().reset_index()
        
        # Merge aggregated tax back to the original costs
        costs = pd.merge(costs, tax_by_timestamp, on='timestamp', how='left')
        costs['tax'] = costs['tax'].fillna(0)
    else:
        costs['tax'] = 0
    
    # Calculate total cost
    costs['cost'] = costs['energy_cost'] + costs['tax']
    
    # Group by date
    costs['date'] = costs['timestamp'].dt.date
    # Convert date objects to datetime64 for consistency with savings dataframe
    costs['date'] = pd.to_datetime(costs['date'])
    
    daily_costs = costs.groupby('date').agg({
        'cost': 'sum',
        'energy_cost': 'sum',
        'tax': 'sum'
    }).reset_index()
    
    return daily_costs

def get_meter_hierarchy():
    """Retrieve and cache meter structure with formatted connection name -> (connection_id, main_metering_point, gtv) mapping"""
    if 'meter_hierarchy' not in st.session_state:
        try:
            api = KenterAPI()
            meter_data = api.get_meter_list()
            gtv_info = api.get_gtv_info()
            hierarchy = {}
            
            for connection in meter_data:
                conn_id = connection.get('connectionId')
                if not conn_id:
                    continue

                # Find main metering point
                main_mp = None
                for mp in connection.get('meteringPoints', []):
                    if mp.get('meteringPointType') == 'OP' and mp.get('relatedMeteringPointId') is None:
                        main_mp = mp.get('meteringPointId')
                        break  # Found main point

                # Get connection name details and GTV info
                connection_name = conn_id  # default if no name found
                if connection.get('meteringPoints'):
                    master_data = connection['meteringPoints'][0].get('masterData', [{}])[0]
                    bp_code = master_data.get('bpCode', '')
                    bp_name = master_data.get('bpName', '')
                    if bp_code and bp_name:
                        connection_name = f"{bp_code} - {bp_name}"

                # Get GTV info for this connection
                gtv_data = gtv_info.get(conn_id, {})
                
                hierarchy[connection_name] = {
                    'connection_id': conn_id,
                    'main_meter': main_mp,
                    'gtv': gtv_data.get('gtv'),
                    'address': gtv_data.get('address'),
                    'city': gtv_data.get('city')
                }

            st.session_state.meter_hierarchy = hierarchy
        except Exception as e:
            st.error(f"Error fetching meter data: {str(e)}")
            st.session_state.meter_hierarchy = {}
    
    return st.session_state.meter_hierarchy

# Function to clear report state when connection changes
def clear_report_state():
    st.session_state.show_report = False
    if 'report_data' in st.session_state:
        del st.session_state.report_data