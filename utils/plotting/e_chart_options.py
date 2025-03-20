import math

def get_price_flow_options(x_data, supply_data, return_data, price_data):
    """
    Generate ECharts options for price flow plot
    """
    # Modern colors for 2025 tech aesthetic
    color_supply = '#FF6B6B'  # Coral for grid consumption
    color_return = '#4361EE'  # Blue for solar production
    color_price = '#2EC4B6'   # Teal for price
    
    # Calculate y-axis max values for proper scaling and round them to integers
    max_energy = math.ceil(max(max(supply_data), max(return_data)) * 1.1)
    max_price = math.ceil(max(price_data) * 1.1 * 100) / 100  # Round to 2 decimal places
    
    # Calculate nice intervals for the y-axes
    energy_interval = max(1, math.ceil(max_energy / 5))  # At least 1 kWh
    price_interval = max(0.01, round(max_price / 5, 2))  # At least 0.01 €/kWh
    
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
                "interval": energy_interval,
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
                "interval": price_interval,
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
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6,
                "lineStyle": {
                    "width": 3, 
                    "color": color_supply,
                    "shadowColor": "rgba(0, 0, 0, 0.2)",
                    "shadowBlur": 6
                },
                "itemStyle": {
                    "color": color_supply,
                    "borderWidth": 2,
                    "borderColor": "#fff"
                },
                "data": supply_data,
                "yAxisIndex": 0
            },
            {
                "name": "Return",
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6,
                "lineStyle": {
                    "width": 3, 
                    "color": color_return,
                    "shadowColor": "rgba(0, 0, 0, 0.2)",
                    "shadowBlur": 6
                },
                "itemStyle": {
                    "color": color_return,
                    "borderWidth": 2,
                    "borderColor": "#fff"
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

def get_savings_bar_options(x_data, current_cost, final_cost):
    """
    Generate ECharts options for savings bar plot
    """
    # Modern colors for 2025 tech aesthetic
    color_current = '#FF6B6B'  # Vibrant coral for current costs
    color_final = '#4361EE'    # Rich blue for final costs
    
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
