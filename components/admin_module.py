import streamlit as st

def run_admin_page():
    """
    Admin settings page for configuring battery model parameters.
    """
    st.title("Admin Settings")
    st.markdown("Configure battery model parameters for different types of installations.")
    
    # Add a back button at the top
    if st.button("← Back to Analysis", type="secondary"):
        st.session_state.current_page = "Battery Savings Analysis"
        st.rerun()
    
    # Load existing settings if available
    if 'battery_settings' in st.session_state:
        settings = st.session_state['battery_settings']
    else:
        settings = {
            'charge_efficiency': 1.0,
            'discharge_efficiency': 1.0,
            'min_state_of_charge': 0.0,
            'max_cycle_fraction': 0.5,
            'maximum_charge_rate_kw': None,
            'battery_type': "Custom",
            'battery_capacity': 100.0
        }
    
    with st.expander("Battery Technology Parameters", expanded=True):
        st.markdown("### Battery Efficiency and Technology")
        col1, col2 = st.columns(2)
        
        with col1:
            charge_efficiency = st.slider(
                "Charge Efficiency (%)", 
                min_value=80, 
                max_value=100, 
                value=int(settings.get('charge_efficiency', 1.0) * 100), 
                help="Percentage of energy retained during charging. Set to 100% for optimal debugging."
            ) / 100
            
            discharge_efficiency = st.slider(
                "Discharge Efficiency (%)", 
                min_value=80, 
                max_value=100, 
                value=int(settings.get('discharge_efficiency', 1.0) * 100), 
                help="Percentage of stored energy that can be discharged. Set to 100% for optimal debugging."
            ) / 100
        
        with col2:
            min_state_of_charge = st.slider(
                "Minimum State of Charge (%)", 
                min_value=0, 
                max_value=30, 
                value=int(settings.get('min_state_of_charge', 0.0) * 100), 
                help="Minimum battery level to maintain. Set to 0% for optimal debugging to allow full battery utilization."
            ) / 100
    
    with st.expander("Charging and Power Parameters", expanded=True):
        st.markdown("### Power Limits and Charging Rates")
        
        # Add battery capacity selection at the top
        battery_capacity = st.number_input(
            "Battery Capacity (kWh)", 
            min_value=10.0, 
            max_value=1000.0, 
            value=settings.get('battery_capacity', 100.0), 
            step=10.0,
            help="Total energy storage capacity of the battery system"
        )
        
        battery_type = st.selectbox(
            "Battery Installation Type",
            options=["Custom", "Small Residential (<50 kWh)", "Large Residential (50-100 kWh)", 
                    "Medium Commercial (100-250 kWh)", "Large Commercial/Farm (>250 kWh)"],
            index=["Custom", "Small Residential (<50 kWh)", "Large Residential (50-100 kWh)", 
                   "Medium Commercial (100-250 kWh)", "Large Commercial/Farm (>250 kWh)"].index(settings.get('battery_type', "Custom")),
            help="Select a predefined battery type or choose custom to configure manually"
        )
        
        # Set default values based on selection
        if battery_type == "Small Residential (<50 kWh)":
            default_c_rate = 0.5
            default_max_power = 10.0
            st.info("Small residential systems typically use up to 10 kW inverters with 0.5C rate")
        elif battery_type == "Large Residential (50-100 kWh)":
            default_c_rate = 0.7
            default_max_power = 50.0
            st.info("Large residential systems typically use up to 50 kW inverters with 0.7C rate")
        elif battery_type == "Medium Commercial (100-250 kWh)":
            default_c_rate = 0.8
            default_max_power = 100.0
            st.info("Medium commercial systems typically use up to 100 kW inverters with 0.8C rate")
        elif battery_type == "Large Commercial/Farm (>250 kWh)":
            default_c_rate = 0.9
            default_max_power = 250.0
            st.info("Large commercial systems typically use up to 250 kW inverters with 0.9C rate")
        else:  # Custom
            default_c_rate = 1.0
            default_max_power = None
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_cycle_fraction = st.slider(
                "Maximum C-Rate", 
                min_value=0.1, 
                max_value=2.0, 
                value=settings.get('max_cycle_fraction', 0.5), 
                step=0.1, 
                help="Maximum charge/discharge rate as a fraction of total capacity per hour. Lower value (0.5) for more stable behavior during debugging."
            )
        
        with col2:
            if battery_type == "Custom":
                # Determine if we should check the custom power box
                saved_max_power = settings.get('maximum_charge_rate_kw')
                use_custom_power = st.checkbox("Set Custom Maximum Power", value=saved_max_power is not None)
                
                if use_custom_power:
                    max_power_kw = st.number_input(
                        "Maximum Charge Power (kW)", 
                        min_value=1.0, 
                        max_value=1000.0, 
                        value=saved_max_power if saved_max_power is not None else 100.0, 
                        step=1.0,
                        help="Maximum power for charging/discharging in kilowatts."
                    )
                else:
                    st.info("Power will be automatically calculated based on battery capacity")
                    max_power_kw = None
            else:
                st.number_input(
                    "Maximum Charge Power (kW)",
                    min_value=1.0,
                    value=default_max_power,
                    disabled=True,
                    help="Predefined maximum power for this battery type"
                )
                max_power_kw = default_max_power
    
    # Save settings button
    if st.button("Save Settings", type="primary"):
        # Save the settings to session state
        st.session_state['battery_settings'] = {
            'charge_efficiency': charge_efficiency,
            'discharge_efficiency': discharge_efficiency,
            'min_state_of_charge': min_state_of_charge,
            'max_cycle_fraction': max_cycle_fraction,
            'maximum_charge_rate_kw': max_power_kw,
            'battery_type': battery_type,
            'battery_capacity': battery_capacity
        }
        st.success("Settings saved successfully! These will be applied to all future battery calculations.") 