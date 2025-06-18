import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional

def make_chart(data: List[dict] = None, analysis_result: Dict = None, type: str = "line", title: str = "Chart", **kwargs) -> Dict:
    """
    Enhanced chart generator supporting multiple visualization types and data sources
    
    Args:
        data: Direct transaction data (legacy support)
        analysis_result: Result from analyze_data executor
        type: Chart type (line, bar, pie, scatter, area, waterfall, table, etc.)
        title: Chart title
        **kwargs: Chart-specific parameters
    """
    
    # Handle data source - prefer analysis_result over raw data
    if analysis_result and "data" in analysis_result:
        chart_data = analysis_result["data"]
        summary = analysis_result.get("summary", {})
    elif data:
        # Legacy support - convert transactions to simple chart data
        df = pd.DataFrame(data)
        if not df.empty:
            df["balance"] = df["amount"].cumsum()
            chart_data = df.to_dict('records')
            summary = {"total_transactions": len(data)}
        else:
            chart_data = []
            summary = {}
    else:
        chart_data = []
        summary = {}
    
    if not chart_data:
        return {
            "chart_spec": _create_empty_chart(title).to_json(),
            "citations": [],
            "summary": {"error": "No data available for charting"}
        }
    
    try:
        # Generate chart based on type
        if type == "line":
            fig = _create_line_chart(chart_data, title, **kwargs)
        elif type == "bar":
            fig = _create_bar_chart(chart_data, title, **kwargs)
        elif type == "pie":
            fig = _create_pie_chart(chart_data, title, **kwargs)
        elif type == "scatter":
            fig = _create_scatter_chart(chart_data, title, **kwargs)
        elif type == "area":
            fig = _create_area_chart(chart_data, title, **kwargs)
        elif type == "waterfall":
            fig = _create_waterfall_chart(chart_data, title, **kwargs)
        elif type == "treemap":
            fig = _create_treemap_chart(chart_data, title, **kwargs)
        elif type == "heatmap":
            fig = _create_heatmap_chart(chart_data, title, **kwargs)
        elif type == "table":
            fig = _create_table_chart(chart_data, title, **kwargs)
        elif type == "gauge":
            fig = _create_gauge_chart(chart_data, title, **kwargs)
        else:
            fig = _create_bar_chart(chart_data, title, **kwargs)  # Default fallback
        
        # Extract citations from data
        citations = _extract_citations(chart_data, data)
        
        return {
            "chart_spec": fig.to_json(),
            "citations": citations,
            "summary": summary
        }
        
    except Exception as e:
        # Fallback to simple chart on error
        return {
            "chart_spec": _create_error_chart(title, str(e)).to_json(),
            "citations": [],
            "summary": {"error": f"Chart generation error: {str(e)}"}
        }

def _create_line_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create line chart for trends over time"""
    
    df = pd.DataFrame(data)
    
    # Determine x and y axes
    x_axis = kwargs.get("x_axis", _auto_detect_x_axis(df))
    y_axis = kwargs.get("y_axis", _auto_detect_y_axis(df))
    series = kwargs.get("series", [y_axis])
    
    fig = go.Figure()
    
    if isinstance(series, list) and len(series) > 1:
        # Multi-series line chart
        for serie in series:
            if serie in df.columns:
                fig.add_trace(go.Scatter(
                    x=df[x_axis],
                    y=df[serie],
                    mode='lines+markers',
                    name=serie.title(),
                    line=dict(width=3)
                ))
    else:
        # Single series
        y_col = series[0] if isinstance(series, list) else y_axis
        fig.add_trace(go.Scatter(
            x=df[x_axis],
            y=df[y_col],
            mode='lines+markers',
            name=y_col.title(),
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_axis.replace('_', ' ').title(),
        yaxis_title=y_axis.replace('_', ' ').title(),
        hovermode='x unified'
    )
    
    return fig

def _create_bar_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create bar chart for categorical comparisons"""
    
    df = pd.DataFrame(data)
    
    x_axis = kwargs.get("x_axis", _auto_detect_x_axis(df))
    y_axis = kwargs.get("y_axis", _auto_detect_y_axis(df))
    
    # Sort by y_axis for better visualization
    if y_axis in df.columns:
        df = df.sort_values(y_axis, ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df[x_axis],
        y=df[y_axis],
        text=df[y_axis],
        textposition='auto',
        marker_color='rgba(55, 128, 191, 0.7)',
        marker_line=dict(color='rgba(55, 128, 191, 1.0)', width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_axis.replace('_', ' ').title(),
        yaxis_title=y_axis.replace('_', ' ').title(),
        xaxis_tickangle=-45
    )
    
    return fig

def _create_pie_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create pie chart for proportional data"""
    
    df = pd.DataFrame(data)
    
    labels = kwargs.get("labels", _auto_detect_x_axis(df))
    values = kwargs.get("values", _auto_detect_y_axis(df))
    
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=df[labels],
        values=df[values],
        hole=0.3,  # Donut chart
        textinfo='label+percent',
        textposition='outside'
    ))
    
    fig.update_layout(title=title)
    
    return fig

def _create_scatter_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create scatter plot for correlation analysis"""
    
    df = pd.DataFrame(data)
    
    x_axis = kwargs.get("x_axis", _auto_detect_x_axis(df))
    y_axis = kwargs.get("y_axis", _auto_detect_y_axis(df))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_axis],
        y=df[y_axis],
        mode='markers',
        marker=dict(
            size=10,
            color=df[y_axis] if y_axis in df.columns else 'blue',
            colorscale='Viridis',
            showscale=True
        ),
        text=df[x_axis],
        hovertemplate=f'{x_axis}: %{{x}}<br>{y_axis}: %{{y}}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_axis.replace('_', ' ').title(),
        yaxis_title=y_axis.replace('_', ' ').title()
    )
    
    return fig

