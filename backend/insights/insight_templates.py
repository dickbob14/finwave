"""
Enhanced insight templates incorporating payroll and cohort metrics
"""

INSIGHT_TEMPLATES = {
    'payroll_insights': {
        'headcount_change': {
            'condition': lambda m: abs(m.get('new_hires_mtd', 0) - m.get('terminations_mtd', 0)) > 2,
            'template': "Headcount {direction} by {net_change} this month ({new_hires} hires, {terminations} departures). {impact}",
            'params': lambda m: {
                'direction': 'grew' if m['new_hires_mtd'] > m['terminations_mtd'] else 'shrank',
                'net_change': abs(m['new_hires_mtd'] - m['terminations_mtd']),
                'new_hires': m['new_hires_mtd'],
                'terminations': m['terminations_mtd'],
                'impact': 'Consider capacity planning.' if m['new_hires_mtd'] > m['terminations_mtd'] else 'Monitor retention drivers.'
            },
            'significance': 'high'
        },
        
        'payroll_efficiency': {
            'condition': lambda m: m.get('payroll_as_pct_revenue', 0) > 50,
            'template': "Payroll represents {pct:.1f}% of revenue. {benchmark} {action}",
            'params': lambda m: {
                'pct': m['payroll_as_pct_revenue'],
                'benchmark': 'Above 40-45% SaaS benchmark.' if m['payroll_as_pct_revenue'] > 45 else 'Within normal range.',
                'action': 'Review productivity metrics and automation opportunities.' if m['payroll_as_pct_revenue'] > 45 else ''
            },
            'significance': 'high' if lambda m: m.get('payroll_as_pct_revenue', 0) > 45 else 'medium'
        },
        
        'cost_per_fte': {
            'condition': lambda m: m.get('average_cost_fte', 0) > 0,
            'template': "Average fully-loaded cost per FTE: ${cost:,.0f}/month (includes {benefits_load:.0f}% benefits load)",
            'params': lambda m: {
                'cost': m['average_cost_fte'],
                'benefits_load': m.get('benefits_load_pct', 20) * 100
            },
            'significance': 'medium'
        }
    },
    
    'cohort_insights': {
        'retention_trend': {
            'condition': lambda m: m.get('net_retention_rate', 0) != 100,
            'template': "Net revenue retention at {nrr:.0f}%. {assessment} {recommendation}",
            'params': lambda m: {
                'nrr': m['net_retention_rate'],
                'assessment': 'Excellent - expansion offsetting churn.' if m['net_retention_rate'] > 110 
                            else 'Healthy retention.' if m['net_retention_rate'] > 95
                            else 'Concerning churn levels.',
                'recommendation': '' if m['net_retention_rate'] > 95 
                                else 'Prioritize customer success initiatives.'
            },
            'significance': 'high' if lambda m: m['net_retention_rate'] < 95 else 'medium'
        },
        
        'cac_payback': {
            'condition': lambda m: m.get('months_to_recover_cac', 0) > 0,
            'template': "CAC payback period: {months:.1f} months. {assessment}",
            'params': lambda m: {
                'months': m['months_to_recover_cac'],
                'assessment': 'Excellent efficiency.' if m['months_to_recover_cac'] < 12
                            else 'Within target range.' if m['months_to_recover_cac'] < 18
                            else 'Consider optimizing acquisition costs.'
            },
            'significance': 'high' if lambda m: m['months_to_recover_cac'] > 18 else 'medium'
        },
        
        'ltv_cac_ratio': {
            'condition': lambda m: m.get('ltv_to_cac_ratio', 0) > 0,
            'template': "LTV:CAC ratio of {ratio:.1f}x indicates {assessment}",
            'params': lambda m: {
                'ratio': m['ltv_to_cac_ratio'],
                'assessment': 'strong unit economics.' if m['ltv_to_cac_ratio'] > 3
                            else 'acceptable unit economics.' if m['ltv_to_cac_ratio'] > 1.5
                            else 'challenging unit economics - review pricing and retention.'
            },
            'significance': 'high'
        }
    },
    
    'productivity_insights': {
        'revenue_per_employee': {
            'condition': lambda m: m.get('revenue_per_fte', 0) > 0 and m.get('fte_count', 0) > 10,
            'template': "Revenue per FTE: ${rev_per_fte:,.0f} ({assessment} for {industry})",
            'params': lambda m, context: {
                'rev_per_fte': m['revenue_per_fte'],
                'assessment': 'strong' if m['revenue_per_fte'] > 200000/12 else 'below benchmark',
                'industry': context.get('industry', 'SaaS')
            },
            'significance': 'medium'
        },
        
        'department_efficiency': {
            'condition': lambda m: 'department_metrics' in m,
            'template': "Engineering represents {eng_pct:.0f}% of headcount. Sales efficiency at ${rev_per_sales:,.0f}/rep",
            'params': lambda m: {
                'eng_pct': m['department_metrics'].get('engineering_pct', 0),
                'rev_per_sales': m['department_metrics'].get('revenue_per_sales_rep', 0)
            },
            'significance': 'medium'
        }
    },
    
    'integrated_insights': {
        'burn_vs_growth': {
            'condition': lambda m: m.get('burn_rate', 0) > 0 and m.get('revenue_growth_yoy', 0) > 0,
            'template': "Burn multiple of {burn_multiple:.1f}x ({burn:,.0f} burn / {growth:.0f}% growth). {assessment}",
            'params': lambda m: {
                'burn_multiple': abs(m['burn_rate']) / m['revenue_growth_yoy'] if m['revenue_growth_yoy'] > 0 else 999,
                'burn': abs(m['burn_rate']),
                'growth': m['revenue_growth_yoy'],
                'assessment': 'Efficient growth.' if abs(m['burn_rate']) / m['revenue_growth_yoy'] < 1.5
                            else 'Monitor efficiency.' if abs(m['burn_rate']) / m['revenue_growth_yoy'] < 2.5
                            else 'High burn relative to growth.'
            },
            'significance': 'high'
        },
        
        'runway_alert': {
            'condition': lambda m: m.get('runway_months', 0) < 18 and m.get('runway_months', 0) > 0,
            'template': "⚠️ {runway:.0f} months of runway at current burn rate. {action}",
            'params': lambda m: {
                'runway': m['runway_months'],
                'action': 'Consider fundraising timeline.' if m['runway_months'] < 12
                        else 'Monitor cash position closely.'
            },
            'significance': 'critical' if lambda m: m['runway_months'] < 12 else 'high'
        }
    }
}

