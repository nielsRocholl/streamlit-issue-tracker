from typing import Literal
import pandas as pd
from datetime import time
import holidays
import streamlit as st

class NetworkTaxCalculator:
    """Calculator for network operator specific energy taxes."""
    
    NETWORK_OPERATORS = ["Enexis"]  # Add more operators as needed
    
    # Tax rates per operator (in cents/kWh)
    TAX_RATES = {
        "Enexis": {
            "low_gtv": {  # < 50 kW
                "normal": 8.04,
                "low": 4.21
            },
            "high_gtv": {  # >= 50 kW
                "normal": 2.50,
                "low": 2.50
            }
        }
    }
    
    @staticmethod
    def get_tax_rate(operator: str, gtv: float, rate_type: Literal["normal", "low"]) -> float:
        """
        Get the appropriate tax rate based on operator, GTV, and rate type.
        
        Args:
            operator: Network operator name
            gtv: Contracted capacity in kW
            rate_type: Type of rate ("normal" or "low")
            
        Returns:
            Tax rate in cents/kWh
        """
        if operator not in NetworkTaxCalculator.TAX_RATES:
            raise ValueError(f"Unknown network operator: {operator}")
            
        # For now, only implement Enexis logic
        if operator == "Enexis":
            gtv_category = "low_gtv" if gtv < 50 else "high_gtv"
            return NetworkTaxCalculator.TAX_RATES[operator][gtv_category][rate_type]
        
        return 0.0
    
    @staticmethod
    def determine_rate_type(timestamp) -> str:
        """
        Determine the rate type based on the timestamp.
        
        Normal rate: working days 7:00 AM - 11:00 PM
        Low rate: working days 11:00 PM - 7:00 AM
        Low rate: All day on weekends and public holidays
        
        Args:
            timestamp: The timestamp to evaluate
            
        Returns:
            rate_type: "normal" or "low"
        """
        # Convert to pandas Timestamp if not already
        ts = pd.Timestamp(timestamp)
        
        # Check if it's a weekend (Saturday = 5, Sunday = 6)
        if ts.dayofweek >= 5:
            return "low"
        
        # Check if it's a holiday in the Netherlands
        nl_holidays = holidays.NL()
        if ts.date() in nl_holidays:
            return "low"
        
        # Check time of day
        ts_time = ts.time()
        morning_start = time(7, 0)  # 7:00 AM
        night_start = time(23, 0)   # 11:00 PM
        
        if morning_start <= ts_time < night_start:
            return "normal"
        else:
            return "low"
    
    @staticmethod
    def get_tax_per_kwh(timestamp, operator: str = None, gtv: float = None) -> float:
        """
        Get the tax per kWh based on timestamp, operator, and GTV.
        Uses Streamlit session state for operator and GTV if not provided.
        
        Args:
            timestamp: The timestamp to evaluate
            operator: Network operator name (optional, will use session state if not provided)
            gtv: Contracted capacity in kW (optional, will use session state if not provided)
            
        Returns:
            Tax rate in euros/kWh
            
        Raises:
            ValueError: If operator or GTV cannot be determined from parameters or session state
        """
        # Get operator and GTV from session state if not provided
        if operator is None:
            if 'network_operator' in st.session_state:
                operator = st.session_state.network_operator
            else:
                raise ValueError("Network operator not provided and not found in session state")
        
        if gtv is None:
            if 'gtv' in st.session_state:
                try:
                    gtv = float(st.session_state.gtv)
                except (ValueError, TypeError):
                    raise ValueError("GTV in session state could not be converted to a number")
            else:
                raise ValueError("GTV not provided and not found in session state")
        
        # Determine rate type based on timestamp
        rate_type = NetworkTaxCalculator.determine_rate_type(timestamp)
        
        # Get tax rate in cents/kWh
        tax_rate_cents = NetworkTaxCalculator.get_tax_rate(operator, gtv, rate_type)
        
        # Convert to euros/kWh
        tax_rate_euros = tax_rate_cents / 100
        
        return tax_rate_euros
    
    