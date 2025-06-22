"""
Chart generation helpers for PDF reports
"""

import io
import base64
import json
import logging
from datetime import date
from pathlib import Path
from typing import List, Optional, Dict, Any
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generate charts for PDF reports"""
    
    def __init__(self, theme_path: str = None):
        self.theme = self._load_theme(theme_path)
        self._setup_style()
        
    def _load_theme(self, theme_path: str = None) -> Dict[str, Any]:
        """Load theme configuration"""
        if not theme_path:
            theme_path = Path(__file__).parent.parent / 'static' / 'theme.json'
        
        with open(theme_path) as f:
            return json.load(f)
    
    def _setup_style(self):
        """Setup matplotlib style based on theme"""
        # Set font
        plt.rcParams['font.family'] = self.theme['charts']['font_family']
        plt.rcParams['font.size'] = 10
        
        # Set colors
        plt.rcParams['text.color'] = self.theme['charts']['text_color']
        plt.rcParams['axes.labelcolor'] = self.theme['charts']['text_color']
        plt.rcParams['xtick.color'] = self.theme['charts']['text_color']
        plt.rcParams['ytick.color'] = self.theme['charts']['text_color']
        
        # Grid style
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.color'] = self.theme['charts']['grid_color']
        plt.rcParams['grid.linestyle'] = '-'
        plt.rcParams['grid.linewidth'] = 0.5
        plt.rcParams['grid.alpha'] = 0.3
        
        # Remove spines
        plt.rcParams['axes.spines.top'] = False
        plt.rcParams['axes.spines.right'] = False
        
        # Set figure background
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
    
    def _fig_to_base64(self, fig: Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        plt.close(fig)
        return image_base64
    
    def plot_revenue_trend(self, periods: List[str], values: List[Optional[float]], 
                          title: str = "Revenue Trend") -> str:
        """Generate revenue trend line chart"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Filter out None values
        filtered_data = [(p, v) for p, v in zip(periods, values) if v is not None]
        if not filtered_data:
            return ""
        
        periods_filtered, values_filtered = zip(*filtered_data)
        
        # Plot line
        ax.plot(range(len(periods_filtered)), values_filtered, 
               color=self.theme['colors']['primary_color'], 
               linewidth=2.5, marker='o', markersize=6)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Set x-axis labels
        ax.set_xticks(range(len(periods_filtered)))
        ax.set_xticklabels(periods_filtered, rotation=45, ha='right')
        
        # Add value labels on points
        for i, (period, value) in enumerate(zip(periods_filtered, values_filtered)):
            ax.annotate(f'${value/1000:.0f}K', 
                       xy=(i, value), 
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=9,
                       color=self.theme['charts']['text_color'])
        
        # Styling
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('')
        ax.set_ylabel('Revenue', fontsize=11)
        
        # Tight layout
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def plot_burn_vs_revenue(self, periods: List[str], 
                           revenue: List[Optional[float]], 
                           burn: List[Optional[float]]) -> str:
        """Generate dual-axis chart for burn rate vs revenue"""
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        # Revenue bars
        x = range(len(periods))
        ax1.bar(x, [r or 0 for r in revenue], 
               color=self.theme['colors']['primary_color'], 
               alpha=0.7, label='Revenue')
        
        # Burn line (secondary axis)
        ax2 = ax1.twinx()
        ax2.plot(x, [b or 0 for b in burn], 
                color=self.theme['colors']['danger_color'], 
                linewidth=2.5, marker='o', label='Burn Rate')
        
        # Format axes
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Labels
        ax1.set_xlabel('')
        ax1.set_ylabel('Revenue', fontsize=11, color=self.theme['colors']['primary_color'])
        ax2.set_ylabel('Burn Rate', fontsize=11, color=self.theme['colors']['danger_color'])
        
        # X-axis
        ax1.set_xticks(x)
        ax1.set_xticklabels(periods, rotation=45, ha='right')
        
        # Title
        ax1.set_title('Revenue vs Burn Rate', fontsize=14, fontweight='bold', pad=20)
        
        # Color the y-axis labels
        ax1.tick_params(axis='y', labelcolor=self.theme['colors']['primary_color'])
        ax2.tick_params(axis='y', labelcolor=self.theme['colors']['danger_color'])
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def plot_margin_analysis(self, periods: List[str], 
                           gross_margin: List[Optional[float]], 
                           ebitda_margin: List[Optional[float]]) -> str:
        """Generate margin trend chart"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        x = range(len(periods))
        
        # Plot lines
        if any(gross_margin):
            ax.plot(x, [m or 0 for m in gross_margin], 
                   color=self.theme['colors']['success_color'], 
                   linewidth=2.5, marker='o', label='Gross Margin')
        
        if any(ebitda_margin):
            ax.plot(x, [m or 0 for m in ebitda_margin], 
                   color=self.theme['colors']['primary_color'], 
                   linewidth=2.5, marker='s', label='EBITDA Margin')
        
        # Add zero line
        ax.axhline(y=0, color=self.theme['charts']['grid_color'], 
                  linestyle='--', linewidth=1)
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        # X-axis
        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45, ha='right')
        
        # Labels and title
        ax.set_title('Margin Analysis', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('')
        ax.set_ylabel('Margin %', fontsize=11)
        
        # Legend
        ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def plot_cash_runway(self, cash_balance: float, burn_rate: float, 
                        runway_months: int) -> str:
        """Generate cash runway projection chart"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Project cash over time
        months = list(range(runway_months + 3))  # Extra months to show zero
        cash_projection = [max(0, cash_balance - (burn_rate * m)) for m in months]
        
        # Plot area chart
        ax.fill_between(months, cash_projection, alpha=0.3, 
                       color=self.theme['colors']['primary_color'])
        ax.plot(months, cash_projection, 
               color=self.theme['colors']['primary_color'], 
               linewidth=2.5)
        
        # Add runway line
        ax.axvline(x=runway_months, color=self.theme['colors']['danger_color'], 
                  linestyle='--', linewidth=2, alpha=0.7)
        ax.text(runway_months, cash_balance * 0.5, f'{runway_months} months', 
               rotation=90, va='center', ha='right', 
               color=self.theme['colors']['danger_color'],
               fontweight='bold')
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000000:.1f}M'))
        
        # Labels
        ax.set_title('Cash Runway Projection', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Months from Today', fontsize=11)
        ax.set_ylabel('Cash Balance', fontsize=11)
        
        # Styling
        ax.set_xlim(0, len(months) - 1)
        ax.set_ylim(0, cash_balance * 1.1)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def plot_kpi_gauge(self, value: float, target: float, 
                      title: str, is_percentage: bool = False) -> str:
        """Generate a gauge chart for KPI vs target"""
        fig, ax = plt.subplots(figsize=(6, 4), subplot_kw=dict(projection='polar'))
        
        # Calculate percentage of target
        pct_of_target = min(value / target * 100, 150) if target > 0 else 0
        
        # Set up the gauge
        theta = [0, pct_of_target * 1.8]  # 180 degrees = 100%
        radii = [0, 1]
        
        # Determine color based on performance
        if pct_of_target >= 95:
            color = self.theme['colors']['success_color']
        elif pct_of_target >= 80:
            color = self.theme['colors']['warning_color']
        else:
            color = self.theme['colors']['danger_color']
        
        # Plot gauge
        ax.bar(theta[1] * 3.14159 / 180, radii[1], width=0.3, bottom=0.5,
              color=color, alpha=0.8)
        
        # Add text
        ax.text(0, -0.1, f'{value:.1f}{"%" if is_percentage else ""}', 
               ha='center', va='center', fontsize=24, fontweight='bold')
        ax.text(0, -0.3, f'Target: {target:.1f}{"%" if is_percentage else ""}', 
               ha='center', va='center', fontsize=12, 
               color=self.theme['charts']['text_color'])
        
        # Remove polar labels
        ax.set_ylim(0, 1)
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.grid(False)
        ax.spines['polar'].set_visible(False)
        
        # Title
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def generate_all_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all charts for a report"""
        charts = {}
        
        try:
            # Revenue trend
            if 'income_statement' in report_data:
                revenue_data = next((item for item in report_data['income_statement'] 
                                   if item['label'] == 'Revenue'), None)
                if revenue_data and revenue_data['values']:
                    charts['revenue_trend'] = self.plot_revenue_trend(
                        report_data['periods'][-len(revenue_data['values']):],
                        revenue_data['values']
                    )
            
            # Margin analysis
            if 'kpi_dashboard' in report_data and 'Financial' in report_data['kpi_dashboard']:
                financial_kpis = report_data['kpi_dashboard']['Financial']
                gross_margin = next((m for m in financial_kpis if m['name'] == 'Gross Margin %'), None)
                ebitda_margin = next((m for m in financial_kpis if m['name'] == 'EBITDA Margin %'), None)
                
                if gross_margin or ebitda_margin:
                    charts['margin_analysis'] = self.plot_margin_analysis(
                        report_data['periods'][-3:],
                        gross_margin['values'] if gross_margin else [None]*3,
                        ebitda_margin['values'] if ebitda_margin else [None]*3
                    )
            
            # Cash runway
            if 'runway_analysis' in report_data and report_data['runway_analysis']:
                runway = report_data['runway_analysis']
                if runway.get('cash') and runway.get('burn_rate'):
                    charts['cash_runway'] = self.plot_cash_runway(
                        runway['cash'],
                        runway['burn_rate'],
                        int(runway['months'])
                    )
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return charts