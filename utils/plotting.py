import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math  # Add math import for ceil function


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
   
    # Modern colors for 2025 tech aesthetic
    color_supply = '#FF6B6B'  # Coral for grid consumption
    color_return = '#4361EE'  # Blue for solar production
    color_price = '#2EC4B6'   # Teal for price
    
    # Format timestamps for display
    x_data = [ts.strftime('%H:%M') for ts in merged_df['timestamp']]
    
    # Convert numeric data to lists, ensuring each value is a simple number
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    supply_data = safe_list(merged_df['supply'])
    return_data = safe_list(merged_df['return'])
    price_data = safe_list(merged_df['price'])
    
    # Calculate y-axis max values for proper scaling
    max_energy = max(max(supply_data), max(return_data)) * 1.1
    max_price = max(price_data) * 1.1
    
    # Create ECharts options
    options = {
        "backgroundColor": '#f6f4f1',  # Match app background color
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "label": {
                    "backgroundColor": "#6a7985"
                }
            }
            # Custom formatter will be handled by JavaScript in the frontend
        },
        "legend": {
            "data": ["Supply", "Return", "Price"],
            "selected": {
                "Supply": True,
                "Return": True,
                "Price": True
            },
            "icon": "circle",
            "textStyle": {
                "fontSize": 12,
                "color": "#333"
            },
            "itemGap": 20,
            "itemWidth": 10,
            "itemHeight": 10
        },
        "grid": {
            "left": "3%", 
            "right": "4%", 
            "bottom": "15%", 
            "top": "15%", 
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": x_data,
            "axisLabel": {
                "rotate": 30,
                "interval": math.ceil(len(x_data) / 24),  # Show fewer labels when many points
                "fontSize": 11,
                "color": "#666"
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#ccc"
                }
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Energy (kWh)",
                "nameTextStyle": {
                    "fontSize": 12,
                    "color": "#666"
                },
                "min": 0,
                "max": max_energy,
                "axisLabel": {
                    "formatter": "{value} kWh",
                    "fontSize": 11,
                    "color": "#666"
                },
                "splitLine": {
                    "show": False
                }
            },
            {
                "type": "value",
                "name": "Price (€/kWh)",
                "nameTextStyle": {
                    "fontSize": 12,
                    "color": "#666"
                },
                "min": 0,
                "max": max_price,
                "position": "right",
                "axisLabel": {
                    "formatter": "€{value}",
                    "fontSize": 11,
                    "color": "#666"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": "Supply",
                "type": "bar",
                "stack": "energy",
                "itemStyle": {
                    "color": color_supply,
                    "borderRadius": [4, 4, 0, 0]
                },
                "data": supply_data,
                "yAxisIndex": 0
            },
            {
                "name": "Return",
                "type": "bar",
                "stack": "energy",
                "itemStyle": {
                    "color": color_return,
                    "borderRadius": [4, 4, 0, 0]
                },
                "data": return_data,
                "yAxisIndex": 0
            },
            {
                "name": "Price",
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6,
                "lineStyle": {
                    "width": 3, 
                    "color": color_price,
                    "shadowColor": "rgba(0, 0, 0, 0.2)",
                    "shadowBlur": 6
                },
                "itemStyle": {
                    "color": color_price,
                    "borderWidth": 2,
                    "borderColor": "#fff"
                },
                "data": price_data,
                "yAxisIndex": 1
            }
        ],
        "dataZoom": [{
            "type": "slider",
            "show": len(x_data) > 24,
            "height": 20,
            "bottom": 10,
            "start": 0,
            "end": 100,
            "borderColor": "rgba(0,0,0,0)",
            "backgroundColor": "rgba(0,0,0,0.05)",
            "fillerColor": "rgba(67, 97, 238, 0.2)",
            "handleStyle": {
                "color": color_return
            }
        }],
        "toolbox": {
            "feature": {
                "saveAsImage": {
                    "title": "Save as Image",
                    "pixelRatio": 2
                },
                "dataZoom": {},
                "restore": {}
            },
            "right": 15,
            "itemSize": 15,
            "itemGap": 5,
            "iconStyle": {
                "borderWidth": 0,
                "borderColor": "#ccc",
                "color": "#666"
            }
        },
        "animation": True,
        "animationDuration": 1000,
        "animationEasing": "cubicOut"
    }
    
    return options

