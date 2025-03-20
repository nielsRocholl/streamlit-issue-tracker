import streamlit as st
from utils.utils import get_meter_hierarchy, clear_report_state
from modules.tax_module import NetworkTaxCalculator

def run_sidebar(authenticator):
    # Sidebar configuration - cleaner and more organized
    with st.sidebar:
        # Create a container for the main sidebar content
        sidebar_content = st.container()
        
        # Then render the main content
        with sidebar_content:
            if st.session_state.get("connected"):
                # Client selection section with better spacing
                st.markdown("## Client Data")
                meter_hierarchy = get_meter_hierarchy()

                # Connection selection with improved layout
                connection_names = list(meter_hierarchy.keys())
                
                # Store the selected connection in session state to persist across page navigation
                if 'selected_conn_name' not in st.session_state:
                    st.session_state.selected_conn_name = connection_names[0]
                
                selected_conn_name = st.selectbox(
                    "Client Connection Point",
                    options=connection_names,
                    index=connection_names.index(st.session_state.selected_conn_name) if st.session_state.selected_conn_name in connection_names else 0,
                    help="Select the client's facility connection point",
                    on_change=clear_report_state
                )
                
                # Update the session state with the current selection
                st.session_state.selected_conn_name = selected_conn_name

                # Get connection details automatically
                if selected_conn_name:
                    conn_details = meter_hierarchy[selected_conn_name]
                    connection_id = conn_details['connection_id']
                    main_meter = conn_details['main_meter']
                    
                    # Clean up client data presentation with consistent styling
                    st.markdown("#### Client Details")
                    if conn_details.get('address') and conn_details.get('city'):
                        st.markdown(f"**Location:** {conn_details['address']}, {conn_details['city']}")
                    
                    # Display GTV in a consistent format
                    if conn_details.get('gtv'):
                        st.markdown(f"**Contracted Capacity:** {conn_details.get('gtv', 'N/A')} kW")
                        # Store GTV in session state
                        st.session_state.gtv = conn_details.get('gtv', 'N/A')
                
                st.markdown("---")
                
                # Battery configuration
                st.subheader("⚡ Battery Configuration")
                
                # Add admin button at the top of battery configuration
                if st.session_state.get("connected"):
                    if st.button("Configure Battery Settings", type="primary", use_container_width=True):
                        st.session_state.current_page = "Admin Settings"
                        st.rerun()
                
                # Use saved battery settings if available
                if 'battery_settings' in st.session_state:
                    settings = st.session_state['battery_settings']
                    battery_type = settings.get('battery_type', 'Custom')
                    battery_capacity = settings.get('battery_capacity', 100.0)
                    st.info(f"Using custom settings from Admin page:\n- Battery type: {battery_type}\n- Capacity: {battery_capacity} kWh\n- C-rate: {settings.get('max_cycle_fraction', 1.0)}")
                    
                    # Add a button to view detailed settings
                    if st.button("View Detailed Settings"):
                        with st.expander("Battery Settings Details", expanded=True):
                            st.write("**Efficiency Parameters:**")
                            st.write(f"- Charge Efficiency: {settings.get('charge_efficiency', 0.95)*100:.1f}%")
                            st.write(f"- Discharge Efficiency: {settings.get('discharge_efficiency', 0.95)*100:.1f}%")
                            st.write(f"- Min State of Charge: {settings.get('min_state_of_charge', 0.1)*100:.1f}%")
                            
                            st.write("**Power Parameters:**")
                            st.write(f"- Max C-rate: {settings.get('max_cycle_fraction', 1.0)}")
                            max_power = settings.get('maximum_charge_rate_kw')
                            if max_power is None:
                                st.write("- Auto-calculated maximum power based on battery size")
                            else:
                                st.write(f"- Maximum Charge Power: {max_power} kW")
                    
                    # Add a button to reset to defaults
                    if st.button("Reset to Default Settings"):
                        if 'battery_settings' in st.session_state:
                            del st.session_state['battery_settings']
                        st.success("Reset to default settings. Page will refresh.")
                        st.experimental_rerun()
                else:
                    st.info("Using default settings. Visit Admin Settings page to customize.")
                    battery_capacity = 100.0  # Default battery capacity when no settings are available
                
                # Energy arbitrage options
                enable_solar_arbitrage = st.toggle(
                    "Solar Storage",
                    value=True,
                    help="Store excess solar energy to use during expensive periods"
                )
                    
                # If any settings change and we have data, recalculate
                if 'report_data' in st.session_state:
                    # Create a settings tuple that includes all relevant settings
                    current_settings = {
                        'battery_capacity': battery_capacity,
                        'enable_solar_arbitrage': enable_solar_arbitrage,
                        'battery_settings_id': id(st.session_state.get('battery_settings', {}))
                    }
                    
                    if 'last_settings' not in st.session_state:
                        st.session_state.last_settings = current_settings
                    
                    if current_settings != st.session_state.last_settings:
                        st.session_state.last_settings = current_settings
                        # recalculate_savings(battery_capacity, enable_solar_arbitrage)
                
                # Network operator in its own section
                with st.expander("Network & Grid", expanded=True):
                    network_operator = st.selectbox(
                        "Network Operator",
                        options=NetworkTaxCalculator.NETWORK_OPERATORS,
                        index=0,
                        help="Select the client's network operator for accurate tax calculations"
                    )
                    # Store network operator in session state
                    st.session_state.network_operator = network_operator
            else:
                st.info("Please log in to access the analyzer")
                
                # Add a big, visible login button in the sidebar
                auth_url = authenticator.get_auth_url()
                st.link_button("Login with Google", auth_url, type="primary", use_container_width=True)
                
    # Return necessary values that the main app needs
    return {
        'selected_conn_name': selected_conn_name if 'selected_conn_name' in locals() else None,
        'connection_id': connection_id if 'connection_id' in locals() else None,
        'main_meter': main_meter if 'main_meter' in locals() else None,
        'battery_capacity': battery_capacity if 'battery_capacity' in locals() else 100.0,
        'enable_solar_arbitrage': enable_solar_arbitrage if 'enable_solar_arbitrage' in locals() else True,
        'conn_details': conn_details if 'conn_details' in locals() else None
    } 