import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np

def create_plot(usage_df, price_df):
    """Create an interactive plot showing energy flow and prices with clear labeling"""
    fig = go.Figure()

    # Energy Supply (Consumption)
    supply_df = usage_df[usage_df['type'] == 'supply']
    fig.add_trace(go.Scatter(
        x=supply_df['timestamp'],
        y=supply_df['value'],
        name='Energy Used from Grid',
        line=dict(color='#FF6B6B', width=2),  # Coral for grid consumption (matching cost savings chart)
        hovertemplate="%{x|%b %d %H:%M}<br>%{y:.1f} kWh<extra></extra>"
    ))

    # Energy Return (Solar Production)
    return_df = usage_df[usage_df['type'] == 'return']
    fig.add_trace(go.Scatter(
        x=return_df['timestamp'],
        y=return_df['value'],
        name='Solar Energy Produced',
        line=dict(color='#4361EE', width=2),  # Blue for solar (matching cost savings chart)
        hovertemplate="%{x|%b %d %H:%M}<br>%{y:.1f} kWh<extra></extra>"
    ))

    # Electricity Prices (Right Axis)
    fig.add_trace(go.Scatter(
        x=price_df['timestamp'],
        y=price_df['price'],
        name='Electricity Price',
        line=dict(color='#2EC4B6', width=2, dash='dot'),  # Teal for price (matching trend line)
        yaxis='y2',
        hovertemplate="%{x|%b %d %H:%M}<br>€%{y:.3f}/kWh<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="<b>Energy Flow & Electricity Prices</b><br>"
                 "<span style='font-size:0.9em'>Grid consumption vs solar production with market prices</span>",
            x=0.05,
            xanchor='left'
        ),
        xaxis=dict(
            title="Date/Time",
            gridcolor='#F0F0F0',
            showgrid=False
        ),
        yaxis=dict(
            title=dict(text="Energy (kWh)", font=dict(color='#4361EE')),
            gridcolor='#F0F0F0',
            showgrid=False
        ),
        yaxis2=dict(
            title=dict(text="Price (€/kWh)", font=dict(color='#2EC4B6')),
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        hovermode="x unified",
        template="plotly_white",
        margin=dict(t=100),
        plot_bgcolor='#f6f4f1',
        paper_bgcolor='#f6f4f1'
    )
    
    # Add annotation explaining solar production
    fig.add_annotation(
        text="↑ Solar production reduces grid energy needs",
        xref="paper", yref="paper",
        x=0.05, y=0.95,
        showarrow=False,
        font=dict(color='#4361EE', size=10)
    )
    
    return fig


def create_cost_savings_plot(daily_costs, savings):
    """Create an intuitive, modern visualization of potential savings"""
    # Ensure daily_costs and savings are not empty
    if daily_costs.empty or savings.empty:
        return go.Figure()
    
    # Create copies to avoid modifying originals
    daily_costs = daily_costs.copy()
    savings = savings.copy()
    
    # Ensure date/timestamp columns are datetime type
    if 'date' in daily_costs.columns:
        daily_costs['date'] = pd.to_datetime(daily_costs['date'])
    
    if 'timestamp' in savings.columns:
        savings['timestamp'] = pd.to_datetime(savings['timestamp'])
        
        # Create a date column in savings to match daily_costs
        savings['date'] = savings['timestamp'].dt.date
        savings['date'] = pd.to_datetime(savings['date'])
    
    # Merge data frames using the properly converted date columns
    merged_data = pd.merge(
        daily_costs,
        savings,
        on='date',  # Now both have compatible 'date' columns
        how='outer'
    )
    
    # Calculate different cost scenarios
    merged_data['cost_with_solar_only'] = merged_data['cost'] - merged_data['net_savings']
    merged_data['final_cost'] = merged_data['cost_with_solar_only']
    
    fig = go.Figure()

    # Original cost bars
    fig.add_trace(go.Bar(
        x=merged_data['date'],
        y=merged_data['cost'],
        name='Current Cost',
        marker=dict(
            color='#FF6B6B',  # Coral for current costs
            opacity=0.8
        ),
        hovertemplate="<b>Current Cost</b><br>%{x|%b %d}<br>€%{y:.2f}<extra></extra>"
    ))

    # Cost with only solar optimization
    fig.add_trace(go.Scatter(
        x=merged_data['date'],
        y=merged_data['cost_with_solar_only'],
        name='With Solar Storage',
        line=dict(color='#4361EE', width=3, dash='dot'),  # Blue for solar storage
        mode='lines+markers',
        marker=dict(
            symbol='diamond',
            size=8,
            color='#4361EE',
            line=dict(color='white', width=1)
        ),
        hovertemplate="<b>With Solar Storage</b><br>%{x|%b %d}<br>€%{y:.2f}<extra></extra>"
    ))

    fig.update_layout(
        showlegend=True,
        xaxis=dict(
            title=None,
            showgrid=False,
            showline=True,
            linecolor='rgba(0,0,0,0.2)'
        ),
        yaxis=dict(
            title="Daily Cost (€)",
            showgrid=False,
            showline=True,
            linecolor='rgba(0,0,0,0.2)',
            titlefont=dict(size=14)
        ),
        plot_bgcolor='#f6f4f1',
        paper_bgcolor='#f6f4f1',
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        margin=dict(t=40, l=60, r=60, b=40),
        barmode='overlay'
    )

    return fig


def create_cost_savings_plot_v2(daily_costs, savings):
    """Create an enhanced visualization of cost savings using subplots for clarity"""
    # Ensure daily_costs and savings are not empty
    if daily_costs.empty or savings.empty:
        return go.Figure()
    
    # Create copies to avoid modifying originals
    daily_costs = daily_costs.copy()
    savings = savings.copy()
    
    # Ensure date/timestamp columns are datetime type
    if 'date' in daily_costs.columns:
        daily_costs['date'] = pd.to_datetime(daily_costs['date'])
    
    if 'timestamp' in savings.columns:
        savings['timestamp'] = pd.to_datetime(savings['timestamp'])
        
        # Create a date column in savings to match daily_costs
        savings['date'] = savings['timestamp'].dt.date
        savings['date'] = pd.to_datetime(savings['date'])
    
    # Merge data frames using the properly converted date columns
    merged_data = pd.merge(
        daily_costs,
        savings,
        on='date',  # Now both have compatible 'date' columns
        how='outer'
    )
    
    # Calculate different cost scenarios
    merged_data['cost_with_solar_only'] = merged_data['cost'] - merged_data['net_savings']
    merged_data['final_cost'] = merged_data['cost_with_solar_only']
    
    # Calculate daily savings for the waterfall
    merged_data['solar_savings'] = merged_data['net_savings']
    merged_data['lost_revenue'] = merged_data['lost_revenue']
    merged_data['total_savings'] = merged_data['solar_savings'] - merged_data['lost_revenue']
    
    # Create figure with subplots
    fig = make_subplots(
        rows=2, 
        cols=1,
        row_heights=[0.55, 0.45],  # Give more space to bottom plot
        vertical_spacing=0.2,  # Increase spacing between plots
        subplot_titles=("Daily Cost Comparison", "Total Savings Breakdown")
    )

    # Top plot: Daily costs comparison
    fig.add_trace(
        go.Bar(
            x=merged_data['date'],
            y=merged_data['cost'],
            name='Current Cost',
            marker_color='#FF6B6B',  # Coral for current costs
            hovertemplate="<b>Current Cost</b><br>%{x|%b %d}<br>€%{y:.2f}<extra></extra>",
        ),
        row=1, col=1
    )
    
    # Calculate daily savings
    merged_data['daily_savings'] = merged_data['cost'] - merged_data['final_cost']
    
    # Add savings overlay
    fig.add_trace(
        go.Bar(
            x=merged_data['date'],
            y=merged_data['daily_savings'],
            name='Savings with Battery',
            marker_color='#4361EE',  # Blue for savings
            hovertemplate="<b>Daily Savings</b><br>%{x|%b %d}<br>€%{y:.2f}<extra></extra>",
            base=merged_data['final_cost'],  # Start from final cost
        ),
        row=1, col=1
    )

    # Add a line for the final cost
    fig.add_trace(
        go.Scatter(
            x=merged_data['date'],
            y=merged_data['final_cost'],
            name='Final Cost with Battery',
            line=dict(color='#2EC4B6', width=2, dash='dot'),  # Teal for final cost
            hovertemplate="<b>Final Cost</b><br>%{x|%b %d}<br>€%{y:.2f}<extra></extra>",
        ),
        row=1, col=1
    )

    # Bottom plot: Daily savings breakdown
    colors = ['#4361EE', '#FF6B6B']  # Blue, Coral
    savings_data = [
        ('Solar Storage Savings', merged_data['solar_savings'].sum()),
        ('Lost Solar Revenue', -merged_data['lost_revenue'].sum())
    ]
    
    # Create waterfall chart for savings
    fig.add_trace(
        go.Waterfall(
            name="Savings Breakdown",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Solar Storage<br>Savings", "Lost Solar<br>Revenue", "Total<br>Savings"],
            textposition=["inside", "inside", "inside"],
            text=[f"€{val:.2f}" for val in [
                savings_data[0][1],
                savings_data[1][1],
                sum(x[1] for x in savings_data)
            ]],
            y=[
                savings_data[0][1],
                savings_data[1][1],
                0
            ],
            connector={"line": {"color": "#2EC4B6"}},  # Teal for connectors
            decreasing={"marker": {"color": "#FF6B6B"}},  # Coral for negative
            increasing={"marker": {"color": "#4361EE"}},  # Blue for positive
            totals={"marker": {"color": "#38B000"}},      # Green for total savings
            textfont=dict(
                size=12,
                color='white',  # White text for better contrast
                family="Arial"
            ),
            hovertemplate="<b>%{x}</b><br>€%{y:.2f}<extra></extra>"
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text="<b>Battery Storage Cost Analysis</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        showlegend=True,
        plot_bgcolor='#f6f4f1',
        paper_bgcolor='#f6f4f1',
        height=900,
        margin=dict(t=100, l=80, r=80, b=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        barmode='overlay',  # Ensure bars overlay each other
        bargap=0.15        # Gap between bars
    )

    # Update axes and subplot-specific settings
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor='rgba(0,0,0,0.2)',
        row=1, col=1
    )
    fig.update_yaxes(
        title="Daily Cost (€)",
        showgrid=False,
        showline=True,
        linecolor='rgba(0,0,0,0.2)',
        titlefont=dict(size=14),
        row=1, col=1
    )
    fig.update_yaxes(
        title="Savings (€)",
        showgrid=False,
        showline=True,
        linecolor='rgba(0,0,0,0.2)',
        titlefont=dict(size=14),
        row=2, col=1
    )

    # Update the first subplot to use grouped bars
    fig.update_layout({
        'barmode': 'group',
        'bargap': 0.15,
        'bargroupgap': 0.1
    })

    return fig


def create_echarts_cost_savings_plot(daily_costs, savings):
    """Create an enhanced visualization of cost savings using ECharts"""
    import json
    import numpy as np
    
    # Ensure daily_costs and savings are not empty
    if daily_costs.empty or savings.empty:
        return {}
    
    # Create copies to avoid modifying originals
    daily_costs = daily_costs.copy()
    savings = savings.copy()
    
    # Ensure date/timestamp columns are datetime type
    if 'date' in daily_costs.columns:
        daily_costs['date'] = pd.to_datetime(daily_costs['date'])
    
    if 'timestamp' in savings.columns:
        savings['timestamp'] = pd.to_datetime(savings['timestamp'])
        
        # Create a date column in savings to match daily_costs
        savings['date'] = savings['timestamp'].dt.date
        savings['date'] = pd.to_datetime(savings['date'])
    
    # Merge data frames using the properly converted date columns
    merged_data = pd.merge(
        daily_costs,
        savings,
        on='date',  # Now both have compatible 'date' columns
        how='outer'
    )
    
    # Drop rows with NaN values to ensure clean data
    merged_data = merged_data.dropna(subset=['cost', 'net_savings'])
    
    # Calculate different cost scenarios
    merged_data['cost_with_solar_only'] = merged_data['cost'] - merged_data['net_savings']
    merged_data['final_cost'] = merged_data['cost_with_solar_only']
    
    # Calculate 7-day moving average of daily savings
    window_size = min(7, len(merged_data))
    if window_size > 0:
        merged_data['savings_ma'] = merged_data['net_savings'].rolling(window=window_size, min_periods=1).mean()
    else:
        merged_data['savings_ma'] = merged_data['net_savings']
    
    # Format dates for display
    x_data = [d.strftime('%b %d') for d in merged_data['date']]
    
    # Convert numeric data to lists, ensuring each value is a simple number 
    # with no NaN or special formats that would break JSON
    def safe_list(series):
        return [round(float(x), 2) if pd.notna(x) else 0 for x in series]
    
    current_cost = safe_list(merged_data['cost'])
    final_cost = safe_list(merged_data['final_cost'])
    daily_savings = safe_list(merged_data['net_savings'])
    savings_trend = safe_list(merged_data['savings_ma'])
    
    # Modern colors for 2025 tech aesthetic
    color_current = '#FF6B6B'  # Vibrant coral for current costs
    color_final = '#4361EE'    # Rich blue for final costs
    color_trend = '#2EC4B6'    # Modern teal for trend line
    
    # Calculate savings percentage for each day
    savings_pct = []
    for i in range(len(current_cost)):
        if current_cost[i] > 0:
            pct = round((current_cost[i] - final_cost[i]) / current_cost[i] * 100, 1)
            savings_pct.append(pct)
        else:
            savings_pct.append(0)
    
    # Create the basic ECharts option structure with minimal complexity
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
            "data": ["Current Cost", "Final Cost", "Savings Trend"],
            "selected": {
                "Current Cost": True,
                "Final Cost": True,
                "Savings Trend": True
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
                "show": False  # Remove grid lines
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
                "show": False  # Remove grid lines
            }
        },
        "series": [
            {
                "name": "Current Cost",
                "type": "bar",
                "barWidth": "50%",
                "itemStyle": {
                    "color": color_current,
                    "borderRadius": [8, 8, 0, 0]  # Curved top corners
                },
                "data": current_cost,
                "tooltip": {
                    "formatter": "{b}<br>Original: <b>€{c}</b>"
                }
            },
            {
                "name": "Final Cost",
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
            },
            {
                "name": "Savings",
                "type": "bar",
                "stack": "savings",
                "barGap": "-100%",  # Overlay on the current cost bars
                "itemStyle": {
                    "color": "transparent",  # Make the bar invisible
                    "borderWidth": 0
                },
                "emphasis": {
                    "itemStyle": {
                        "color": "transparent"  # Keep invisible on hover
                    }
                },
                "data": current_cost,
                "tooltip": {
                    "formatter": "{b}<br>Savings: <b>€{c}</b>"
                }
            },
            {
                "name": "Savings Trend",
                "type": "line",
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 3, 
                    "color": color_trend
                },
                "itemStyle": {
                    "color": color_trend
                },
                "data": savings_trend,
                "tooltip": {
                    "formatter": "{b}<br>Avg Savings: <b>€{c}</b>"
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

def create_battery_level_plot(energy_flows_df, battery_capacity):
    """
    Create a plot showing battery level over time.
    
    Args:
        energy_flows_df: DataFrame with energy flow data including battery_level
        battery_capacity: The maximum capacity of the battery in kWh
        
    Returns:
        A plotly figure object showing battery level over time
    """
    if energy_flows_df is None or energy_flows_df.empty or 'battery_level' not in energy_flows_df.columns:
        # Return empty figure if no data
        return go.Figure().update_layout(
            title="No battery level data available",
            xaxis_title="Time",
            yaxis_title="Battery Level (kWh)",
            height=400
        )
    
    # Make a copy to avoid modifying the original
    df = energy_flows_df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Add title with key information
    total_solar_to_grid = df['solar_to_grid'].sum()
    total_solar_to_battery = df['solar_to_battery'].sum()
    title = f"Battery Level Over Time (Hourly)"
    
    # Count occurrences of each limitation type
    if 'charge_limited_by' in df.columns:
        limited_by_space = (df['charge_limited_by'] == 'battery_space').sum()
        limited_by_rate = (df['charge_limited_by'] == 'charging_rate').sum()
        limited_by_taper = (df['charge_limited_by'] == 'taper').sum()
        
        limitations = []
        if limited_by_space > 0:
            limitations.append(f"Battery full ({limited_by_space} intervals)")
        if limited_by_rate > 0:
            limitations.append(f"Max charge rate ({limited_by_rate} intervals)")
        if limited_by_taper > 0:
            limitations.append(f"Charge tapering ({limited_by_taper} intervals)")
            
        if limitations:
            title += f"<br><span style='font-size:12px'>Solar to grid due to: {', '.join(limitations)}</span>"
    
    # Add charge rate info if available (from the first day's metrics)
    if 'date' in df.columns and len(df) > 0:
        first_date = df['date'].iloc[0]
        first_date_transactions = df[df['date'] == first_date]
        if len(first_date_transactions) > 0 and 'charge_rate_info' in first_date_transactions.iloc[0]:
            charging_info = first_date_transactions.iloc[0]['charge_rate_info']
            title += f"<br><span style='font-size:12px'>{charging_info}</span>"
    
    # Resample to hourly if data is more granular
    # We'll use the mean battery level for each hour
    df['hour'] = df['timestamp'].dt.floor('h')  # Use lowercase 'h' as 'H' is deprecated
    
    # Check which columns exist and create agg dict accordingly
    agg_dict = {'battery_level': 'mean'}
    
    # Add optional columns if they exist
    for col in ['solar_energy_in_battery', 'grid_energy_in_battery', 'solar_to_grid', 'solar_to_battery']:
        if col in df.columns:
            agg_dict[col] = 'mean' if 'energy_in_battery' in col else 'sum'
    
    # If energy composition columns don't exist, add them with default values
    if 'solar_energy_in_battery' not in df.columns:
        df['solar_energy_in_battery'] = df['battery_level']  # Assume all energy is from solar
    
    if 'grid_energy_in_battery' not in df.columns:
        df['grid_energy_in_battery'] = 0.0  # Assume no grid energy in battery
        
    # Update the aggregation dict to include these columns
    if 'solar_energy_in_battery' not in agg_dict:
        agg_dict['solar_energy_in_battery'] = 'mean'
    if 'grid_energy_in_battery' not in agg_dict:
        agg_dict['grid_energy_in_battery'] = 'mean'
    
    # Aggregate the data
    hourly_data = df.groupby('hour').agg(agg_dict).reset_index()
    
    # Calculate percentage of capacity
    hourly_data['battery_pct'] = (hourly_data['battery_level'] / battery_capacity) * 100
    
    # Fix: Filter out insignificant grid energy amounts - likely rounding errors
    # Only show grid energy if it's more than 1% of the battery level
    grid_threshold = 0.01
    has_significant_grid_energy = False
    
    # Safely check for significant grid energy
    valid_rows = hourly_data[hourly_data['battery_level'] > 0]
    if not valid_rows.empty:
        has_significant_grid_energy = (valid_rows['grid_energy_in_battery'] / valid_rows['battery_level'] > grid_threshold).any()
    
    if not has_significant_grid_energy:
        # If no significant grid energy, set it to zero and make solar = battery level
        hourly_data['grid_energy_in_battery'] = 0
        hourly_data['solar_energy_in_battery'] = hourly_data['battery_level']
    
    # Calculate percentage of battery that is from solar vs grid
    hourly_data['solar_pct'] = (hourly_data['solar_energy_in_battery'] / hourly_data['battery_level']) * 100
    hourly_data['solar_pct'] = hourly_data['solar_pct'].fillna(0).clip(0, 100)
    hourly_data['grid_pct'] = 100 - hourly_data['solar_pct']
    
    # Create the figure
    fig = go.Figure()
    
    # Add solar to grid as bar chart on secondary y-axis
    if hourly_data['solar_to_grid'].sum() > 0:
        fig.add_trace(go.Bar(
            x=hourly_data['hour'],
            y=hourly_data['solar_to_grid'],
            name='Solar to Grid',
            marker_color='rgba(255, 153, 51, 0.7)',  # Orange
            yaxis='y2',
            hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Solar to Grid: %{y:.2f} kWh<extra></extra>'
        ))
    
    # Add battery level line
    fig.add_trace(go.Scatter(
        x=hourly_data['hour'],
        y=hourly_data['battery_level'],
        name='Battery Level (kWh)',
        line=dict(color='#4361EE', width=3),
        hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Battery Level: %{y:.2f} kWh<br>(%{customdata[0]:.1f}% of capacity)<extra></extra>',
        customdata=np.column_stack((hourly_data['battery_pct'],))
    ))
    
    # Add solar energy component area
    fig.add_trace(go.Scatter(
        x=hourly_data['hour'],
        y=hourly_data['solar_energy_in_battery'],
        name='Solar Energy in Battery',
        fill='tozeroy',
        mode='none',
        fillcolor='rgba(255, 215, 0, 0.3)',  # Golden yellow with transparency
        hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Solar Energy: %{y:.2f} kWh<br>(%{customdata[0]:.1f}% of battery)<extra></extra>',
        customdata=np.column_stack((hourly_data['solar_pct'],))
    ))
    
    # Only add grid energy trace if there's significant grid energy
    if has_significant_grid_energy:
        # Add grid energy component area
        fig.add_trace(go.Scatter(
            x=hourly_data['hour'],
            y=hourly_data['grid_energy_in_battery'],
            name='Grid Energy in Battery',
            fill='tonexty',
            mode='none',
            fillcolor='rgba(100, 149, 237, 0.3)',  # Cornflower blue with transparency
            hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Grid Energy: %{y:.2f} kWh<br>(%{customdata[0]:.1f}% of battery)<extra></extra>',
            customdata=np.column_stack((hourly_data['grid_pct'],))
        ))
    
    # Add a reference line for battery capacity
    fig.add_shape(
        type="line",
        x0=hourly_data['hour'].min(),
        y0=battery_capacity,
        x1=hourly_data['hour'].max(),
        y1=battery_capacity,
        line=dict(
            color="rgba(255, 0, 0, 0.5)",
            width=2,
            dash="dash",
        )
    )
    
    # Add annotation for battery capacity
    fig.add_annotation(
        x=hourly_data['hour'].max(),
        y=battery_capacity,
        text=f"Capacity: {battery_capacity} kWh",
        showarrow=False,
        yshift=10,
        xshift=-5,
        align="right",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.1)",
        font=dict(size=10)
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            y=0.95,
            yanchor='top',
            font=dict(size=14)
        ),
        xaxis_title="Time",
        yaxis_title="Energy (kWh)",
        yaxis2=dict(
            title="Solar to Grid (kWh)",
            overlaying="y",
            side="right"
        ),
        legend_title="Legend",
        hovermode="x unified",
        height=500,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,  # Move legend below the plot
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.1)",
            borderwidth=1
        ),
        margin=dict(t=120, l=60, r=60, b=80)  # Increased margins for better spacing
    )
    
    return fig

