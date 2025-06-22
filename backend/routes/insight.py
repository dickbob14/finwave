"""
Insight API routes for variance analysis and financial intelligence
Handles WHY-questions and provides data-driven explanations
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from insights.variance_analyzer import generate_financial_insights, VarianceAnalyzer, InsightEngine
from insights.llm_commentary import LLMCommentaryEngine, generate_mock_commentary
from database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insight", tags=["insights"])

class InsightRequest(BaseModel):
    """Request model for insight analysis"""
    question: str
    start_date: str
    end_date: str
    context: Optional[Dict[str, Any]] = None
    include_recommendations: bool = True

class VarianceExplanationRequest(BaseModel):
    """Request model for variance explanation"""
    metric: str
    expected_value: float
    actual_value: float
    period: str
    context: Optional[Dict[str, Any]] = None

@router.post("/analyze")
async def analyze_financial_question(request: InsightRequest):
    """
    Analyze financial questions and provide data-driven insights
    
    Handles WHY-questions about financial performance with variance analysis
    """
    try:
        # Validate dates
        datetime.fromisoformat(request.start_date)
        datetime.fromisoformat(request.end_date)
        
        # Generate comprehensive insights
        insights_data = generate_financial_insights(request.start_date, request.end_date)
        
        # Analyze the specific question
        question_analysis = await _analyze_question(
            request.question, 
            insights_data, 
            request.start_date, 
            request.end_date,
            request.context
        )
        
        return {
            "question": request.question,
            "period": {"start_date": request.start_date, "end_date": request.end_date},
            "analysis": question_analysis,
            "supporting_data": {
                "variance_count": len(insights_data.get('variances', [])),
                "trend_count": len(insights_data.get('trends', [])),
                "anomaly_count": len(insights_data.get('anomalies', [])),
                "confidence_score": question_analysis.get('confidence_score', 0.7)
            },
            "recommendations": question_analysis.get('recommendations', []) if request.include_recommendations else [],
            "generated_at": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Insight analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Insight analysis failed")

@router.get("/variance")
async def get_variance_analysis(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    severity_filter: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    variance_type: Optional[str] = Query(None, description="Filter by type (budget, trend, seasonal, outlier, ratio)")
):
    """
    Get comprehensive variance analysis for the specified period
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate insights
        insights_data = generate_financial_insights(start_date, end_date)
        
        # Filter results
        variances = insights_data.get('variances', [])
        
        if severity_filter:
            variances = [v for v in variances if v.get('severity') == severity_filter.lower()]
        
        if variance_type:
            variances = [v for v in variances if v.get('variance_type') == variance_type.lower()]
        
        # Group variances by type and severity
        grouped_variances = _group_variances_by_type(variances)
        severity_summary = _summarize_by_severity(variances)
        
        # Generate executive summary
        executive_summary = _generate_variance_executive_summary(variances, insights_data)
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "summary": {
                "total_variances": len(variances),
                "by_severity": severity_summary,
                "by_type": {vtype: len(vars) for vtype, vars in grouped_variances.items()},
                "executive_summary": executive_summary
            },
            "variances": variances,
            "grouped_variances": grouped_variances,
            "insights": insights_data.get('executive_summary', {}),
            "generated_at": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Variance analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Variance analysis failed")

