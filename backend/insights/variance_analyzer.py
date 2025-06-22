"""
Advanced variance analysis and insight detection system
Leverages statistical analysis and pattern recognition for financial anomaly detection
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from dataclasses import dataclass
import json
import statistics
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract, text

from database import get_db_session
from models.financial import GeneralLedger, Account, IngestionHistory

logger = logging.getLogger(__name__)

class VarianceType(Enum):
    """Types of variance detected"""
    BUDGET_VARIANCE = "budget_variance"
    SEASONAL_VARIANCE = "seasonal_variance" 
    TREND_VARIANCE = "trend_variance"
    OUTLIER_VARIANCE = "outlier_variance"
    RATIO_VARIANCE = "ratio_variance"

class SeverityLevel(Enum):
    """Severity levels for variances"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class VarianceInsight:
    """Container for variance analysis insights"""
    variance_type: VarianceType
    severity: SeverityLevel
    account_id: str
    account_name: str
    expected_value: Decimal
    actual_value: Decimal
    variance_amount: Decimal
    variance_percentage: float
    description: str
    recommendations: List[str]
    confidence_score: float
    metadata: Dict[str, Any]

@dataclass
class TrendAnalysis:
    """Container for trend analysis results"""
    account_id: str
    account_name: str
    trend_direction: str  # "increasing", "decreasing", "stable", "volatile"
    trend_strength: float  # 0-1, how strong the trend is
    seasonal_pattern: bool
    volatility_score: float
    data_points: List[Dict]
    projections: Dict[str, Decimal]

