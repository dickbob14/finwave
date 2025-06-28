"""
AI-powered financial query endpoint
"""

import logging
import os
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import openai

from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ask"])

# Configure OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    message: str
    citations: List[Dict[str, Any]] = []
    sql: Optional[str] = None
    kpis: List[Dict[str, Any]] = []
    error: Optional[str] = None
    ai_powered: bool = True

@router.post("/ask", response_model=AskResponse)
async def ask_finwave(
    request: AskRequest,
    user: dict = Depends(get_current_user)
):
    """
    Process financial queries using AI
    """
    try:
        if not openai_api_key:
            # Return a helpful message if OpenAI is not configured
            return AskResponse(
                message="I understand you're asking about your financial data. AI-powered insights require an OpenAI API key to be configured. For now, I can help you navigate to the right reports and dashboards.",
                error="OpenAI API key not configured",
                ai_powered=False
            )
        
        # Create a system prompt with context about the user's data
        system_prompt = """You are FinWave AI, a financial analysis assistant. You have access to:
        - QuickBooks financial data (P&L, balance sheet, cash flow)
        - Salesforce CRM data (pipeline, deals, customers)
        - Gusto payroll data (headcount, compensation)
        
        Provide concise, actionable insights based on the user's query. If you need specific data that isn't available, suggest what reports or integrations would help."""
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        message = response.choices[0].message.content
        
        # Extract any SQL or KPIs mentioned in the response (simplified for now)
        return AskResponse(
            message=message,
            citations=[],
            sql=None,
            kpis=[]
        )
        
    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}")
        
        # Return a fallback response
        return AskResponse(
            message="I understand you're asking about your financial data. Based on your connected sources (QuickBooks, Salesforce, Gusto), I can help analyze revenue trends, expense patterns, cash flow, and key metrics. Could you be more specific about what you'd like to know?",
            error=str(e),
            ai_powered=False
        )