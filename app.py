import streamlit as st
from modules.kenter_module import get_kenter_data
from modules.entsoe_module import get_energy_prices
from modules.battery_module import BatterySavingsCalculator
from components.admin_module import run_admin_page
from components.sidebar import run_sidebar
from utils.utils import *
from auth.authenticator import Authenticator
from datetime import datetime
from streamlit_echarts import st_echarts
import pandas as pd
from utils.plotting.plotting import *
from utils.calculations.calculations import *



# Set page configuration
st.set_page_config(
    page_title="Energy Storage Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS to fix chart visibility in tabs
streamlit_style = """
    <style>
    iframe[title="streamlit_echarts.st_echarts"]{ height: 1000px;} 
    </style>
    """
st.markdown(streamlit_style, unsafe_allow_html=True)

# Initialize the Authenticator
allowed_users = st.secrets["ALLOWED_USERS"].split(",")
authenticator = Authenticator(
    allowed_users=allowed_users,
    token_key=st.secrets["TOKEN_KEY"],
    client_secret=st.secrets["CLIENT_SECRET"],
    redirect_uri= "http://localhost:8501" #"https://mango2mango.streamlit.app/" #"http://localhost:8501" #
)

def main():
    # Initialize page state if not exists
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Battery Savings Analysis"
    
    # Use pages in sidebar
    if st.session_state.current_page == "Battery Savings Analysis":
        run_main_app()
    elif st.session_state.current_page == "Admin Settings":
        run_admin_page()

def run_main_app():
    # Header with title in modern layout
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.title("Energy Analyzer")
        st.caption("Smart Battery Solutions for Solar Systems")
    
    # Authentication check
    authenticator.check_auth()
    
    # Account info in top right
    with header_col2:
        if st.session_state.get("connected"):
            st.markdown(
                f"""
                <div style="text-align: right; padding: 10px; border-radius: 5px;">
                    <small>Logged in as: {st.session_state['user_info'].get('email', 'User')}</small><br>
                    <a href="?logout=true" target="_self">Logout</a>
                </div>
                """, 
                unsafe_allow_html=True
            )
            # Handle logout via URL parameter using the new query_params API
            if st.query_params.get("logout"):
                authenticator.logout()
                st.rerun()
        else:
            # Keep the header area clean when not logged in
            st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    # Call the sidebar component instead of having the sidebar code here
    sidebar_data = run_sidebar(authenticator)
    
    # Extract values from sidebar data
    selected_conn_name = sidebar_data['selected_conn_name']
    connection_id = sidebar_data['connection_id']
    main_meter = sidebar_data['main_meter']
    battery_capacity = sidebar_data['battery_capacity']
    enable_solar_arbitrage = sidebar_data['enable_solar_arbitrage']

    # Main content area - Only visible for authenticated users
    if st.session_state.get("connected"):
        # Analysis Period section moved from sidebar to main content area
        st.markdown("## Analysis Period")
        
        # Create a 3-column layout for the Analysis Period section
        date_col1, date_col2, date_col3 = st.columns([1, 1, 1])
        
        # Calculate default dates: yesterday and 15 days before yesterday
        yesterday = datetime.now().date() - pd.Timedelta(days=1)
        default_start_date = yesterday - pd.Timedelta(days=14)
        
        # Date inputs in main content area
        with date_col1:
            start_date = st.date_input(
                "Start Date", 
                value=default_start_date, 
                help="Select the beginning of the analysis period"
            )
        
        with date_col2:
            end_date = st.date_input(
                "End Date", 
                value=yesterday, 
                help="Select the end of the analysis period"
            )
        
        # Generate Report button in main content area
        with date_col3:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
            generate_report = st.button("Generate Report", type="primary", use_container_width=True)
        
        st.markdown("---")
        
        # Process the Generate Report button click
        if generate_report:
            st.session_state.show_report = True
            if start_date and end_date and selected_conn_name:
                valid, error_message = validate_dates(start_date, end_date)
                if not valid:
                    st.error(error_message)
                    st.session_state.show_report = False
                    return
                
                # Check if GTV and network operator are available in session state
                if 'gtv' not in st.session_state:
                    st.error("Contracted capacity (GTV) is not available. Please select a client connection with GTV information.")
                    st.session_state.show_report = False
                    return
                
                if 'network_operator' not in st.session_state:
                    st.error("Network operator is not selected. Please select a network operator in the sidebar.")
                    st.session_state.show_report = False
                    return
                
                try:
                    with st.spinner('Analyzing energy data and calculating savings...'):
                        # Fetch data
                        usage_df = get_kenter_data(
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d'),
                            connection_id=connection_id,
                            metering_point=main_meter,
                        )
                        calculate_covernment_tax(usage_df, connection_id, main_meter)
                        
                        price_df = get_energy_prices(
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                        
                        # Ensure battery_capacity has a value
                        if 'battery_capacity' not in locals() or battery_capacity is None:
                            # Use settings if available, otherwise use default
                            if 'battery_settings' in st.session_state:
                                battery_capacity = st.session_state['battery_settings'].get('battery_capacity', 100.0)
                            else:
                                battery_capacity = 100.0
                        
                        # Get battery parameters from settings if available
                        battery_params = {}
                        if 'battery_settings' in st.session_state:
                            settings = st.session_state['battery_settings']
                            battery_params = {
                                'charge_efficiency': settings.get('charge_efficiency', 1.0),
                                'discharge_efficiency': settings.get('discharge_efficiency', 1.0),
                                'min_state_of_charge': settings.get('min_state_of_charge', 0.0),
                                'max_cycle_fraction': settings.get('max_cycle_fraction', 0.5),
                                'maximum_charge_rate_kw': settings.get('maximum_charge_rate_kw', None)
                            }
                        
                        # Calculate potential battery savings
                        battery_calculator = BatterySavingsCalculator(
                            battery_capacity=battery_capacity,
                            enable_solar_arbitrage=enable_solar_arbitrage,
                            **battery_params
                        )
                        

                        # The arbitrage function now returns a dict with both savings and energy_flows
                        battery_results = battery_calculator.arbitrage(usage_df, price_df)

                        missing_intervals = battery_results['missing_intervals']
                        transaction_history_charge = battery_results['transaction_history_charge']
                        transaction_history_discharge = battery_results['transaction_history_discharge']
                        transaction_history_solar_export = battery_results['transaction_history_solar_export']
                        battery_history = battery_results['battery_history']
                        
                        # Calculate metrics including tax, now with energy source tracking
                        daily_costs = calculate_daily_costs(usage_df, price_df)
                                                
                        # Store the data for recalculation without fetching again
                        st.session_state.report_data = {
                            'usage_df': usage_df,
                            'price_df': price_df,
                            'daily_costs': daily_costs,
                            'transaction_history_discharge': transaction_history_discharge,
                            'transaction_history_charge': transaction_history_charge,
                            'transaction_history_solar_export': transaction_history_solar_export,
                            'battery_history': battery_history,
                            'generated_at': datetime.now()
                        }
                        
                except Exception as e:
                    if 'timestamp' in str(e):
                        st.error("No data available for the selected meter and date range.")
                    else:
                        st.error(f"Error generating report: {str(e)}")
                    st.session_state.show_report = False
                    st.session_state.pop('report_data', None)
                    return

        # Initialize the show_report state if it doesn't exist
        if 'show_report' not in st.session_state:
            st.session_state.show_report = False

        # Display report content organized in tabs for better navigation
        if st.session_state.show_report and 'report_data' in st.session_state:
            report_data = st.session_state.report_data
            usage_df = report_data['usage_df']
            price_df = report_data['price_df']
            daily_costs = report_data['daily_costs']
            transaction_history_discharge = report_data['transaction_history_discharge']
            transaction_history_charge = report_data['transaction_history_charge']
            transaction_history_solar_export = report_data['transaction_history_solar_export']
            battery_history = report_data['battery_history']

            cost_without_battery, cost_with_battery, dates = calculate_cost_with_and_without_battery(daily_costs, transaction_history_discharge, transaction_history_charge, transaction_history_solar_export, usage_df, main_meter, connection_id)

            
            st.markdown("---")
            
            
            # Key metrics in a prominent row
            st.markdown("## Battery Impact Summary")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric(
                    "Current Energy Costs", 
                    f"€{np.sum(cost_without_battery):.2f}".replace('.', ','), 
                    help="Total energy costs without a battery system"
                )
            
            with metric_col2:
                st.metric(
                    "Potential Savings", 
                    f"€{(np.sum(cost_without_battery) - np.sum(cost_with_battery)):.2f}".replace('.', ','), 
                    help="Total savings with the selected battery configuration"
                )
            
            with metric_col3:
                st.metric(
                    "New Energy Costs", 
                    f"€{np.sum(cost_with_battery):.2f}".replace('.', ','), 
                    help="Total energy costs after implementing the battery system"
                )
                
            with metric_col4:
                savings_percentage = (np.sum(cost_without_battery) - np.sum(cost_with_battery)) / np.sum(cost_without_battery) * 100
                st.metric(
                    "Percentage Saved", 
                    f"{savings_percentage:.1f}%".replace('.', ','),
                    delta_color="inverse",
                    help="Percentage of energy costs saved with the battery system"
                )
            
            # Organize detailed content in tabs with new order
            report_tabs = st.tabs([
                "Savings Analysis", 
                "Detailed Metrics",
                "Battery ROI",
                "Energy Flow"
            ])

            echarts_options_tab1 = savings_bar_plot(cost_without_battery, cost_with_battery, dates)
            echarts_options_tab4 = price_flow_plot(usage_df, price_df)
            # Tab 1: Savings Analysis
            with report_tabs[0]:
                st.markdown(f"### Battery Savings Potential ")
                
                # Display contextual information above the chart
                explanation_col1, explanation_col2 = st.columns([3, 1])
                with explanation_col1:
                    st.markdown(f"""
                    This chart shows your client's **{None} energy costs** with and without a battery system:
                    - The **red** show current costs without a battery
                    - The **blue** shows costs after battery savings
                    """)
                
                # Create the ECharts options - use the same function but with grouped data
                st_echarts(options=echarts_options_tab1, height="500px", key="cost_savings_chart")
                    
                st.markdown(f"### {None} Savings Breakdown")
                st.markdown(f"""
                This chart shows how your client's savings are calculated ({None} aggregation):
                - **Solar Savings**: Money saved by using stored solar energy
                - **Lost Solar Revenue**: Money not received from selling excess solar to the grid (because it was stored instead)
                - **Net Savings**: Total savings after all factors are considered
                """)

            # Tab 2: Detailed Metrics
            with report_tabs[1]:
                st.markdown("### Energy & Cost Details")
                
            # Tab 3: Battery ROI
            with report_tabs[2]:
                st.markdown("### Return on Investment")
            
            # Tab 4: Energy Flow (moved to end)
            with report_tabs[3]:
                st.markdown("### Energy Flow & Electricity Prices")
                st.markdown("""
                This chart shows the relationship between energy consumption, production, and electricity prices:
                - **Coral bars**: Energy consumed from the grid
                - **Blue bars**: Solar energy returned to the grid
                - **Teal line**: Electricity price variations throughout the period
                """)
                
                st_echarts(options=echarts_options_tab4, height="500px", key="price_flow_chart")

            # Report footer with timestamp
            st.markdown("---")
                
        elif not st.session_state.show_report:
            st.info("Select your client's connection and date range in the sidebar, then click 'Generate Report' to begin the analysis.")
    
    else:
        # Display demo message for users who haven't logged in
        st.markdown("")

if __name__ == "__main__":
    main()