class VarianceAnalyzer:
    """Advanced variance analysis engine"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize variance analyzer
        
        Args:
            confidence_threshold: Minimum confidence score for insights (0-1)
        """
        self.confidence_threshold = confidence_threshold
        self.variance_thresholds = {
            SeverityLevel.LOW: 0.05,      # 5%
            SeverityLevel.MEDIUM: 0.15,   # 15%
            SeverityLevel.HIGH: 0.25,     # 25%
            SeverityLevel.CRITICAL: 0.50  # 50%
        }
    
    def analyze_variances(self, start_date: str, end_date: str, include_budget: bool = True) -> List[VarianceInsight]:
        """
        Comprehensive variance analysis for the given period
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format  
            include_budget: Whether to include budget variance analysis
            
        Returns:
            List of variance insights ordered by severity
        """
        insights = []
        
        with get_db_session() as db:
            # Get account-level data for analysis
            account_data = self._get_account_analysis_data(db, start_date, end_date)
            
            for account_id, data in account_data.items():
                # Budget variance analysis
                if include_budget:
                    budget_insights = self._analyze_budget_variance(data)
                    insights.extend(budget_insights)
                
                # Trend variance analysis
                trend_insights = self._analyze_trend_variance(db, account_id, end_date)
                insights.extend(trend_insights)
                
                # Seasonal variance analysis
                seasonal_insights = self._analyze_seasonal_variance(db, account_id, start_date, end_date)
                insights.extend(seasonal_insights)
                
                # Outlier detection
                outlier_insights = self._detect_outliers(db, account_id, start_date, end_date)
                insights.extend(outlier_insights)
            
            # Financial ratio variance analysis
            ratio_insights = self._analyze_ratio_variances(db, start_date, end_date)
            insights.extend(ratio_insights)
        
        # Filter by confidence threshold and sort by severity
        filtered_insights = [i for i in insights if i.confidence_score >= self.confidence_threshold]
        return sorted(filtered_insights, key=lambda x: (x.severity.value, -x.confidence_score), reverse=True)
    
    def analyze_trends(self, lookback_months: int = 12) -> List[TrendAnalysis]:
        """
        Analyze trends across accounts for the specified lookback period
        
        Args:
            lookback_months: Number of months to analyze
            
        Returns:
            List of trend analyses
        """
        trends = []
        end_date = datetime.now().date()
        start_date = (end_date - timedelta(days=lookback_months * 30)).isoformat()
        end_date = end_date.isoformat()
        
        with get_db_session() as db:
            accounts = self._get_active_accounts(db, start_date, end_date)
            
            for account in accounts:
                trend = self._analyze_account_trend(db, account['account_id'], start_date, end_date)
                if trend:
                    trends.append(trend)
        
        return trends
    
    def detect_anomalies(self, start_date: str, end_date: str, sensitivity: float = 2.0) -> List[VarianceInsight]:
        """
        Detect statistical anomalies in financial data
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            sensitivity: Z-score threshold for anomaly detection
            
        Returns:
            List of anomaly insights
        """
        anomalies = []
        
        with get_db_session() as db:
            accounts = self._get_active_accounts(db, start_date, end_date)
            
            for account in accounts:
                account_anomalies = self._detect_account_anomalies(
                    db, account['account_id'], start_date, end_date, sensitivity
                )
                anomalies.extend(account_anomalies)
        
        return sorted(anomalies, key=lambda x: x.confidence_score, reverse=True)
    
    def _get_account_analysis_data(self, db: Session, start_date: str, end_date: str) -> Dict[str, Dict]:
        """Get aggregated account data for analysis"""
        results = db.query(
            GeneralLedger.account_id,
            GeneralLedger.account_name,
            GeneralLedger.account_type,
            func.sum(GeneralLedger.debit_amount).label('total_debits'),
            func.sum(GeneralLedger.credit_amount).label('total_credits'),
            func.sum(GeneralLedger.amount).label('net_amount'),
            func.count().label('transaction_count'),
            func.avg(GeneralLedger.amount).label('avg_amount'),
            func.stddev(GeneralLedger.amount).label('amount_stddev')
        ).filter(
            and_(
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).group_by(
            GeneralLedger.account_id,
            GeneralLedger.account_name,
            GeneralLedger.account_type
        ).all()
        
        return {
            r.account_id: {
                'account_id': r.account_id,
                'account_name': r.account_name,
                'account_type': r.account_type,
                'total_debits': r.total_debits or Decimal('0'),
                'total_credits': r.total_credits or Decimal('0'),
                'net_amount': r.net_amount or Decimal('0'),
                'transaction_count': r.transaction_count,
                'avg_amount': r.avg_amount or Decimal('0'),
                'amount_stddev': r.amount_stddev or Decimal('0')
            }
            for r in results
        }
    
    def _analyze_budget_variance(self, account_data: Dict) -> List[VarianceInsight]:
        """Analyze budget vs actual variance (simplified - assumes budget exists)"""
        insights = []
        
        # In a real implementation, you'd fetch budget data from database
        # For demo purposes, we'll simulate budget as 10% higher than actual for revenue,
        # 10% lower for expenses
        actual = account_data['net_amount']
        account_type = account_data['account_type']
        
        if account_type in ['Income', 'Revenue']:
            # Revenue accounts - budget should be higher
            budget = actual * Decimal('1.1')
        elif account_type in ['Expense']:
            # Expense accounts - budget should be lower  
            budget = actual * Decimal('0.9')
        else:
            # Skip balance sheet accounts for budget variance
            return insights
        
        if budget != 0:
            variance_amount = actual - budget
            variance_pct = float(variance_amount / budget)
            
            # Determine severity
            severity = self._get_variance_severity(abs(variance_pct))
            
            if severity != SeverityLevel.LOW:  # Only report significant variances
                recommendations = self._get_budget_variance_recommendations(
                    account_type, variance_pct, account_data['account_name']
                )
                
                insight = VarianceInsight(
                    variance_type=VarianceType.BUDGET_VARIANCE,
                    severity=severity,
                    account_id=account_data['account_id'],
                    account_name=account_data['account_name'],
                    expected_value=budget,
                    actual_value=actual,
                    variance_amount=variance_amount,
                    variance_percentage=variance_pct,
                    description=f"Budget variance of {variance_pct:.1%} in {account_data['account_name']}",
                    recommendations=recommendations,
                    confidence_score=0.8,  # High confidence for budget variance
                    metadata={'account_type': account_type, 'transaction_count': account_data['transaction_count']}
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_trend_variance(self, db: Session, account_id: str, end_date: str) -> List[VarianceInsight]:
        """Analyze trend-based variances"""
        insights = []
        
        # Get last 6 months of data for trend analysis
        start_date = (datetime.fromisoformat(end_date) - timedelta(days=180)).date().isoformat()
        
        monthly_data = self._get_monthly_account_data(db, account_id, start_date, end_date)
        
        if len(monthly_data) >= 3:  # Need at least 3 months
            amounts = [float(d['amount']) for d in monthly_data]
            
            # Calculate trend
            trend_strength = self._calculate_trend_strength(amounts)
            expected_current = self._predict_next_value(amounts)
            actual_current = amounts[-1] if amounts else 0
            
            if expected_current != 0:
                variance_pct = (actual_current - expected_current) / abs(expected_current)
                
                if abs(variance_pct) > 0.15:  # 15% threshold for trend variance
                    severity = self._get_variance_severity(abs(variance_pct))
                    
                    account_name = monthly_data[0]['account_name']
                    
                    insight = VarianceInsight(
                        variance_type=VarianceType.TREND_VARIANCE,
                        severity=severity,
                        account_id=account_id,
                        account_name=account_name,
                        expected_value=Decimal(str(expected_current)),
                        actual_value=Decimal(str(actual_current)),
                        variance_amount=Decimal(str(actual_current - expected_current)),
                        variance_percentage=variance_pct,
                        description=f"Trend deviation detected in {account_name}",
                        recommendations=self._get_trend_variance_recommendations(variance_pct, trend_strength),
                        confidence_score=min(0.9, abs(trend_strength)),
                        metadata={'trend_strength': trend_strength, 'months_analyzed': len(monthly_data)}
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_seasonal_variance(self, db: Session, account_id: str, start_date: str, end_date: str) -> List[VarianceInsight]:
        """Analyze seasonal variance patterns"""
        insights = []
        
        # Get same period from previous year for comparison
        current_year = datetime.fromisoformat(end_date).year
        prev_year_start = start_date.replace(str(current_year), str(current_year - 1))
        prev_year_end = end_date.replace(str(current_year), str(current_year - 1))
        
        current_data = self._get_period_account_total(db, account_id, start_date, end_date)
        previous_data = self._get_period_account_total(db, account_id, prev_year_start, prev_year_end)
        
        if current_data and previous_data and previous_data['amount'] != 0:
            current_amount = current_data['amount']
            previous_amount = previous_data['amount']
            variance_pct = float((current_amount - previous_amount) / previous_amount)
            
            if abs(variance_pct) > 0.20:  # 20% threshold for seasonal variance
                severity = self._get_variance_severity(abs(variance_pct))
                
                insight = VarianceInsight(
                    variance_type=VarianceType.SEASONAL_VARIANCE,
                    severity=severity,
                    account_id=account_id,
                    account_name=current_data['account_name'],
                    expected_value=previous_amount,
                    actual_value=current_amount,
                    variance_amount=current_amount - previous_amount,
                    variance_percentage=variance_pct,
                    description=f"Year-over-year seasonal variance in {current_data['account_name']}",
                    recommendations=self._get_seasonal_variance_recommendations(variance_pct),
                    confidence_score=0.75,
                    metadata={'previous_year_amount': float(previous_amount)}
                )
                insights.append(insight)
        
        return insights
    
    def _detect_outliers(self, db: Session, account_id: str, start_date: str, end_date: str) -> List[VarianceInsight]:
        """Detect statistical outliers in transaction amounts"""
        insights = []
        
        # Get individual transactions for outlier detection
        transactions = db.query(
            GeneralLedger.amount,
            GeneralLedger.transaction_date,
            GeneralLedger.description,
            GeneralLedger.account_name
        ).filter(
            and_(
                GeneralLedger.account_id == account_id,
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).all()
        
        if len(transactions) > 10:  # Need sufficient data for outlier detection
            amounts = [float(t.amount) for t in transactions]
            mean_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            if std_amount > 0:
                # Find outliers (more than 2 standard deviations from mean)
                for transaction in transactions:
                    amount = float(transaction.amount)
                    z_score = abs(amount - mean_amount) / std_amount
                    
                    if z_score > 2.5:  # Outlier threshold
                        variance_pct = (amount - mean_amount) / abs(mean_amount) if mean_amount != 0 else 0
                        severity = self._get_variance_severity(abs(variance_pct))
                        
                        insight = VarianceInsight(
                            variance_type=VarianceType.OUTLIER_VARIANCE,
                            severity=severity,
                            account_id=account_id,
                            account_name=transaction.account_name,
                            expected_value=Decimal(str(mean_amount)),
                            actual_value=transaction.amount,
                            variance_amount=transaction.amount - Decimal(str(mean_amount)),
                            variance_percentage=variance_pct,
                            description=f"Statistical outlier detected: {transaction.description}",
                            recommendations=self._get_outlier_recommendations(z_score, transaction.description),
                            confidence_score=min(0.95, z_score / 5),  # Higher z_score = higher confidence
                            metadata={
                                'z_score': z_score,
                                'transaction_date': transaction.transaction_date.isoformat(),
                                'description': transaction.description
                            }
                        )
                        insights.append(insight)
        
        return insights
    
    def _analyze_ratio_variances(self, db: Session, start_date: str, end_date: str) -> List[VarianceInsight]:
        """Analyze financial ratio variances"""
        insights = []
        
        # Calculate key financial ratios
        revenue = self._get_account_type_total(db, ['Income', 'Revenue'], start_date, end_date)
        expenses = self._get_account_type_total(db, ['Expense'], start_date, end_date)
        assets = self._get_account_type_total(db, ['Bank', 'Cash', 'Accounts Receivable', 'Other Current Asset'], start_date, end_date)
        liabilities = self._get_account_type_total(db, ['Accounts Payable', 'Credit Card'], start_date, end_date)
        
        # Profit margin analysis
        if revenue > 0:
            profit_margin = float((revenue - expenses) / revenue)
            expected_margin = 0.15  # Expected 15% profit margin
            
            if abs(profit_margin - expected_margin) > 0.05:  # 5% variance threshold
                variance_pct = (profit_margin - expected_margin) / expected_margin
                severity = self._get_variance_severity(abs(variance_pct))
                
                insight = VarianceInsight(
                    variance_type=VarianceType.RATIO_VARIANCE,
                    severity=severity,
                    account_id="PROFIT_MARGIN",
                    account_name="Profit Margin Ratio",
                    expected_value=Decimal(str(expected_margin)),
                    actual_value=Decimal(str(profit_margin)),
                    variance_amount=Decimal(str(profit_margin - expected_margin)),
                    variance_percentage=variance_pct,
                    description=f"Profit margin variance: {profit_margin:.1%} vs expected {expected_margin:.1%}",
                    recommendations=self._get_ratio_variance_recommendations("profit_margin", profit_margin, expected_margin),
                    confidence_score=0.85,
                    metadata={'ratio_type': 'profit_margin', 'revenue': float(revenue), 'expenses': float(expenses)}
                )
                insights.append(insight)
        
        # Current ratio analysis (simplified)
        if liabilities > 0:
            current_ratio = float(assets / liabilities)
            expected_ratio = 2.0  # Expected current ratio of 2:1
            
            if abs(current_ratio - expected_ratio) > 0.5:  # 0.5 variance threshold
                variance_pct = (current_ratio - expected_ratio) / expected_ratio
                severity = self._get_variance_severity(abs(variance_pct))
                
                insight = VarianceInsight(
                    variance_type=VarianceType.RATIO_VARIANCE,
                    severity=severity,
                    account_id="CURRENT_RATIO",
                    account_name="Current Ratio",
                    expected_value=Decimal(str(expected_ratio)),
                    actual_value=Decimal(str(current_ratio)),
                    variance_amount=Decimal(str(current_ratio - expected_ratio)),
                    variance_percentage=variance_pct,
                    description=f"Current ratio variance: {current_ratio:.2f} vs expected {expected_ratio:.2f}",
                    recommendations=self._get_ratio_variance_recommendations("current_ratio", current_ratio, expected_ratio),
                    confidence_score=0.80,
                    metadata={'ratio_type': 'current_ratio', 'assets': float(assets), 'liabilities': float(liabilities)}
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_account_trend(self, db: Session, account_id: str, start_date: str, end_date: str) -> Optional[TrendAnalysis]:
        """Analyze trend for a specific account"""
        monthly_data = self._get_monthly_account_data(db, account_id, start_date, end_date)
        
        if len(monthly_data) < 3:
            return None
        
        amounts = [float(d['amount']) for d in monthly_data]
        account_name = monthly_data[0]['account_name']
        
        # Calculate trend metrics
        trend_strength = self._calculate_trend_strength(amounts)
        trend_direction = self._determine_trend_direction(amounts)
        volatility = self._calculate_volatility(amounts)
        seasonal_pattern = self._detect_seasonal_pattern(amounts)
        
        # Generate projections
        next_month = self._predict_next_value(amounts)
        next_quarter = self._predict_future_value(amounts, 3)
        
        return TrendAnalysis(
            account_id=account_id,
            account_name=account_name,
            trend_direction=trend_direction,
            trend_strength=abs(trend_strength),
            seasonal_pattern=seasonal_pattern,
            volatility_score=volatility,
            data_points=[{'month': d['month'], 'amount': float(d['amount'])} for d in monthly_data],
            projections={
                'next_month': Decimal(str(next_month)),
                'next_quarter': Decimal(str(next_quarter))
            }
        )
    
    def _detect_account_anomalies(self, db: Session, account_id: str, start_date: str, end_date: str, sensitivity: float) -> List[VarianceInsight]:
        """Detect anomalies using Z-score analysis"""
        insights = []
        
        # Get daily aggregated data
        daily_data = self._get_daily_account_data(db, account_id, start_date, end_date)
        
        if len(daily_data) > 7:  # Need at least a week of data
            amounts = [float(d['amount']) for d in daily_data]
            mean_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            if std_amount > 0:
                for day_data in daily_data:
                    amount = float(day_data['amount'])
                    z_score = abs(amount - mean_amount) / std_amount
                    
                    if z_score > sensitivity:
                        variance_pct = (amount - mean_amount) / abs(mean_amount) if mean_amount != 0 else 0
                        severity = self._get_variance_severity(abs(variance_pct))
                        
                        insight = VarianceInsight(
                            variance_type=VarianceType.OUTLIER_VARIANCE,
                            severity=severity,
                            account_id=account_id,
                            account_name=day_data['account_name'],
                            expected_value=Decimal(str(mean_amount)),
                            actual_value=Decimal(str(amount)),
                            variance_amount=Decimal(str(amount - mean_amount)),
                            variance_percentage=variance_pct,
                            description=f"Daily anomaly detected on {day_data['date']}",
                            recommendations=self._get_anomaly_recommendations(z_score),
                            confidence_score=min(0.95, z_score / 4),
                            metadata={
                                'z_score': z_score,
                                'date': day_data['date'],
                                'sensitivity': sensitivity
                            }
                        )
                        insights.append(insight)
        
        return insights
    
    # Helper methods for data retrieval
    def _get_active_accounts(self, db: Session, start_date: str, end_date: str) -> List[Dict]:
        """Get list of active accounts in the period"""
        results = db.query(
            GeneralLedger.account_id,
            GeneralLedger.account_name,
            GeneralLedger.account_type
        ).filter(
            and_(
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).distinct().all()
        
        return [
            {
                'account_id': r.account_id,
                'account_name': r.account_name,
                'account_type': r.account_type
            }
            for r in results
        ]
    
    def _get_monthly_account_data(self, db: Session, account_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get monthly aggregated data for an account"""
        results = db.query(
            extract('year', GeneralLedger.transaction_date).label('year'),
            extract('month', GeneralLedger.transaction_date).label('month'),
            func.sum(GeneralLedger.amount).label('amount'),
            GeneralLedger.account_name
        ).filter(
            and_(
                GeneralLedger.account_id == account_id,
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).group_by(
            extract('year', GeneralLedger.transaction_date),
            extract('month', GeneralLedger.transaction_date),
            GeneralLedger.account_name
        ).order_by(
            extract('year', GeneralLedger.transaction_date),
            extract('month', GeneralLedger.transaction_date)
        ).all()
        
        return [
            {
                'year': int(r.year),
                'month': int(r.month),
                'amount': r.amount or Decimal('0'),
                'account_name': r.account_name
            }
            for r in results
        ]
    
    def _get_daily_account_data(self, db: Session, account_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Get daily aggregated data for an account"""
        results = db.query(
            func.date(GeneralLedger.transaction_date).label('date'),
            func.sum(GeneralLedger.amount).label('amount'),
            GeneralLedger.account_name
        ).filter(
            and_(
                GeneralLedger.account_id == account_id,
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).group_by(
            func.date(GeneralLedger.transaction_date),
            GeneralLedger.account_name
        ).order_by(
            func.date(GeneralLedger.transaction_date)
        ).all()
        
        return [
            {
                'date': r.date.isoformat(),
                'amount': r.amount or Decimal('0'),
                'account_name': r.account_name
            }
            for r in results
        ]
    
    def _get_period_account_total(self, db: Session, account_id: str, start_date: str, end_date: str) -> Optional[Dict]:
        """Get total for an account in a specific period"""
        result = db.query(
            func.sum(GeneralLedger.amount).label('amount'),
            GeneralLedger.account_name
        ).filter(
            and_(
                GeneralLedger.account_id == account_id,
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).group_by(GeneralLedger.account_name).first()
        
        if result:
            return {
                'amount': result.amount or Decimal('0'),
                'account_name': result.account_name
            }
        return None
    
    def _get_account_type_total(self, db: Session, account_types: List[str], start_date: str, end_date: str) -> Decimal:
        """Get total for specific account types"""
        result = db.query(
            func.sum(GeneralLedger.amount)
        ).filter(
            and_(
                GeneralLedger.account_type.in_(account_types),
                GeneralLedger.transaction_date >= start_date,
                GeneralLedger.transaction_date <= end_date
            )
        ).scalar()
        
        return result or Decimal('0')
    
    # Statistical analysis methods
    def _calculate_trend_strength(self, values: List[float]) -> float:
        """Calculate linear trend strength (-1 to 1)"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        
        # Calculate correlation coefficient
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((values[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0
        
        correlation = numerator / (denominator_x * denominator_y) ** 0.5
        return correlation
    
    def _determine_trend_direction(self, values: List[float]) -> str:
        """Determine overall trend direction"""
        if len(values) < 2:
            return "stable"
        
        trend_strength = self._calculate_trend_strength(values)
        
        if trend_strength > 0.3:
            return "increasing"
        elif trend_strength < -0.3:
            return "decreasing"
        elif self._calculate_volatility(values) > 0.5:
            return "volatile"
        else:
            return "stable"
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation as volatility measure"""
        if len(values) < 2:
            return 0
        
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0
        
        std_val = statistics.stdev(values)
        return std_val / abs(mean_val)
    
    def _detect_seasonal_pattern(self, values: List[float]) -> bool:
        """Simple seasonal pattern detection"""
        if len(values) < 12:  # Need at least a year
            return False
        
        # Simple check: compare first and second half volatility
        mid = len(values) // 2
        first_half_vol = self._calculate_volatility(values[:mid])
        second_half_vol = self._calculate_volatility(values[mid:])
        
        # If volatility is consistent, might indicate seasonal pattern
        return abs(first_half_vol - second_half_vol) < 0.2
    
    def _predict_next_value(self, values: List[float]) -> float:
        """Simple linear extrapolation for next value"""
        if len(values) < 2:
            return values[0] if values else 0
        
        # Linear trend extrapolation
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            return values[-1]
        
        slope = numerator / denominator
        intercept = mean_y - slope * mean_x
        
        return slope * n + intercept
    
    def _predict_future_value(self, values: List[float], periods_ahead: int) -> float:
        """Predict value for multiple periods ahead"""
        if len(values) < 2:
            return values[0] if values else 0
        
        # Linear trend extrapolation
        n = len(values)
        x = list(range(n))
        
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            return values[-1]
        
        slope = numerator / denominator
        intercept = mean_y - slope * mean_x
        
        return slope * (n + periods_ahead - 1) + intercept
    
    # Severity and recommendation methods
    def _get_variance_severity(self, variance_percentage: float) -> SeverityLevel:
        """Determine severity level based on variance percentage"""
        abs_variance = abs(variance_percentage)
        
        if abs_variance >= self.variance_thresholds[SeverityLevel.CRITICAL]:
            return SeverityLevel.CRITICAL
        elif abs_variance >= self.variance_thresholds[SeverityLevel.HIGH]:
            return SeverityLevel.HIGH
        elif abs_variance >= self.variance_thresholds[SeverityLevel.MEDIUM]:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _get_budget_variance_recommendations(self, account_type: str, variance_pct: float, account_name: str) -> List[str]:
        """Generate recommendations for budget variances"""
        recommendations = []
        
        if account_type in ['Income', 'Revenue']:
            if variance_pct < 0:
                recommendations.extend([
                    f"Revenue shortfall in {account_name} - review sales strategies",
                    "Consider market analysis to identify growth opportunities",
                    "Evaluate pricing strategies and customer retention programs"
                ])
            else:
                recommendations.extend([
                    f"Revenue exceeding budget in {account_name} - capitalize on success",
                    "Analyze factors driving outperformance for replication",
                    "Consider increasing targets for future periods"
                ])
        
        elif account_type == 'Expense':
            if variance_pct > 0:
                recommendations.extend([
                    f"Expense overrun in {account_name} - implement cost controls",
                    "Review approval processes and spending authorization",
                    "Identify cost reduction opportunities"
                ])
            else:
                recommendations.extend([
                    f"Under-budget spending in {account_name} - ensure operations not impacted",
                    "Consider reallocating saved budget to growth initiatives"
                ])
        
        return recommendations
    
    def _get_trend_variance_recommendations(self, variance_pct: float, trend_strength: float) -> List[str]:
        """Generate recommendations for trend variances"""
        recommendations = []
        
        if abs(trend_strength) > 0.7:  # Strong trend
            if variance_pct > 0:
                recommendations.append("Strong positive trend deviation - investigate underlying drivers")
            else:
                recommendations.append("Strong negative trend deviation - immediate attention required")
        else:
            recommendations.append("Trend deviation with moderate strength - monitor closely")
        
        recommendations.extend([
            "Review recent operational changes that might impact trends",
            "Consider external factors affecting business performance"
        ])
        
        return recommendations
    
    def _get_seasonal_variance_recommendations(self, variance_pct: float) -> List[str]:
        """Generate recommendations for seasonal variances"""
        recommendations = []
        
        if variance_pct > 0:
            recommendations.extend([
                "Above-average seasonal performance - identify success factors",
                "Consider if this represents a sustainable shift in seasonality"
            ])
        else:
            recommendations.extend([
                "Below-average seasonal performance - review seasonal strategies",
                "Evaluate impact of market conditions on typical seasonal patterns"
            ])
        
        return recommendations
    
    def _get_outlier_recommendations(self, z_score: float, description: str) -> List[str]:
        """Generate recommendations for outlier transactions"""
        recommendations = []
        
        if z_score > 3:
            recommendations.extend([
                f"Significant outlier detected - verify transaction accuracy",
                "Review approval process for large transactions",
                "Consider if this represents a new transaction pattern"
            ])
        else:
            recommendations.extend([
                "Moderate outlier - ensure proper documentation",
                "Monitor for similar unusual transactions"
            ])
        
        return recommendations
    
    def _get_ratio_variance_recommendations(self, ratio_type: str, actual: float, expected: float) -> List[str]:
        """Generate recommendations for financial ratio variances"""
        recommendations = []
        
        if ratio_type == "profit_margin":
            if actual < expected:
                recommendations.extend([
                    "Profit margin below target - review cost structure",
                    "Analyze pricing strategy and operational efficiency",
                    "Consider revenue enhancement initiatives"
                ])
            else:
                recommendations.extend([
                    "Strong profit margin performance - maintain current strategies",
                    "Evaluate sustainability of current margins"
                ])
        
        elif ratio_type == "current_ratio":
            if actual < expected:
                recommendations.extend([
                    "Current ratio below target - review liquidity position",
                    "Consider cash flow management improvements",
                    "Evaluate accounts receivable collection processes"
                ])
            else:
                recommendations.extend([
                    "Strong liquidity position - consider investment opportunities",
                    "Evaluate if excess cash could be deployed more effectively"
                ])
        
        return recommendations
    
    def _get_anomaly_recommendations(self, z_score: float) -> List[str]:
        """Generate recommendations for statistical anomalies"""
        return [
            "Statistical anomaly detected - verify data accuracy",
            "Review business processes for unusual activity",
            "Consider if this represents a process improvement opportunity"
        ]


class InsightEngine:
    """High-level insight generation engine combining multiple analysis types"""
    
    def __init__(self):
        self.variance_analyzer = VarianceAnalyzer()
    
    def generate_comprehensive_insights(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Generate comprehensive financial insights
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dictionary containing all insight types
        """
        # Variance analysis
        variances = self.variance_analyzer.analyze_variances(start_date, end_date)
        
        # Trend analysis
        trends = self.variance_analyzer.analyze_trends()
        
        # Anomaly detection
        anomalies = self.variance_analyzer.detect_anomalies(start_date, end_date)
        
        # Summarize insights by severity
        severity_summary = self._summarize_by_severity(variances + anomalies)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(variances, trends, anomalies)
        
        return {
            'period': {'start_date': start_date, 'end_date': end_date},
            'variances': [self._variance_to_dict(v) for v in variances],
            'trends': [self._trend_to_dict(t) for t in trends],
            'anomalies': [self._variance_to_dict(a) for a in anomalies],
            'severity_summary': severity_summary,
            'executive_summary': executive_summary,
            'total_insights': len(variances) + len(trends) + len(anomalies),
            'generated_at': datetime.now().isoformat()
        }
    
    def _variance_to_dict(self, variance: VarianceInsight) -> Dict[str, Any]:
        """Convert VarianceInsight to dictionary"""
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
    
    def _trend_to_dict(self, trend: TrendAnalysis) -> Dict[str, Any]:
        """Convert TrendAnalysis to dictionary"""
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
    
    def _summarize_by_severity(self, insights: List[VarianceInsight]) -> Dict[str, int]:
        """Summarize insights by severity level"""
        summary = {level.value: 0 for level in SeverityLevel}
        
        for insight in insights:
            summary[insight.severity.value] += 1
        
        return summary
    
    def _generate_executive_summary(self, variances: List[VarianceInsight], trends: List[TrendAnalysis], anomalies: List[VarianceInsight]) -> Dict[str, Any]:
        """Generate executive summary of insights"""
        critical_issues = [v for v in variances + anomalies if v.severity == SeverityLevel.CRITICAL]
        high_issues = [v for v in variances + anomalies if v.severity == SeverityLevel.HIGH]
        
        trending_up = [t for t in trends if t.trend_direction == "increasing" and t.trend_strength > 0.5]
        trending_down = [t for t in trends if t.trend_direction == "decreasing" and t.trend_strength > 0.5]
        
        return {
            'critical_attention_required': len(critical_issues),
            'high_priority_items': len(high_issues),
            'accounts_trending_up': len(trending_up),
            'accounts_trending_down': len(trending_down),
            'top_concerns': [v.description for v in critical_issues[:3]],
            'key_opportunities': [f"{t.account_name} trending {t.trend_direction}" for t in trending_up[:3]],
            'recommended_actions': self._get_top_recommendations(variances + anomalies)
        }
    
    def _get_top_recommendations(self, insights: List[VarianceInsight]) -> List[str]:
        """Get top recommendations across all insights"""
        all_recommendations = []
        for insight in insights:
            all_recommendations.extend(insight.recommendations)
        
        # Count frequency and return top 5 unique recommendations
        from collections import Counter
        recommendation_counts = Counter(all_recommendations)
        return [rec for rec, count in recommendation_counts.most_common(5)]


# Convenience function
def generate_financial_insights(start_date: str, end_date: str) -> Dict[str, Any]:
    """Generate comprehensive financial insights for the given period"""
    engine = InsightEngine()
    return engine.generate_comprehensive_insights(start_date, end_date)