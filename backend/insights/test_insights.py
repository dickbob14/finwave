#!/usr/bin/env python3
"""
Test the Insight Engine with sample data
"""

import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insights.insight_engine import InsightEngine, generate_template_insights

def test_insight_generation():
    """Test insight generation with a populated template"""
    
    print("🧪 Testing Insight Engine")
    print("=" * 60)
    
    # Initialize engine
    engine = InsightEngine()
    
    # Check if we have a populated template
    populated_dir = Path(__file__).parent.parent / 'templates' / 'populated'
    if not populated_dir.exists():
        populated_dir = Path(__file__).parent.parent / 'assets' / 'templates'
    
    # Find a 3-statement model file
    test_file = None
    for file in populated_dir.glob('3statement*.xlsx'):
        test_file = file
        break
    
    if not test_file:
        print("❌ No populated 3-statement model found")
        print("   Run: make populate-3statement-real first")
        return False
    
    print(f"📊 Using template: {test_file.name}")
    
    # Extract metrics
    print("\n1️⃣ Extracting metrics...")
    metrics = engine.extract_metrics_from_template(test_file, '3_statement_model')
    
    if metrics:
        print("   ✅ Metrics extracted successfully")
        
        # Show some key metrics
        if 'income_statement' in metrics:
            revenue = metrics['income_statement'].get('revenue', {})
            if revenue:
                print(f"   📈 Revenue: ${revenue.get('current', 0):,.0f}")
                print(f"   📊 Change: {revenue.get('change_pct', 0):+.1f}%")
        
        if 'ratios' in metrics:
            print(f"   💰 Gross Margin: {metrics['ratios'].get('gross_margin', 0):.1f}%")
            print(f"   💵 EBITDA Margin: {metrics['ratios'].get('ebitda_margin', 0):.1f}%")
    
    # Generate insights
    print("\n2️⃣ Generating insights...")
    
    company_context = {
        'industry': 'SaaS',
        'stage': 'growth',
        'employee_count': 50
    }
    
    insights = engine.generate_insights(metrics, '3_statement_model', company_context)
    
    if insights:
        print("   ✅ Insights generated successfully")
        
        print(f"\n📝 Executive Summary:")
        print(f"   {insights['summary']}")
        
        print(f"\n💡 Narrative:")
        print(f"   {insights['narrative']}")
        
        print(f"\n🔍 Key Findings ({len(insights['findings'])}):")
        for finding in insights['findings'][:3]:
            print(f"   - {finding['metric']}: {finding.get('significance', 'medium')} significance")
        
        print(f"\n🎯 Recommendations ({len(insights['recommendations'])}):")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Test API integration
    print("\n3️⃣ Testing API integration...")
    try:
        api_insights = generate_template_insights(
            str(test_file),
            '3_statement_model',
            company_context
        )
        print("   ✅ API integration working")
    except Exception as e:
        print(f"   ❌ API integration failed: {e}")
    
    print("\n✨ Insight Engine test complete!")
    return True


if __name__ == '__main__':
    # Check for OpenAI key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  No OpenAI API key found")
        print("   Insights will use rule-based generation")
        print("   Set OPENAI_API_KEY for GPT-4 powered insights")
        print()
    
    success = test_insight_generation()
    exit(0 if success else 1)