def _create_area_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create area chart for cumulative trends"""
    
    df = pd.DataFrame(data)
    
    x_axis = kwargs.get("x_axis", _auto_detect_x_axis(df))
    y_axis = kwargs.get("y_axis", _auto_detect_y_axis(df))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_axis],
        y=df[y_axis],
        fill='tonexty',
        mode='lines',
        name=y_axis.title(),
        line=dict(color='rgba(55, 128, 191, 0.8)')
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_axis.replace('_', ' ').title(),
        yaxis_title=y_axis.replace('_', ' ').title()
    )
    
    return fig

def _create_waterfall_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create waterfall chart for financial flows"""
    
    df = pd.DataFrame(data)
    
    x_axis = kwargs.get("x_axis", _auto_detect_x_axis(df))
    y_axis = kwargs.get("y_axis", _auto_detect_y_axis(df))
    
    fig = go.Figure()
    
    # Determine measure types
    measures = ["relative"] * len(df)
    if len(df) > 0:
        measures[0] = "absolute"  # First item is absolute
        measures[-1] = "total"   # Last item is total
    
    fig.add_trace(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=measures,
        x=df[x_axis],
        y=df[y_axis],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(title=title)
    
    return fig

def _create_treemap_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create treemap for hierarchical data"""
    
    df = pd.DataFrame(data)
    
    labels = kwargs.get("labels", _auto_detect_x_axis(df))
    values = kwargs.get("values", _auto_detect_y_axis(df))
    
    fig = go.Figure()
    
    fig.add_trace(go.Treemap(
        labels=df[labels],
        values=df[values],
        parents=[""] * len(df),  # All top-level
        textinfo="label+value+percent parent"
    ))
    
    fig.update_layout(title=title)
    
    return fig

def _create_heatmap_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create heatmap for correlation matrix"""
    
    df = pd.DataFrame(data)
    
    # Select numeric columns for correlation
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        
        fig = go.Figure()
        
        fig.add_trace(go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(title=title)
    else:
        # Fallback to simple heatmap
        fig = _create_bar_chart(data, title, **kwargs)
    
    return fig

def _create_table_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create data table for detailed view"""
    
    df = pd.DataFrame(data)
    
    columns = kwargs.get("columns", df.columns.tolist())
    
    # Format numeric columns
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            df[col] = df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
    
    fig = go.Figure()
    
    fig.add_trace(go.Table(
        header=dict(
            values=[col.replace('_', ' ').title() for col in columns],
            fill_color='paleturquoise',
            align='left',
            font=dict(size=12, color='black')
        ),
        cells=dict(
            values=[df[col] for col in columns],
            fill_color='lavender',
            align='left',
            font=dict(size=11, color='black')
        )
    ))
    
    fig.update_layout(title=title)
    
    return fig

def _create_gauge_chart(data: List[dict], title: str, **kwargs) -> go.Figure:
    """Create gauge chart for KPI display"""
    
    # Use first numeric value as gauge value
    df = pd.DataFrame(data)
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    if len(numeric_cols) > 0:
        value = df[numeric_cols[0]].iloc[0] if len(df) > 0 else 0
        max_val = df[numeric_cols[0]].max() * 1.2  # 20% buffer
    else:
        value = 0
        max_val = 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [None, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_val*0.5], 'color': "lightgray"},
                {'range': [max_val*0.5, max_val*0.8], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_val*0.9
            }
        }
    ))
    
    return fig

def _create_empty_chart(title: str) -> go.Figure:
    """Create empty chart placeholder"""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available",
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False, font=dict(size=20)
    )
    fig.update_layout(title=title)
    return fig

def _create_error_chart(title: str, error: str) -> go.Figure:
    """Create error chart with message"""
    fig = go.Figure()
    fig.add_annotation(
        text=f"Chart Error: {error}",
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False, font=dict(size=16, color="red")
    )
    fig.update_layout(title=title)
    return fig

def _auto_detect_x_axis(df: pd.DataFrame) -> str:
    """Auto-detect appropriate x-axis column"""
    # Prefer date/time columns
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower() or 'month' in col.lower() or 'period' in col.lower()]
    if date_cols:
        return date_cols[0]
    
    # Then categorical columns
    categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
    if categorical_cols:
        return categorical_cols[0]
    
    # Fallback to first column
    return df.columns[0] if len(df.columns) > 0 else 'x'

def _auto_detect_y_axis(df: pd.DataFrame) -> str:
    """Auto-detect appropriate y-axis column"""
    # Prefer amount/value columns
    amount_cols = [col for col in df.columns if any(word in col.lower() for word in ['amount', 'value', 'total', 'revenue', 'expense', 'cost', 'profit', 'balance'])]
    if amount_cols:
        return amount_cols[0]
    
    # Then any numeric column
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        return numeric_cols[0]
    
    # Fallback to second column or first
    return df.columns[1] if len(df.columns) > 1 else df.columns[0]

def _extract_citations(chart_data: List[dict], original_data: List[dict] = None) -> List[str]:
    """Extract data source citations"""
    citations = []
    
    # From chart data
    for item in chart_data[:5]:  # Limit to first 5 for brevity
        if 'id' in item:
            citations.append(item['id'])
        elif 'name' in item:
            citations.append(item['name'])
    
    # From original transaction data
    if original_data:
        for item in original_data[:3]:
            if 'id' in item and item['id'] not in citations:
                citations.append(item['id'])
    
    return citations[:10]  # Limit total citations