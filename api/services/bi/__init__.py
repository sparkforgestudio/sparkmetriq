# api/services/bi/__init__.py
"""
Services BI pour musAI Platform.
"""

from api.services.bi.rag2_client import RAG2Client
from api.services.bi.insight_engine import InsightEngine
from api.services.bi.pricing_optimizer import PricingOptimizerService

__all__ = ["RAG2Client", "InsightEngine", "PricingOptimizerService"]



