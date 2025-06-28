"""
FinWave Chart Helpers

Generates branded matplotlib charts for PDF reports
"""

import base64
import io
import logging
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

# FinWave Brand Colors
COLORS = {
    'primary': '#1E2A38',      # Deep Navy
    'secondary': '#2DB3A6',    # Ocean Teal
    'accent': '#5B5BF2',       # Electric Indigo
    'grid': '#E5E7EB',         # Light Gray
    'text': '#374151',         # Dark Gray
    'background': '#FFFFFF',   # White
    'negative': '#EF4444',     # Red
    'positive': '#10B981'      # Green
}

# Font configuration
FONT_CONFIG = {
    'title': {'family': 'Space Grotesk', 'size': 14, 'weight': 'bold'},
    'label': {'family': 'Inter', 'size': 10, 'weight': 'normal'},
    'tick': {'family': 'Inter', 'size': 9, 'weight': 'normal'},
    'legend': {'family': 'Inter', 'size': 9, 'weight': 'normal'}
}


def set_chart_style():
    """Configure matplotlib with FinWave styling"""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Update RC params
    plt.rcParams['figure.facecolor'] = COLORS['background']
    plt.rcParams['axes.facecolor'] = COLORS['background']
    plt.rcParams['axes.edgecolor'] = COLORS['grid']
    plt.rcParams['axes.labelcolor'] = COLORS['text']
    plt.rcParams['text.color'] = COLORS['text']
    plt.rcParams['xtick.color'] = COLORS['text']
    plt.rcParams['ytick.color'] = COLORS['text']
    plt.rcParams['grid.color'] = COLORS['grid']
    plt.rcParams['grid.linestyle'] = '-'
    plt.rcParams['grid.linewidth'] = 0.5
    plt.rcParams['grid.alpha'] = 0.3
    
    # Font settings (fallback if custom fonts not available)
    try:
        plt.rcParams['font.family'] = ['Inter', 'sans-serif']
        plt.rcParams['font.size'] = 10
    except:
        plt.rcParams['font.family'] = 'sans-serif'


def render_line_chart(data: Dict[str, Any], palette_key: str = 'secondary') -> str:
    """
    Render a line chart with FinWave branding
    
    Args:
        data: Dictionary with 'labels', 'values', 'title', 'y_label'
        palette_key: Color key from COLORS dict
        
    Returns:
        Base64 encoded PNG image
    """
    set_chart_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data
    labels = data.get('labels', [])
    values = data.get('values', [])
    title = data.get('title', 'Chart')
    y_label = data.get('y_label', 'Value')
    
    # Plot line
    ax.plot(labels, values, 
           color=COLORS[palette_key], 
           linewidth=2.5,
           marker='o',
           markersize=6,
           markerfacecolor=COLORS['background'],
           markeredgecolor=COLORS[palette_key],
           markeredgewidth=2)
    
    # Fill area under curve
    ax.fill_between(range(len(labels)), values, alpha=0.1, color=COLORS[palette_key])
    
    # Styling
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLORS['primary'])
    ax.set_ylabel(y_label, fontsize=11, color=COLORS['text'])
    ax.set_xlabel('')
    
    # Format y-axis
    if y_label.startswith('Revenue') or y_label.startswith('Cash'):
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M'))
    
    # Rotate x labels if many
    if len(labels) > 6:
        plt.xticks(rotation=45, ha='right')
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(COLORS['grid'])
    ax.spines['bottom'].set_color(COLORS['grid'])
    
    # Adjust layout
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()
    
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{image_base64}"


def render_area_chart(data: Dict[str, Any], palette_key: str = 'accent') -> str:
    """
    Render an area chart (e.g., cash runway projection)
    
    Args:
        data: Dictionary with 'labels', 'values', 'title', 'y_label'
        palette_key: Color key from COLORS dict
        
    Returns:
        Base64 encoded PNG image
    """
    set_chart_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data
    labels = data.get('labels', [])
    values = data.get('values', [])
    title = data.get('title', 'Chart')
    y_label = data.get('y_label', 'Value')
    
    # Plot area
    ax.fill_between(range(len(labels)), values, 
                   alpha=0.6, 
                   color=COLORS[palette_key],
                   edgecolor=COLORS[palette_key],
                   linewidth=2)
    
    # Add line on top
    ax.plot(labels, values, 
           color=COLORS[palette_key], 
           linewidth=2.5)
    
    # Add zero line if cash goes negative
    if min(values) < 0:
        ax.axhline(y=0, color=COLORS['negative'], linestyle='--', alpha=0.5, linewidth=1)
    
    # Styling
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLORS['primary'])
    ax.set_ylabel(y_label, fontsize=11, color=COLORS['text'])
    ax.set_xlabel('')
    
    # Format y-axis
    if 'Cash' in y_label:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M'))
    
    # Rotate x labels
    plt.xticks(rotation=45, ha='right')
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()
    
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{image_base64}"