def create_battery_discharge_savings_plot(energy_flows_df):
    """
    Create a plot showing battery discharge events and the associated cost savings.
    
    Args:
        energy_flows_df: DataFrame with energy flow data including battery_to_house and price
        
    Returns:
        A plotly figure object showing discharge events and savings over time
    """
    if energy_flows_df is None or energy_flows_df.empty or 'battery_to_house' not in energy_flows_df.columns:
        # Return empty figure if no data
        return go.Figure().update_layout(
            title="No battery discharge data available",
            xaxis_title="Time",
            yaxis_title="Discharge (kWh) / Savings (€)",
            height=300
        )
    
    # Make a copy to avoid modifying the original
    df = energy_flows_df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Filter to only include intervals where battery was discharged to house
    df = df[df['battery_to_house'] > 0]
    
    if df.empty:
        return go.Figure().update_layout(
            title="No battery discharge events found",
            xaxis_title="Time",
            yaxis_title="Discharge (kWh) / Savings (€)",
            height=300
        )
    
    # Calculate savings for each discharge event
    df['discharge_savings'] = df['battery_to_house'] * df['price']
    
    # Resample to hourly if data is more granular
    df['hour'] = df['timestamp'].dt.floor('h')
    
    # Aggregate the data
    hourly_data = df.groupby('hour').agg({
        'battery_to_house': 'sum',
        'discharge_savings': 'sum',
        'price': 'mean'
    }).reset_index()
    
    # Create the figure
    fig = go.Figure()
    
    # Add discharge amount as bars
    fig.add_trace(go.Bar(
        x=hourly_data['hour'],
        y=hourly_data['battery_to_house'],
        name='Discharge Amount (kWh)',
        marker_color='#4CC9F0',  # Light blue
        hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Discharge: %{y:.2f} kWh<br>Avg Price: €%{customdata[0]:.4f}/kWh<extra></extra>',
        customdata=np.column_stack((hourly_data['price'],))
    ))
    
    # Add savings as line on secondary y-axis
    fig.add_trace(go.Scatter(
        x=hourly_data['hour'],
        y=hourly_data['discharge_savings'],
        name='Cost Savings (€)',
        mode='lines+markers',
        line=dict(color='#F72585', width=2),  # Pink/purple
        marker=dict(size=6),
        yaxis='y2',
        hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Savings: €%{y:.2f}<extra></extra>'
    ))
    
    # Calculate cumulative savings
    hourly_data['cumulative_savings'] = hourly_data['discharge_savings'].cumsum()
    
    # Add cumulative savings as a line
    fig.add_trace(go.Scatter(
        x=hourly_data['hour'],
        y=hourly_data['cumulative_savings'],
        name='Cumulative Savings (€)',
        mode='lines',
        line=dict(color='#7209B7', width=2, dash='dot'),  # Purple
        yaxis='y2',
        hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>Total Savings: €%{y:.2f}<extra></extra>'
    ))
    
    # Calculate total savings
    total_savings = hourly_data['discharge_savings'].sum()
    total_discharge = hourly_data['battery_to_house'].sum()
    title = f"Battery Discharge Savings: €{total_savings:.2f} from {total_discharge:.1f} kWh"
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            y=0.95,
            yanchor='top',
            font=dict(size=14)
        ),
        xaxis_title="Time",
        yaxis_title="Discharge (kWh)",
        yaxis2=dict(
            title="Savings (€)",
            overlaying="y",
            side="right",
            rangemode="tozero"
        ),
        legend_title="Legend",
        hovermode="x unified",
        height=400,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,  # Move legend below the plot
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.1)",
            borderwidth=1
        ),
        margin=dict(t=80, l=60, r=60, b=80)  # Margins for better spacing
    )
    
    return fig