@router.get("/trends")
async def get_trend_analysis(
    lookback_months: int = Query(12, description="Number of months to analyze"),
    trend_direction: Optional[str] = Query(None, description="Filter by direction (increasing, decreasing, volatile, stable)")
):
    """
    Get trend analysis for accounts over the specified lookback period
    """
    try:
        analyzer = VarianceAnalyzer()
        trends = analyzer.analyze_trends(lookback_months)
        
        # Filter by direction if specified
        if trend_direction:
            trends = [t for t in trends if t.trend_direction == trend_direction.lower()]
        
        # Categorize trends
        categorized_trends = {
            'strong_growth': [t for t in trends if t.trend_direction == 'increasing' and t.trend_strength > 0.7],
            'moderate_growth': [t for t in trends if t.trend_direction == 'increasing' and 0.3 < t.trend_strength <= 0.7],
            'declining': [t for t in trends if t.trend_direction == 'decreasing' and t.trend_strength > 0.5],
            'volatile': [t for t in trends if t.trend_direction == 'volatile'],
            'stable': [t for t in trends if t.trend_direction == 'stable']
        }
        
        # Convert trends to dict format
        trends_dict = [_trend_to_dict(t) for t in trends]
        categorized_dict = {k: [_trend_to_dict(t) for t in v] for k, v in categorized_trends.items()}
        
        return {
            "lookback_period_months": lookback_months,
            "summary": {
                "total_accounts_analyzed": len(trends),
                "strong_growth_accounts": len(categorized_trends['strong_growth']),
                "declining_accounts": len(categorized_trends['declining']),
                "volatile_accounts": len(categorized_trends['volatile']),
                "stable_accounts": len(categorized_trends['stable'])
            },
            "trends": trends_dict,
            "categorized_trends": categorized_dict,
            "insights": _generate_trend_insights(categorized_trends),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Trend analysis failed")

@router.get("/anomalies")
async def get_anomaly_detection(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    sensitivity: float = Query(2.0, description="Z-score threshold for anomaly detection (higher = less sensitive)")
):
    """
    Detect statistical anomalies in financial data
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Validate sensitivity
        if sensitivity < 1.0 or sensitivity > 5.0:
            raise HTTPException(status_code=400, detail="Sensitivity must be between 1.0 and 5.0")
        
        analyzer = VarianceAnalyzer()
        anomalies = analyzer.detect_anomalies(start_date, end_date, sensitivity)
        
        # Group by severity
        critical_anomalies = [a for a in anomalies if a.severity.value == 'critical']
        high_anomalies = [a for a in anomalies if a.severity.value == 'high']
        medium_anomalies = [a for a in anomalies if a.severity.value == 'medium']
        
        # Convert to dict format
        anomalies_dict = [_variance_to_dict(a) for a in anomalies]
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "sensitivity_threshold": sensitivity,
            "summary": {
                "total_anomalies": len(anomalies),
                "critical_anomalies": len(critical_anomalies),
                "high_priority_anomalies": len(high_anomalies),
                "medium_priority_anomalies": len(medium_anomalies)
            },
            "anomalies": anomalies_dict,
            "critical_attention": [_variance_to_dict(a) for a in critical_anomalies[:5]],  # Top 5 critical
            "insights": _generate_anomaly_insights(anomalies),
            "generated_at": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail="Anomaly detection failed")

@router.post("/explain")
async def explain_variance(request: VarianceExplanationRequest):
    """
    Explain a specific variance with detailed analysis and recommendations
    """
    try:
        # Calculate variance metrics
        variance_amount = request.actual_value - request.expected_value
        variance_percentage = (variance_amount / request.expected_value * 100) if request.expected_value != 0 else 0
        
        # Generate explanation using LLM or rule-based system
        explanation = await _generate_variance_explanation(
            request.metric,
            request.expected_value,
            request.actual_value,
            variance_amount,
            variance_percentage,
            request.period,
            request.context
        )
        
        return {
            "metric": request.metric,
            "period": request.period,
            "variance_analysis": {
                "expected_value": request.expected_value,
                "actual_value": request.actual_value,
                "variance_amount": variance_amount,
                "variance_percentage": variance_percentage,
                "severity": _get_variance_severity(abs(variance_percentage))
            },
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Variance explanation failed: {e}")
        raise HTTPException(status_code=500, detail="Variance explanation failed")

@router.get("/dashboard")
async def get_insights_dashboard(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """
    Get comprehensive insights dashboard data
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate comprehensive insights
        insights_data = generate_financial_insights(start_date, end_date)
        
        # Get trend analysis
        analyzer = VarianceAnalyzer()
        trends = analyzer.analyze_trends(6)  # 6 months lookback
        
        # Prepare dashboard data
        dashboard_data = {
            "period": {"start_date": start_date, "end_date": end_date},
            "overview": {
                "total_insights": insights_data.get('total_insights', 0),
                "critical_issues": insights_data.get('severity_summary', {}).get('critical', 0),
                "high_priority": insights_data.get('severity_summary', {}).get('high', 0),
                "trending_accounts": len([t for t in trends if abs(t.trend_strength) > 0.5]),
                "anomalies_detected": len(insights_data.get('anomalies', []))
            },
            "top_concerns": [
                {
                    "title": v.get('description', ''),
                    "severity": v.get('severity', ''),
                    "account": v.get('account_name', ''),
                    "variance_percentage": v.get('variance_percentage', 0)
                }
                for v in insights_data.get('variances', [])[:5]  # Top 5
            ],
            "trending_accounts": [
                {
                    "account_name": t.account_name,
                    "trend_direction": t.trend_direction,
                    "trend_strength": t.trend_strength,
                    "projections": {k: float(v) for k, v in t.projections.items()}
                }
                for t in trends[:10]  # Top 10 trending
            ],
            "executive_summary": insights_data.get('executive_summary', {}),
            "quick_actions": _generate_quick_actions(insights_data),
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        raise HTTPException(status_code=500, detail="Dashboard generation failed")

# Helper functions
async def _analyze_question(question: str, insights_data: Dict, start_date: str, end_date: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Analyze financial question and provide data-driven answer"""
    question_lower = question.lower()
    
    # Question type detection
    if any(word in question_lower for word in ['why', 'what caused', 'reason for', 'explain']):
        return await _handle_why_question(question, insights_data, start_date, end_date, context)
    elif any(word in question_lower for word in ['how much', 'what is', 'show me']):
        return await _handle_what_question(question, insights_data, start_date, end_date, context)
    elif any(word in question_lower for word in ['predict', 'forecast', 'what will', 'next month']):
        return await _handle_prediction_question(question, insights_data, start_date, end_date, context)
    else:
        return await _handle_general_question(question, insights_data, start_date, end_date, context)

async def _handle_why_question(question: str, insights_data: Dict, start_date: str, end_date: str, context: Optional[Dict]) -> Dict[str, Any]:
    """Handle WHY-type questions with variance analysis"""
    variances = insights_data.get('variances', [])
    trends = insights_data.get('trends', [])
    
    # Look for relevant variances
    relevant_variances = []
    for variance in variances:
        if any(word in variance.get('account_name', '').lower() for word in question.lower().split()):
            relevant_variances.append(variance)
    
    # Generate explanation
    if relevant_variances:
        primary_variance = relevant_variances[0]
        explanation = f"The variance in {primary_variance.get('account_name')} is primarily due to a {primary_variance.get('variance_percentage', 0):.1f}% difference from expected values."
        
        drivers = []
        for variance in relevant_variances[:3]:
            drivers.append({
                "factor": variance.get('account_name'),
                "impact": variance.get('variance_amount', 0),
                "description": variance.get('description', '')
            })
    else:
        explanation = "Based on the available data, no significant variances were detected that directly relate to your question."
        drivers = []
    
    return {
        "answer_type": "variance_analysis",
        "explanation": explanation,
        "drivers": drivers,
        "confidence_score": 0.8 if relevant_variances else 0.3,
        "supporting_variances": relevant_variances[:5],
        "recommendations": _generate_question_recommendations(question, relevant_variances)
    }

async def _handle_what_question(question: str, insights_data: Dict, start_date: str, end_date: str, context: Optional[Dict]) -> Dict[str, Any]:
    """Handle WHAT-type questions with data retrieval"""
    # This would retrieve specific metrics based on the question
    return {
        "answer_type": "data_retrieval",
        "explanation": "Data retrieval functionality not yet implemented",
        "confidence_score": 0.5,
        "recommendations": ["Use the variance analysis endpoint for detailed metrics"]
    }

async def _handle_prediction_question(question: str, insights_data: Dict, start_date: str, end_date: str, context: Optional[Dict]) -> Dict[str, Any]:
    """Handle prediction/forecast questions"""
    trends = insights_data.get('trends', [])
    
    # Simple trend-based predictions
    projections = []
    for trend in trends[:5]:  # Top 5 trends
        if trend.get('projections'):
            projections.append({
                "account": trend.get('account_name'),
                "next_month_projection": trend.get('projections', {}).get('next_month', 0),
                "confidence": trend.get('trend_strength', 0)
            })
    
    return {
        "answer_type": "prediction",
        "explanation": f"Based on trend analysis of {len(trends)} accounts, here are the projections:",
        "projections": projections,
        "confidence_score": 0.7,
        "recommendations": ["Monitor these trends closely as predictions are based on historical patterns"]
    }

async def _handle_general_question(question: str, insights_data: Dict, start_date: str, end_date: str, context: Optional[Dict]) -> Dict[str, Any]:
    """Handle general financial questions"""
    executive_summary = insights_data.get('executive_summary', {})
    
    return {
        "answer_type": "general_analysis",
        "explanation": "For general financial insights, please refer to the executive summary and variance analysis.",
        "executive_summary": executive_summary,
        "confidence_score": 0.6,
        "recommendations": ["Use more specific questions for detailed analysis"]
    }

def _group_variances_by_type(variances: List[Dict]) -> Dict[str, List[Dict]]:
    """Group variances by type"""
    grouped = {}
    for variance in variances:
        vtype = variance.get('variance_type', 'unknown')
        if vtype not in grouped:
            grouped[vtype] = []
        grouped[vtype].append(variance)
    return grouped

def _summarize_by_severity(variances: List[Dict]) -> Dict[str, int]:
    """Summarize variances by severity"""
    summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for variance in variances:
        severity = variance.get('severity', 'low')
        if severity in summary:
            summary[severity] += 1
    return summary

def _generate_variance_executive_summary(variances: List[Dict], insights_data: Dict) -> str:
    """Generate executive summary for variance analysis"""
    total_variances = len(variances)
    critical_count = len([v for v in variances if v.get('severity') == 'critical'])
    
    if critical_count > 0:
        return f"Identified {total_variances} variances with {critical_count} requiring immediate attention. Focus on critical items first."
    elif total_variances > 0:
        return f"Detected {total_variances} variances within acceptable ranges. Regular monitoring recommended."
    else:
        return "No significant variances detected. Financial performance is tracking to expectations."

def _trend_to_dict(trend) -> Dict[str, Any]:
    """Convert TrendAnalysis object to dictionary"""
    return {
        'account_id': trend.account_id,
        'account_name': trend.account_name,
        'trend_direction': trend.trend_direction,
        'trend_strength': trend.trend_strength,
        'seasonal_pattern': trend.seasonal_pattern,
        'volatility_score': trend.volatility_score,
        'data_points': trend.data_points,
        'projections': {k: float(v) for k, v in trend.projections.items()}
    }

def _variance_to_dict(variance) -> Dict[str, Any]:
    """Convert VarianceInsight object to dictionary"""
    return {
        'variance_type': variance.variance_type.value,
        'severity': variance.severity.value,
        'account_id': variance.account_id,
        'account_name': variance.account_name,
        'expected_value': float(variance.expected_value),
        'actual_value': float(variance.actual_value),
        'variance_amount': float(variance.variance_amount),
        'variance_percentage': variance.variance_percentage,
        'description': variance.description,
        'recommendations': variance.recommendations,
        'confidence_score': variance.confidence_score,
        'metadata': variance.metadata
    }

def _generate_trend_insights(categorized_trends: Dict) -> List[str]:
    """Generate insights from trend analysis"""
    insights = []
    
    strong_growth = len(categorized_trends['strong_growth'])
    declining = len(categorized_trends['declining'])
    volatile = len(categorized_trends['volatile'])
    
    if strong_growth > 0:
        insights.append(f"{strong_growth} accounts showing strong growth momentum")
    if declining > 0:
        insights.append(f"{declining} accounts in decline requiring attention")
    if volatile > 0:
        insights.append(f"{volatile} accounts showing high volatility")
    
    return insights

def _generate_anomaly_insights(anomalies: List) -> List[str]:
    """Generate insights from anomaly detection"""
    insights = []
    
    if len(anomalies) == 0:
        insights.append("No statistical anomalies detected in the analysis period")
    elif len(anomalies) < 5:
        insights.append(f"Small number of anomalies ({len(anomalies)}) detected - investigate outliers")
    else:
        insights.append(f"Multiple anomalies ({len(anomalies)}) detected - systematic review recommended")
    
    return insights

async def _generate_variance_explanation(metric: str, expected: float, actual: float, 
                                       variance_amount: float, variance_pct: float, 
                                       period: str, context: Optional[Dict]) -> Dict[str, Any]:
    """Generate detailed variance explanation"""
    # Rule-based explanation system
    severity = _get_variance_severity(abs(variance_pct))
    
    if abs(variance_pct) < 5:
        explanation = f"The {metric} variance of {variance_pct:.1f}% is within acceptable tolerance."
    elif variance_pct > 0:
        explanation = f"The {metric} is {variance_pct:.1f}% above expectations, indicating potential overperformance or budget underestimation."
    else:
        explanation = f"The {metric} is {abs(variance_pct):.1f}% below expectations, requiring investigation into underperformance factors."
    
    # Generate potential causes
    potential_causes = _generate_potential_causes(metric, variance_pct, context)
    
    # Generate recommendations
    recommendations = _generate_variance_recommendations(metric, variance_pct, severity)
    
    return {
        "explanation": explanation,
        "severity": severity,
        "potential_causes": potential_causes,
        "recommendations": recommendations,
        "confidence_score": 0.8
    }

def _get_variance_severity(variance_percentage: float) -> str:
    """Determine variance severity level"""
    abs_variance = abs(variance_percentage)
    
    if abs_variance >= 50:
        return 'critical'
    elif abs_variance >= 25:
        return 'high'
    elif abs_variance >= 15:
        return 'medium'
    else:
        return 'low'

def _generate_potential_causes(metric: str, variance_pct: float, context: Optional[Dict]) -> List[str]:
    """Generate potential causes for variance"""
    causes = []
    
    if 'revenue' in metric.lower():
        if variance_pct > 0:
            causes.extend(["Increased sales volume", "Higher pricing", "New customer acquisition"])
        else:
            causes.extend(["Reduced demand", "Lost customers", "Pricing pressure"])
    elif 'expense' in metric.lower():
        if variance_pct > 0:
            causes.extend(["Increased operational costs", "Higher material prices", "Expanded activities"])
        else:
            causes.extend(["Cost reduction initiatives", "Operational efficiency", "Reduced activity levels"])
    
    return causes

def _generate_variance_recommendations(metric: str, variance_pct: float, severity: str) -> List[str]:
    """Generate recommendations for variance"""
    recommendations = []
    
    if severity in ['critical', 'high']:
        recommendations.append("Immediate investigation required")
        recommendations.append("Review underlying business drivers")
    
    if 'revenue' in metric.lower() and variance_pct < 0:
        recommendations.append("Analyze sales pipeline and customer retention")
    elif 'expense' in metric.lower() and variance_pct > 0:
        recommendations.append("Review cost controls and approval processes")
    
    return recommendations

def _generate_question_recommendations(question: str, variances: List[Dict]) -> List[str]:
    """Generate recommendations based on question and variances"""
    recommendations = []
    
    if variances:
        recommendations.append("Review the identified variances for root cause analysis")
        recommendations.append("Consider implementing monitoring for these accounts")
    else:
        recommendations.append("No significant variances found - performance is tracking expectations")
    
    return recommendations

def _generate_quick_actions(insights_data: Dict) -> List[Dict[str, str]]:
    """Generate quick action items from insights"""
    actions = []
    
    critical_variances = [v for v in insights_data.get('variances', []) if v.get('severity') == 'critical']
    
    for variance in critical_variances[:3]:  # Top 3 critical
        actions.append({
            "title": f"Investigate {variance.get('account_name', 'Unknown')} variance",
            "description": variance.get('description', ''),
            "priority": "critical",
            "estimated_effort": "1-2 hours"
        })
    
    return actions

@router.get("/status")
async def get_insight_status():
    """
    Get insight system status and capabilities
    """
    # Check database connectivity
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
            db_connected = True
    except Exception:
        db_connected = False
    
    # Check LLM configuration
    import os
    llm_configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "database_connected": db_connected,
        "llm_configured": llm_configured,
        "capabilities": [
            "Variance Analysis",
            "Trend Detection", 
            "Anomaly Detection",
            "Question Analysis",
            "Predictive Insights"
        ],
        "variance_types": ["budget", "trend", "seasonal", "outlier", "ratio"],
        "severity_levels": ["critical", "high", "medium", "low"],
        "supported_questions": [
            "Why are expenses higher this month?",
            "What caused the revenue variance?",
            "Which accounts are trending upward?",
            "Are there any anomalies in the data?"
        ],
        "checked_at": datetime.now().isoformat()
    }