def render_bar_chart(data: Dict[str, Any], palette_key: str = 'secondary') -> str:
    """
    Render a bar chart with positive/negative coloring
    
    Args:
        data: Dictionary with 'labels', 'values', 'title', 'y_label'
        palette_key: Color key from COLORS dict
        
    Returns:
        Base64 encoded PNG image
    """
    set_chart_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data
    labels = data.get('labels', [])
    values = data.get('values', [])
    title = data.get('title', 'Chart')
    y_label = data.get('y_label', 'Value')
    
    # Determine colors based on positive/negative
    colors = [COLORS['positive'] if v >= 0 else COLORS['negative'] for v in values]
    
    # Create bars
    bars = ax.bar(range(len(labels)), values, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        label_y = height + (max(values) * 0.01 if height > 0 else min(values) * 0.01)
        ax.text(bar.get_x() + bar.get_width()/2., label_y,
                f'{value:,.0f}',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=9, color=COLORS['text'])
    
    # Styling
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLORS['primary'])
    ax.set_ylabel(y_label, fontsize=11, color=COLORS['text'])
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45 if len(labels) > 6 else 0, ha='right' if len(labels) > 6 else 'center')
    
    # Add zero line
    ax.axhline(y=0, color=COLORS['text'], linestyle='-', alpha=0.3, linewidth=0.5)
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()
    
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{image_base64}"


def render_waterfall_chart(data: Dict[str, Any]) -> str:
    """
    Render a waterfall chart for variance analysis
    
    Args:
        data: Dictionary with 'categories', 'values', 'title'
        
    Returns:
        Base64 encoded PNG image
    """
    set_chart_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data
    categories = data.get('categories', [])
    values = data.get('values', [])
    title = data.get('title', 'Variance Analysis')
    
    # Calculate cumulative values
    cumulative = np.cumsum(values)
    
    # Create waterfall
    for i, (cat, val, cum) in enumerate(zip(categories, values, cumulative)):
        # Determine bar properties
        if i == 0:  # Starting value
            bottom = 0
            height = val
            color = COLORS['primary']
        elif i == len(categories) - 1:  # Ending value
            bottom = 0
            height = cum
            color = COLORS['primary']
        else:  # Changes
            bottom = cumulative[i-1] if val > 0 else cum
            height = abs(val)
            color = COLORS['positive'] if val > 0 else COLORS['negative']
        
        # Draw bar
        bar = ax.bar(i, height, bottom=bottom, color=color, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Add connector lines
        if 0 < i < len(categories) - 1:
            ax.plot([i-0.4, i+0.4], [cumulative[i-1], cumulative[i-1]], 'k--', alpha=0.5, linewidth=1)
        
        # Add value labels
        label_y = bottom + height/2
        ax.text(i, label_y, f'{val:+,.0f}' if i > 0 and i < len(categories)-1 else f'{val:,.0f}',
                ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    
    # Styling
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLORS['primary'])
    ax.set_ylabel('Value ($)', fontsize=11, color=COLORS['text'])
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45 if len(categories) > 6 else 0, ha='right' if len(categories) > 6 else 'center')
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()
    
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{image_base64}"


def render_scenario_chart(data: Dict[str, Any]) -> str:
    """
    Render a multi-line chart for scenario analysis
    
    Args:
        data: Dictionary with scenarios (base_case, optimistic, conservative)
        
    Returns:
        Base64 encoded PNG image
    """
    set_chart_style()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Colors for scenarios
    scenario_colors = {
        'base_case': COLORS['secondary'],
        'optimistic': COLORS['positive'],
        'conservative': COLORS['accent']
    }
    
    scenario_labels = {
        'base_case': 'Base Case',
        'optimistic': 'Optimistic',
        'conservative': 'Conservative'
    }
    
    # Plot each scenario
    for scenario_key, color in scenario_colors.items():
        scenario_data = data.get(scenario_key, [])
        if scenario_data:
            months = [d['month'] for d in scenario_data]
            revenues = [d['revenue'] for d in scenario_data]
            
            ax.plot(months, revenues,
                   color=color,
                   linewidth=2.5,
                   label=scenario_labels[scenario_key],
                   marker='o' if scenario_key == 'base_case' else None,
                   markersize=5)
    
    # Styling
    ax.set_title('Revenue Forecast Scenarios', fontsize=14, fontweight='bold', pad=20, color=COLORS['primary'])
    ax.set_ylabel('Revenue ($)', fontsize=11, color=COLORS['text'])
    ax.set_xlabel('')
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M'))
    
    # Legend
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=False)
    
    # Rotate x labels
    plt.xticks(rotation=45, ha='right')
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor=COLORS['background'])
    plt.close()
    
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{image_base64}"


def build_base64_chart(chart_type: str, data: Dict[str, Any], **kwargs) -> str:
    """
    Main entry point for chart generation
    
    Args:
        chart_type: Type of chart (line, area, bar, waterfall, scenario)
        data: Chart data
        **kwargs: Additional parameters
        
    Returns:
        Base64 encoded PNG image
    """
    try:
        if chart_type == 'line':
            return render_line_chart(data, kwargs.get('palette_key', 'secondary'))
        elif chart_type == 'area':
            return render_area_chart(data, kwargs.get('palette_key', 'accent'))
        elif chart_type == 'bar':
            return render_bar_chart(data, kwargs.get('palette_key', 'secondary'))
        elif chart_type == 'waterfall':
            return render_waterfall_chart(data)
        elif chart_type == 'scenario':
            return render_scenario_chart(data)
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")
            
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        
        # Return a placeholder image
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'Chart Generation Failed\n{chart_type}', 
                ha='center', va='center', fontsize=14, color=COLORS['text'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode('utf-8')}"