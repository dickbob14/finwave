"""
LLM-powered financial commentary generation system
Integrates with language models to provide intelligent financial analysis and insights
"""
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dataclasses import dataclass
import os

from sqlalchemy.orm import Session
from database import get_db_session
from templates.excel_templates import ExcelTemplateGenerator
from insights.variance_analyzer import VarianceInsight, TrendAnalysis, generate_financial_insights

logger = logging.getLogger(__name__)

@dataclass
class FinancialCommentary:
    """Container for AI-generated financial commentary"""
    executive_summary: str
    performance_analysis: List[str]
    variance_commentary: List[str]
    trend_insights: List[str]
    risk_assessment: str
    opportunities: List[str]
    recommendations: List[str]
    confidence_score: float
    data_sources: List[str]
    generated_at: datetime

class LLMCommentaryEngine:
    """LLM-powered financial commentary generation"""
    
    def __init__(self, llm_provider: str = "openai", model: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize LLM commentary engine
        
        Args:
            llm_provider: LLM provider ("openai", "anthropic", "local")
            model: Model name to use
            api_key: API key for the provider (if not in env vars)
        """
        self.llm_provider = llm_provider
        self.model = model
        self.api_key = api_key or self._get_api_key()
        
        # Initialize LLM client based on provider
        self.client = self._initialize_llm_client()
        
        # Commentary templates
        self.templates = {
            'system_prompt': self._get_system_prompt(),
            'analysis_prompt': self._get_analysis_prompt_template(),
            'variance_prompt': self._get_variance_prompt_template(),
            'trend_prompt': self._get_trend_prompt_template()
        }
    
    def generate_comprehensive_commentary(self, start_date: str, end_date: str, 
                                        include_technical_analysis: bool = True) -> FinancialCommentary:
        """
        Generate comprehensive financial commentary using LLM
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            include_technical_analysis: Whether to include technical variance analysis
            
        Returns:
            FinancialCommentary object with AI-generated insights
        """
        # Gather financial data
        financial_data = self._gather_comprehensive_data(start_date, end_date)
        
        # Generate insights using variance analyzer if requested
        insights_data = {}
        if include_technical_analysis:
            insights_data = generate_financial_insights(start_date, end_date)
        
        # Generate commentary sections
        executive_summary = self._generate_executive_summary(financial_data, insights_data)
        performance_analysis = self._generate_performance_analysis(financial_data, insights_data)
        variance_commentary = self._generate_variance_commentary(insights_data.get('variances', []))
        trend_insights = self._generate_trend_insights(insights_data.get('trends', []))
        risk_assessment = self._generate_risk_assessment(financial_data, insights_data)
        opportunities = self._generate_opportunities(financial_data, insights_data)
        recommendations = self._generate_recommendations(financial_data, insights_data)
        
        # Calculate confidence score based on data quality
        confidence_score = self._calculate_confidence_score(financial_data, insights_data)
        
        return FinancialCommentary(
            executive_summary=executive_summary,
            performance_analysis=performance_analysis,
            variance_commentary=variance_commentary,
            trend_insights=trend_insights,
            risk_assessment=risk_assessment,
            opportunities=opportunities,
            recommendations=recommendations,
            confidence_score=confidence_score,
            data_sources=self._get_data_sources(financial_data, insights_data),
            generated_at=datetime.now()
        )
    
    def generate_variance_explanation(self, variance_insights: List[Dict]) -> List[str]:
        """
        Generate natural language explanations for variance insights
        
        Args:
            variance_insights: List of variance insight dictionaries
            
        Returns:
            List of explanatory commentary strings
        """
        if not variance_insights:
            return ["No significant variances detected in the analyzed period."]
        
        # Group variances by type and severity
        grouped_variances = self._group_variances(variance_insights)
        
        explanations = []
        
        for variance_type, variances in grouped_variances.items():
            if variances:
                explanation = self._generate_variance_type_explanation(variance_type, variances)
                explanations.append(explanation)
        
        return explanations
    
    def generate_trend_narrative(self, trend_analyses: List[Dict]) -> List[str]:
        """
        Generate narrative descriptions of trend patterns
        
        Args:
            trend_analyses: List of trend analysis dictionaries
            
        Returns:
            List of trend narrative strings
        """
        if not trend_analyses:
            return ["No significant trends identified in the analyzed accounts."]
        
        narratives = []
        
        # Categorize trends
        strong_upward = [t for t in trend_analyses if t['trend_direction'] == 'increasing' and t['trend_strength'] > 0.7]
        strong_downward = [t for t in trend_analyses if t['trend_direction'] == 'decreasing' and t['trend_strength'] > 0.7]
        volatile = [t for t in trend_analyses if t['trend_direction'] == 'volatile']
        
        if strong_upward:
            narrative = self._generate_upward_trend_narrative(strong_upward)
            narratives.append(narrative)
        
        if strong_downward:
            narrative = self._generate_downward_trend_narrative(strong_downward)
            narratives.append(narrative)
        
        if volatile:
            narrative = self._generate_volatility_narrative(volatile)
            narratives.append(narrative)
        
        return narratives
    
    def generate_custom_analysis(self, data: Dict, analysis_type: str, custom_prompt: str) -> str:
        """
        Generate custom financial analysis using provided prompt
        
        Args:
            data: Financial data dictionary
            analysis_type: Type of analysis being performed
            custom_prompt: Custom prompt for the LLM
            
        Returns:
            Generated analysis text
        """
        # Prepare context with financial data
        context = self._prepare_llm_context(data)
        
        # Construct full prompt
        full_prompt = f"""
        {self.templates['system_prompt']}
        
        Context: {context}
        
        Analysis Type: {analysis_type}
        
        Specific Request: {custom_prompt}
        
        Please provide a detailed, professional analysis addressing the specific request.
        """
        
        return self._call_llm(full_prompt)
    
    def _initialize_llm_client(self):
        """Initialize LLM client based on provider"""
        if self.llm_provider == "openai":
            try:
                import openai
                return openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                raise
        elif self.llm_provider == "anthropic":
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("Anthropic package not installed. Run: pip install anthropic")
                raise
        elif self.llm_provider == "local":
            # For local models (e.g., Ollama), implement custom client
            return self._initialize_local_client()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _initialize_local_client(self):
        """Initialize local LLM client (placeholder for local models)"""
        # This would integrate with local models like Ollama
        logger.warning("Local LLM provider not yet implemented, using mock responses")
        return None
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables"""
        if self.llm_provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.llm_provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        return None
    
    def _gather_comprehensive_data(self, start_date: str, end_date: str) -> Dict:
        """Gather comprehensive financial data for LLM analysis"""
        with get_db_session() as db:
            excel_gen = ExcelTemplateGenerator()
            
            # Key financial metrics
            revenue = excel_gen._get_revenue(db, start_date, end_date)
            expenses = excel_gen._get_expenses(db, start_date, end_date)
            net_income = revenue - expenses
            profit_margin = (net_income / revenue * 100) if revenue != 0 else 0
            
            # Balance sheet data
            cash_balance = excel_gen._get_cash_balance(db, end_date)
            ar_balance = excel_gen._get_ar_balance(db, end_date)
            ap_balance = excel_gen._get_ap_balance(db, end_date)
            
            # P&L breakdown
            pl_data = excel_gen._get_pl_data(db, start_date, end_date)
            
            # Trial balance
            trial_balance = excel_gen._get_trial_balance_data(db, start_date, end_date)
            
            # Previous period comparison
            prev_start = (datetime.fromisoformat(start_date) - timedelta(days=30)).date().isoformat()
            prev_end = (datetime.fromisoformat(end_date) - timedelta(days=30)).date().isoformat()
            
            prev_revenue = excel_gen._get_revenue(db, prev_start, prev_end)
            prev_expenses = excel_gen._get_expenses(db, prev_start, prev_end)
            prev_net_income = prev_revenue - prev_expenses
            
            return {
                'period': {'start_date': start_date, 'end_date': end_date},
                'current_metrics': {
                    'revenue': float(revenue),
                    'expenses': float(expenses),
                    'net_income': float(net_income),
                    'profit_margin': float(profit_margin),
                    'cash_balance': float(cash_balance),
                    'accounts_receivable': float(ar_balance),
                    'accounts_payable': float(ap_balance)
                },
                'previous_metrics': {
                    'revenue': float(prev_revenue),
                    'expenses': float(prev_expenses),
                    'net_income': float(prev_net_income)
                },
                'growth_metrics': {
                    'revenue_growth': float((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue != 0 else 0,
                    'expense_growth': float((expenses - prev_expenses) / prev_expenses * 100) if prev_expenses != 0 else 0,
                    'net_income_change': float(net_income - prev_net_income)
                },
                'detailed_pl': {
                    'revenue_accounts': [{'name': r['account_name'], 'amount': float(r['amount'])} for r in pl_data['revenue']],
                    'expense_accounts': [{'name': e['account_name'], 'amount': float(e['amount'])} for e in pl_data['expenses']]
                },
                'account_balances': [
                    {
                        'account_name': tb['account_name'],
                        'account_type': tb['account_type'],
                        'debit_total': float(tb['debit_total']),
                        'credit_total': float(tb['credit_total'])
                    }
                    for tb in trial_balance
                ]
            }
    
    def _generate_executive_summary(self, financial_data: Dict, insights_data: Dict) -> str:
        """Generate executive summary using LLM"""
        context = self._prepare_llm_context(financial_data, insights_data)
        
        prompt = f"""
        {self.templates['system_prompt']}
        
        Financial Data Context:
        {context}
        
        Please provide a concise executive summary (150-200 words) of the financial performance for this period. 
        Focus on:
        1. Overall financial health
        2. Key performance highlights
        3. Major concerns or risks
        4. One primary recommendation
        
        Write in a professional, executive-level tone suitable for board presentation.
        """
        
        return self._call_llm(prompt)
    
    def _generate_performance_analysis(self, financial_data: Dict, insights_data: Dict) -> List[str]:
        """Generate detailed performance analysis"""
        context = self._prepare_llm_context(financial_data, insights_data)
        
        prompt = f"""
        {self.templates['system_prompt']}
        
        Financial Data Context:
        {context}
        
        Please provide a detailed performance analysis broken into 3-4 key insights. 
        For each insight, provide:
        1. The specific metric or finding
        2. Context compared to previous period
        3. Business implications
        4. Potential underlying causes
        
        Format as separate bullet points for each major insight.
        """
        
        response = self._call_llm(prompt)
        return self._parse_bulleted_response(response)
    
    def _generate_variance_commentary(self, variances: List[Dict]) -> List[str]:
        """Generate commentary on variance analysis"""
        if not variances:
            return ["No significant variances requiring management attention were identified."]
        
        # Group by severity
        critical_variances = [v for v in variances if v['severity'] == 'critical']
        high_variances = [v for v in variances if v['severity'] == 'high']
        
        commentary = []
        
        if critical_variances:
            prompt = f"""
            Analyze these critical financial variances and provide management commentary:
            
            {json.dumps(critical_variances, indent=2)}
            
            For each critical variance, explain:
            1. What the variance indicates
            2. Potential business impact
            3. Immediate actions required
            
            Write in a serious, action-oriented tone.
            """
            critical_commentary = self._call_llm(prompt)
            commentary.append(f"Critical Variances: {critical_commentary}")
        
        if high_variances:
            prompt = f"""
            Analyze these high-priority financial variances:
            
            {json.dumps(high_variances, indent=2)}
            
            Provide insights on patterns and recommended management attention areas.
            """
            high_commentary = self._call_llm(prompt)
            commentary.append(f"High Priority Variances: {high_commentary}")
        
        return commentary
    
    def _generate_trend_insights(self, trends: List[Dict]) -> List[str]:
        """Generate insights on trend analysis"""
        if not trends:
            return ["No significant trends detected in account performance."]
        
        # Categorize trends
        positive_trends = [t for t in trends if t['trend_direction'] == 'increasing' and t['trend_strength'] > 0.5]
        negative_trends = [t for t in trends if t['trend_direction'] == 'decreasing' and t['trend_strength'] > 0.5]
        volatile_accounts = [t for t in trends if t['trend_direction'] == 'volatile']
        
        insights = []
        
        if positive_trends:
            prompt = f"""
            Analyze these positive trending accounts:
            {json.dumps(positive_trends, indent=2)}
            
            Provide insight on what's driving growth and sustainability outlook.
            """
            insight = self._call_llm(prompt)
            insights.append(f"Positive Trends: {insight}")
        
        if negative_trends:
            prompt = f"""
            Analyze these declining accounts:
            {json.dumps(negative_trends, indent=2)}
            
            Identify concerns and recommend corrective actions.
            """
            insight = self._call_llm(prompt)
            insights.append(f"Declining Trends: {insight}")
        
        if volatile_accounts:
            prompt = f"""
            Analyze these volatile accounts:
            {json.dumps(volatile_accounts, indent=2)}
            
            Explain volatility causes and risk management recommendations.
            """
            insight = self._call_llm(prompt)
            insights.append(f"Volatility Concerns: {insight}")
        
        return insights
    
    def _generate_risk_assessment(self, financial_data: Dict, insights_data: Dict) -> str:
        """Generate risk assessment"""
        context = self._prepare_llm_context(financial_data, insights_data)
        
        prompt = f"""
        {self.templates['system_prompt']}
        
        Financial Data Context:
        {context}
        
        Provide a comprehensive risk assessment (100-150 words) covering:
        1. Liquidity risks
        2. Operational risks
        3. Market risks
        4. Overall risk level (Low/Medium/High)
        
        Focus on data-driven risk identification.
        """
        
        return self._call_llm(prompt)
    
    def _generate_opportunities(self, financial_data: Dict, insights_data: Dict) -> List[str]:
        """Generate identified opportunities"""
        context = self._prepare_llm_context(financial_data, insights_data)
        
        prompt = f"""
        {self.templates['system_prompt']}
        
        Financial Data Context:
        {context}
        
        Identify 3-5 specific business opportunities based on the financial data. 
        Focus on:
        1. Growth opportunities
        2. Cost optimization opportunities
        3. Process improvement opportunities
        4. Investment opportunities
        
        Format as separate bullet points with specific, actionable opportunities.
        """
        
        response = self._call_llm(prompt)
        return self._parse_bulleted_response(response)
    
    def _generate_recommendations(self, financial_data: Dict, insights_data: Dict) -> List[str]:
        """Generate strategic recommendations"""
        context = self._prepare_llm_context(financial_data, insights_data)
        
        prompt = f"""
        {self.templates['system_prompt']}
        
        Financial Data Context:
        {context}
        
        Provide 5-7 strategic recommendations prioritized by impact and urgency.
        Include:
        1. Immediate actions (next 30 days)
        2. Short-term initiatives (next quarter)
        3. Long-term strategic moves
        
        Format as prioritized action items with clear next steps.
        """
        
        response = self._call_llm(prompt)
        return self._parse_bulleted_response(response)
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt"""
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            else:
                # Fallback to mock response for testing
                return self._generate_mock_response(prompt)
                
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return self._generate_fallback_response(prompt)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response for testing purposes"""
        if "executive summary" in prompt.lower():
            return """The company demonstrates solid financial performance for the analyzed period with revenue growth and maintained profit margins. 
            Key strengths include strong cash position and controlled expense growth. 
            Areas requiring attention include accounts receivable management and potential seasonal revenue fluctuations. 
            Overall financial health appears stable with opportunities for operational optimization."""
        
        elif "performance analysis" in prompt.lower():
            return """• Revenue Performance: Strong growth trajectory with diversified revenue streams showing resilience
            • Cost Management: Expenses well-controlled with opportunities for further optimization
            • Profitability: Healthy margins maintained despite market pressures
            • Cash Flow: Positive operating cash flow with adequate liquidity position"""
        
        elif "risk assessment" in prompt.lower():
            return """Current risk level: MEDIUM. Primary risks include customer concentration in accounts receivable, 
            seasonal revenue volatility, and potential margin pressure from rising costs. 
            Liquidity position remains strong with adequate cash reserves. 
            Recommend enhanced monitoring of collection processes and cost structure optimization."""
        
        else:
            return "Financial analysis indicates stable performance with opportunities for improvement in operational efficiency and strategic growth initiatives."
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate fallback response when LLM fails"""
        return "Unable to generate detailed commentary due to LLM service issues. Please review financial data manually for insights."
    
    def _prepare_llm_context(self, financial_data: Dict, insights_data: Dict = None) -> str:
        """Prepare context string for LLM"""
        context = f"""
        Period: {financial_data['period']['start_date']} to {financial_data['period']['end_date']}
        
        Current Period Metrics:
        - Revenue: ${financial_data['current_metrics']['revenue']:,.2f}
        - Expenses: ${financial_data['current_metrics']['expenses']:,.2f}
        - Net Income: ${financial_data['current_metrics']['net_income']:,.2f}
        - Profit Margin: {financial_data['current_metrics']['profit_margin']:.1f}%
        - Cash Balance: ${financial_data['current_metrics']['cash_balance']:,.2f}
        
        Growth vs Previous Period:
        - Revenue Growth: {financial_data['growth_metrics']['revenue_growth']:+.1f}%
        - Expense Growth: {financial_data['growth_metrics']['expense_growth']:+.1f}%
        - Net Income Change: ${financial_data['growth_metrics']['net_income_change']:+,.2f}
        """
        
        if insights_data:
            context += f"""
            
            Variance Analysis Summary:
            - Total Insights: {insights_data.get('total_insights', 0)}
            - Critical Issues: {insights_data.get('severity_summary', {}).get('critical', 0)}
            - High Priority: {insights_data.get('severity_summary', {}).get('high', 0)}
            """
        
        return context
    
    def _parse_bulleted_response(self, response: str) -> List[str]:
        """Parse bulleted response into list"""
        lines = response.strip().split('\n')
        bullets = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                bullets.append(line[1:].strip())
            elif line and bullets:  # Continuation of previous bullet
                bullets[-1] += " " + line
        
        return bullets if bullets else [response]
    
    def _group_variances(self, variances: List[Dict]) -> Dict[str, List[Dict]]:
        """Group variances by type"""
        grouped = {}
        for variance in variances:
            var_type = variance.get('variance_type', 'unknown')
            if var_type not in grouped:
                grouped[var_type] = []
            grouped[var_type].append(variance)
        return grouped
    
    def _generate_variance_type_explanation(self, variance_type: str, variances: List[Dict]) -> str:
        """Generate explanation for specific variance type"""
        count = len(variances)
        high_severity = len([v for v in variances if v['severity'] in ['critical', 'high']])
        
        if variance_type == 'budget_variance':
            return f"Budget variance analysis identified {count} accounts with significant deviations, including {high_severity} requiring immediate attention."
        elif variance_type == 'trend_variance':
            return f"Trend analysis detected {count} accounts deviating from expected patterns, with {high_severity} showing concerning directional changes."
        elif variance_type == 'outlier_variance':
            return f"Statistical analysis flagged {count} transaction outliers, with {high_severity} representing potential anomalies requiring investigation."
        else:
            return f"{variance_type.replace('_', ' ').title()} analysis identified {count} items requiring review."
    
    def _generate_upward_trend_narrative(self, trends: List[Dict]) -> str:
        """Generate narrative for upward trends"""
        accounts = [t['account_name'] for t in trends[:3]]  # Top 3
        return f"Strong upward trends identified in {', '.join(accounts)}, indicating positive momentum in these areas."
    
    def _generate_downward_trend_narrative(self, trends: List[Dict]) -> str:
        """Generate narrative for downward trends"""
        accounts = [t['account_name'] for t in trends[:3]]  # Top 3
        return f"Declining trends detected in {', '.join(accounts)}, requiring management attention to reverse negative trajectory."
    
    def _generate_volatility_narrative(self, trends: List[Dict]) -> str:
        """Generate narrative for volatile accounts"""
        count = len(trends)
        return f"High volatility observed in {count} accounts, suggesting unstable performance patterns that may impact predictability."
    
    def _calculate_confidence_score(self, financial_data: Dict, insights_data: Dict) -> float:
        """Calculate confidence score based on data quality and completeness"""
        score = 0.5  # Base score
        
        # Data completeness
        if financial_data['current_metrics']['revenue'] > 0:
            score += 0.2
        if financial_data['account_balances']:
            score += 0.1
        if insights_data and insights_data.get('total_insights', 0) > 0:
            score += 0.2
        
        return min(1.0, score)
    
    def _get_data_sources(self, financial_data: Dict, insights_data: Dict) -> List[str]:
        """Get list of data sources used"""
        sources = ["QuickBooks General Ledger", "Financial Account Balances"]
        
        if insights_data:
            sources.extend(["Variance Analysis Engine", "Trend Analysis"])
        
        return sources
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are a senior financial analyst providing professional commentary on financial performance. 
        Your analysis should be data-driven, actionable, and written in clear business language suitable for executives and stakeholders. 
        Focus on insights that drive business decisions and highlight both opportunities and risks."""
    
    def _get_analysis_prompt_template(self) -> str:
        """Get analysis prompt template"""
        return """Based on the provided financial data, please analyze the {analysis_type} and provide:
        1. Key findings and metrics
        2. Comparison to expectations/benchmarks
        3. Business implications
        4. Specific recommendations
        
        Financial Data: {financial_context}"""
    
    def _get_variance_prompt_template(self) -> str:
        """Get variance analysis prompt template"""
        return """Analyze the following variance data and provide management commentary:
        
        Variance Data: {variance_data}
        
        For each significant variance, explain:
        1. The nature and magnitude of the variance
        2. Potential causes and business drivers
        3. Impact on operations and financial performance
        4. Recommended management actions"""
    
    def _get_trend_prompt_template(self) -> str:
        """Get trend analysis prompt template"""
        return """Review the trend analysis data and provide insights on:
        
        Trend Data: {trend_data}
        
        1. Significant trend patterns and their implications
        2. Accounts showing strong positive or negative momentum
        3. Volatility concerns and risk factors
        4. Strategic recommendations based on trend patterns"""


# Convenience functions
def generate_commentary(start_date: str, end_date: str, 
                       llm_provider: str = "openai", 
                       model: str = "gpt-4") -> FinancialCommentary:
    """
    Generate comprehensive financial commentary
    
    Args:
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
        llm_provider: LLM provider to use
        model: Model name
        
    Returns:
        FinancialCommentary object
    """
    engine = LLMCommentaryEngine(llm_provider=llm_provider, model=model)
    return engine.generate_comprehensive_commentary(start_date, end_date)

def generate_mock_commentary(start_date: str, end_date: str) -> FinancialCommentary:
    """Generate mock commentary for testing without LLM API calls"""
    return FinancialCommentary(
        executive_summary="Strong financial performance with controlled growth and maintained profitability. Key focus areas include cash flow optimization and strategic investments.",
        performance_analysis=[
            "Revenue growth of 12% demonstrates strong market position and effective sales strategies",
            "Expense management remains disciplined with 8% growth, maintaining healthy profit margins",
            "Cash position strengthened by improved collections and working capital management"
        ],
        variance_commentary=[
            "Budget variances within acceptable ranges with revenue slightly exceeding targets",
            "Operating expense variances require attention in marketing and professional services categories"
        ],
        trend_insights=[
            "Positive revenue trends across core business lines indicate sustainable growth",
            "Expense trends remain well-controlled with opportunities for optimization"
        ],
        risk_assessment="Overall risk level: LOW. Strong liquidity position with adequate cash reserves. Monitor customer concentration and market competition.",
        opportunities=[
            "Expand into high-margin service offerings based on current capabilities",
            "Optimize operational efficiency through process automation",
            "Strategic partnerships to accelerate growth in emerging markets"
        ],
        recommendations=[
            "Implement enhanced cash flow forecasting for better liquidity management",
            "Review pricing strategies to maintain competitive positioning",
            "Invest in technology infrastructure to support scaling operations",
            "Develop contingency plans for potential market volatility"
        ],
        confidence_score=0.85,
        data_sources=["QuickBooks General Ledger", "Variance Analysis", "Trend Analysis"],
        generated_at=datetime.now()
    )


if __name__ == "__main__":
    # Example usage
    from datetime import datetime, timedelta
    
    # Generate commentary for last 30 days
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    print(f"Generating financial commentary for {start_date} to {end_date}")
    
    try:
        # Try with actual LLM
        commentary = generate_commentary(start_date, end_date)
        print("LLM Commentary Generated Successfully")
    except Exception as e:
        print(f"LLM failed, using mock: {e}")
        # Fallback to mock commentary
        commentary = generate_mock_commentary(start_date, end_date)
    
    print(f"\nExecutive Summary:\n{commentary.executive_summary}")
    print(f"\nConfidence Score: {commentary.confidence_score:.2f}")
    print(f"\nRecommendations:")
    for i, rec in enumerate(commentary.recommendations, 1):
        print(f"{i}. {rec}")