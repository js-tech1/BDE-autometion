"""
Lead Analysis Agent - Analyzes and qualifies leads using AI scoring
"""
from typing import Dict, Any, List
from database import Lead, LeadStatus, Activity
from sqlalchemy.orm import Session
from datetime import datetime
import random


class LeadAnalysisAgent:
    """Agent responsible for analyzing and qualifying leads"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_lead(self, lead_id: int) -> Dict[str, Any]:
        """Analyze a lead and update its qualification data"""
        # Get lead from database
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise ValueError(f"Lead with ID {lead_id} not found")
        
        # Smart scoring based on industry and company data
        score = self._calculate_lead_score(lead)
        pain_points = self._identify_pain_points(lead)
        budget = self._estimate_budget(lead)
        timeline = self._estimate_timeline(lead)
        
        # Update lead with analysis results
        lead.lead_score = score
        lead.qualification_notes = f"Auto-analyzed on {datetime.utcnow().strftime('%Y-%m-%d')}"
        lead.pain_points = "\n".join(pain_points)
        lead.budget_estimate = budget
        lead.decision_timeline = timeline
        
        # Update status based on lead score
        if score >= 0.7:
            lead.status = LeadStatus.QUALIFIED
        elif score >= 0.4:
            lead.status = LeadStatus.CONTACTED
        else:
            lead.status = LeadStatus.NEW
        
        lead.updated_at = datetime.utcnow()
        
        # Log activity
        activity = Activity(
            lead_id=lead.id,
            activity_type="lead_analyzed",
            description=f"Lead analyzed with score: {score:.2f}",
            activity_metadata=f"Status: {lead.status.value}, Budget: {budget}"
        )
        self.db.add(activity)
        
        # Commit changes
        self.db.commit()
        self.db.refresh(lead)
        
        return {
            "lead_id": lead.id,
            "company": lead.company_name,
            "lead_score": score,
            "status": lead.status.value,
            "pain_points": pain_points,
            "budget_estimate": budget,
            "timeline": timeline
        }
    
    def _calculate_lead_score(self, lead: Lead) -> float:
        """Calculate lead score based on available data"""
        score = 0.5  # Base score
        
        # Industry scoring (high-value industries)
        high_value_industries = ['saas', 'fintech', 'technology', 'healthcare', 'finance']
        if lead.industry and any(ind in lead.industry.lower() for ind in high_value_industries):
            score += 0.2
        
        # Company size (larger = higher score)
        if lead.company_size:
            if 'enterprise' in lead.company_size.lower() or '1000+' in lead.company_size:
                score += 0.2
            elif '500' in lead.company_size or '200' in lead.company_size:
                score += 0.1
        
        # Revenue (higher revenue = higher score)
        if lead.revenue:
            if '$100M' in lead.revenue or '$500M' in lead.revenue:
                score += 0.15
            elif '$50M' in lead.revenue or '$20M' in lead.revenue:
                score += 0.1
        
        # Has complete data
        if lead.phone and lead.industry and lead.location:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _identify_pain_points(self, lead: Lead) -> List[str]:
        """Identify likely pain points based on industry"""
        industry_pain_points = {
            'saas': [
                'Need to scale customer acquisition',
                'High customer churn rates',
                'Manual onboarding processes'
            ],
            'retail': [
                'Inventory management challenges',
                'Need for better customer analytics',
                'Omnichannel integration gaps'
            ],
            'fintech': [
                'Compliance and regulatory requirements',
                'Need for real-time transaction processing',
                'Security and fraud prevention'
            ],
            'healthcare': [
                'Patient data management',
                'Appointment scheduling inefficiencies',
                'Insurance claim processing delays'
            ],
            'construction': [
                'Project management complexity',
                'Resource allocation challenges',
                'Cost estimation accuracy'
            ],
            'edtech': [
                'Student engagement and retention',
                'Content delivery scalability',
                'Learning analytics and reporting'
            ],
            'ecommerce': [
                'Cart abandonment issues',
                'Website performance optimization',
                'Customer personalization needs'
            ]
        }
        
        if lead.industry:
            for key, points in industry_pain_points.items():
                if key in lead.industry.lower():
                    return points[:2]  # Return top 2 pain points
        
        return ['Process automation opportunities', 'Digital transformation needs']
    
    def _estimate_budget(self, lead: Lead) -> str:
        """Estimate budget range based on company data"""
        if lead.revenue:
            if '$100M' in lead.revenue or '$500M' in lead.revenue:
                return '$50K - $200K'
            elif '$50M' in lead.revenue:
                return '$30K - $100K'
            elif '$20M' in lead.revenue or '$10M' in lead.revenue:
                return '$15K - $50K'
        
        if lead.company_size:
            if '500' in lead.company_size or '1000' in lead.company_size:
                return '$40K - $150K'
            elif '200' in lead.company_size:
                return '$25K - $80K'
        
        return '$10K - $30K'
    
    def _estimate_timeline(self, lead: Lead) -> str:
        """Estimate decision timeline"""
        timelines = ['1-2 months', '2-3 months', '3-6 months', '6-12 months']
        
        if lead.company_size:
            if 'enterprise' in lead.company_size.lower() or '1000' in lead.company_size:
                return '6-12 months'  # Large companies = slow decisions
            elif '500' in lead.company_size:
                return '3-6 months'
            elif '100' in lead.company_size or '200' in lead.company_size:
                return '2-3 months'
        
        return '1-2 months'  # SMBs decide faster
    
    def batch_analyze_leads(self, status: LeadStatus = LeadStatus.NEW) -> list:
        """Analyze multiple leads in batch"""
        leads = self.db.query(Lead).filter(Lead.status == status).all()
        results = []
        
        for lead in leads:
            try:
                result = self.analyze_lead(lead.id)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing lead {lead.id}: {e}")
                results.append({
                    "lead_id": lead.id,
                    "error": str(e)
                })
        
        return results
    
    def get_qualified_leads(self, min_score: float = 0.7) -> list:
        """Get all qualified leads above a certain score"""
        leads = self.db.query(Lead).filter(
            Lead.lead_score >= min_score,
            Lead.status == LeadStatus.QUALIFIED
        ).all()
        
        return [
            {
                "id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "email": lead.email,
                "lead_score": lead.lead_score,
                "status": lead.status.value
            }
            for lead in leads
        ]
