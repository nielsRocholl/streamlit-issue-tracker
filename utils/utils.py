from datetime import datetime
import pandas as pd
import streamlit as st
from modules.kenter_module import KenterAPI
from modules.tax_module import NetworkTaxCalculator


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


def calculate_daily_costs(usage_df, price_df):
    """Calculate daily costs by multiplying usage with price and adding the tax."""
    # Filter out 'return' type
    tax_calculator = NetworkTaxCalculator()
    usage = usage_df[usage_df['type'] != 'return'].copy()
    merged_df = pd.merge(
        usage,
        price_df,
        on='timestamp',
        how='inner'
    )
    
    merged_df['tax'] = merged_df['timestamp'].apply(lambda x: tax_calculator.get_tax_per_kwh(x))

    merged_df['cost'] = merged_df['value'] * merged_df['price'] + merged_df['value'] * merged_df['tax']
    result_df = merged_df[['timestamp', 'cost']].copy()
    result_df = result_df.groupby('timestamp')['cost'].sum().reset_index()

    return result_df

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