def savings_bar_plot(daily_costs=None, transaction_history_discharge=None):
    """Create an enhanced visualization of cost savings using ECharts with new data structure"""
    
    # Check if we have the required data
    if daily_costs is None or daily_costs.empty or transaction_history_discharge is None or transaction_history_discharge.empty:
        return {}
    
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
    x_data = [d.strftime('%b %d') for d in merged_data['date']]
    
    # Convert numeric data to lists, ensuring each value is a simple number 
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    current_cost = safe_list(merged_data['cost'])
    final_cost = safe_list(merged_data['final_cost'])
    daily_savings = safe_list(merged_data['saved'])
    
    # Modern colors for 2025 tech aesthetic
    color_current = '#FF6B6B'  # Vibrant coral for current costs
    color_final = '#4361EE'    # Rich blue for final costs
    
    # Calculate savings percentage for each day
    savings_pct = []
    for i in range(len(current_cost)):
        if current_cost[i] > 0:
            pct = round((current_cost[i] - final_cost[i]) / current_cost[i] * 100, 1)
            savings_pct.append(pct)
        else:
            savings_pct.append(0)
    
    # Create the ECharts option structure
    options = {
        "backgroundColor": '#f6f4f1',  # Match app background color
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow",
                "shadowStyle": {
                    "color": "rgba(0, 0, 0, 0.1)"
                }
            },
            "backgroundColor": "rgba(255, 255, 255, 0.9)",
            "borderWidth": 0,
            "textStyle": {
                "color": "#333"
            }
        },
        "legend": {
            "data": ["Current Cost", "With Battery"],
            "selected": {
                "Current Cost": True,
                "With Battery": True
            },
            "icon": "circle",
            "textStyle": {
                "fontSize": 12,
                "color": "#333"
            },
            "itemGap": 20,
            "itemWidth": 10,
            "itemHeight": 10
        },
        "grid": {
            "left": "3%", 
            "right": "4%", 
            "bottom": "15%", 
            "top": "15%", 
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": x_data,
            "axisTick": {"alignWithLabel": True},
            "axisLabel": {
                "rotate": 30,
                "interval": 0,
                "fontSize": 11,
                "color": "#666"
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#ccc"
                }
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Cost (€)",
            "nameTextStyle": {
                "fontSize": 12,
                "color": "#666"
            },
            "axisLabel": {
                "formatter": "€{value}",
                "fontSize": 11,
                "color": "#666"
            },
            "splitLine": {
                "show": False
            }
        },
        "series": [
            {
                "name": "Current Cost",
                "type": "bar",
                "barWidth": "50%",
                "itemStyle": {
                    "color": color_current,
                    "borderRadius": [8, 8, 0, 0]
                },
                "data": current_cost,
                "tooltip": {
                    "formatter": "{b}<br>Original: <b>€{c}</b>"
                }
            },
            {
                "name": "With Battery",
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 8,
                "lineStyle": {
                    "width": 3, 
                    "color": color_final,
                    "shadowColor": "rgba(0, 0, 0, 0.2)",
                    "shadowBlur": 8
                },
                "itemStyle": {
                    "color": color_final,
                    "borderWidth": 2,
                    "borderColor": "#fff"
                },
                "data": final_cost,
                "tooltip": {
                    "formatter": "{b}<br>With Battery: <b>€{c}</b>"
                }
            }
        ],
        "dataZoom": [{
            "type": "slider",
            "show": len(x_data) > 10,
            "height": 20,
            "bottom": 10,
            "start": 0,
            "end": 100,
            "borderColor": "rgba(0,0,0,0)",
            "backgroundColor": "rgba(0,0,0,0.05)",
            "fillerColor": "rgba(67, 97, 238, 0.2)",
            "handleStyle": {
                "color": color_final
            }
        }],
        "toolbox": {
            "feature": {
                "saveAsImage": {
                    "title": "Save as Image",
                    "pixelRatio": 2
                },
                "dataZoom": {},
                "restore": {}
            },
            "right": 15,
            "itemSize": 15,
            "itemGap": 5,
            "iconStyle": {
                "borderWidth": 0,
                "borderColor": "#ccc",
                "color": "#666"
            }
        },
        "animation": True,
        "animationDuration": 1000,
        "animationEasing": "cubicOut"
    }
    
    return options

def create_savings_breakdown_chart(savings):
    """Create a waterfall chart showing the breakdown of savings components"""
    import numpy as np
    
    # Calculate total values
    total_solar_savings = savings['net_savings'].sum()
    total_lost_revenue = savings['lost_revenue'].sum()
    total_net_savings = total_solar_savings - total_lost_revenue
    
    # Format values for display
    def format_value(val):
        return round(float(val), 2)
    
    solar_savings = format_value(total_solar_savings)
    lost_revenue = format_value(total_lost_revenue)
    net_savings = format_value(total_net_savings)
    
    # Modern colors
    color_solar = '#4361EE'    # Blue for solar savings
    color_lost = '#FF6B6B'     # Coral for lost revenue
    color_total = '#38B000'    # Green for total
    
    # Create ECharts options
    options = {
        "backgroundColor": '#f6f4f1',  # Match app background color
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            },
            "formatter": "{b}: <b>€{c}</b>"
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "top": "60px",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": ["Solar Savings", "Lost Revenue", "Net Savings"],
            "axisLabel": {
                "interval": 0,
                "fontSize": 12,
                "color": "#666",
                "rotate": 0
            },
            "splitLine": {
                "show": False  # Remove grid lines
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Amount (€)",
            "nameTextStyle": {
                "fontSize": 12,
                "color": "#666"
            },
            "axisLabel": {
                "formatter": "€{value}",
                "fontSize": 11,
                "color": "#666"
            },
            "splitLine": {
                "show": False  # Remove grid lines
            }
        },
        "series": [
            {
                "name": "Savings",
                "type": "bar",
                "stack": "total",
                "label": {
                    "show": True,
                    "position": "inside",
                    "formatter": "€{c}",
                    "fontSize": 12,
                    "fontWeight": "bold",
                    "color": "#fff"
                },
                "itemStyle": {
                    "borderRadius": [8, 8, 0, 0]  # Curved top corners for positive values
                },
                "data": [
                    {
                        "value": solar_savings,
                        "itemStyle": {
                            "color": color_solar,
                            "borderRadius": [8, 8, 0, 0]  # Curved top corners
                        }
                    },
                    {
                        "value": -lost_revenue,
                        "itemStyle": {
                            "color": color_lost,
                            "borderRadius": [0, 0, 8, 8]  # Curved bottom corners for negative values
                        }
                    },
                    {
                        "value": net_savings,
                        "itemStyle": {
                            "color": color_total,
                            "borderRadius": [8, 8, 0, 0]  # Curved top corners
                        }
                    }
                ]
            }
        ],
        "animationEasing": "elasticOut"
    }
    
    return options