def generate_payroll_narrative(metrics: dict, context: dict = None) -> str:
    """Generate narrative incorporating payroll insights"""
    
    parts = []
    
    # Headcount overview
    if 'total_headcount' in metrics:
        parts.append(
            f"The company employs {metrics['total_headcount']} people "
            f"({metrics.get('fte_count', 0)} FTEs, {metrics.get('contractor_count', 0)} contractors)."
        )
    
    # Headcount changes
    net_change = metrics.get('new_hires_mtd', 0) - metrics.get('terminations_mtd', 0)
    if net_change != 0:
        parts.append(
            f"Headcount {'increased' if net_change > 0 else 'decreased'} by {abs(net_change)} this month."
        )
    
    # Cost efficiency
    if 'payroll_as_pct_revenue' in metrics:
        pct = metrics['payroll_as_pct_revenue']
        if pct > 50:
            parts.append(
                f"Payroll costs consume {pct:.0f}% of revenue, suggesting opportunity for productivity gains."
            )
        elif pct < 30:
            parts.append(
                f"Strong operating leverage with payroll at just {pct:.0f}% of revenue."
            )
    
    return " ".join(parts)

def generate_cohort_narrative(metrics: dict, context: dict = None) -> str:
    """Generate narrative for cohort performance"""
    
    parts = []
    
    # Retention metrics
    if 'net_retention_rate' in metrics:
        nrr = metrics['net_retention_rate']
        if nrr > 120:
            parts.append(f"Exceptional {nrr:.0f}% net retention driven by strong expansion revenue.")
        elif nrr > 100:
            parts.append(f"Healthy {nrr:.0f}% net retention with expansion offsetting churn.")
        elif nrr > 80:
            parts.append(f"Net retention of {nrr:.0f}% indicates moderate churn pressure.")
        else:
            parts.append(f"Critical: {nrr:.0f}% net retention requires immediate attention.")
    
    # CAC efficiency
    if 'months_to_recover_cac' in metrics and 'ltv_to_cac_ratio' in metrics:
        months = metrics['months_to_recover_cac']
        ratio = metrics['ltv_to_cac_ratio']
        
        parts.append(
            f"Customer acquisition shows {months:.0f}-month payback with {ratio:.1f}x LTV:CAC ratio."
        )
    
    return " ".join(parts)