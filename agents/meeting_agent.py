"""
Meeting Agent - Handles meeting scheduling and management
"""
from typing import Dict, Any, Optional, List
from database import Lead, Meeting, Activity, LeadStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from config import settings
import pytz


class MeetingAgent:
    """Agent responsible for scheduling and managing meetings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def suggest_meeting_slots(self, lead_id: int, num_slots: int = 3) -> List[Dict[str, Any]]:
        """Suggest available meeting slots for a lead"""
        # Get lead
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise ValueError(f"Lead with ID {lead_id} not found")
        
        # Generate slots for next N business days
        slots = []
        current_date = datetime.now()
        days_added = 0
        
        while len(slots) < num_slots and days_added < settings.meeting_scheduling_window_days:
            check_date = current_date + timedelta(days=days_added + 1)
            
            # Skip weekends
            if check_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Suggest 3 time slots per day
                for hour in [10, 14, 16]:  # 10 AM, 2 PM, 4 PM
                    slot_time = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    
                    # Check if slot is available (no existing meeting)
                    existing = self.db.query(Meeting).filter(
                        Meeting.scheduled_at == slot_time,
                        Meeting.status == "scheduled"
                    ).first()
                    
                    if not existing:
                        slots.append({
                            "datetime": slot_time.isoformat(),
                            "display": slot_time.strftime("%A, %B %d at %I:%M %p")
                        })
                        
                        if len(slots) >= num_slots:
                            break
            
            days_added += 1
        
        return slots
    
    def schedule_meeting(
        self,
        lead_id: int,
        scheduled_at: datetime,
        title: Optional[str] = None,
        description: Optional[str] = None,
        duration_minutes: int = 30
    ) -> Dict[str, Any]:
        """Schedule a meeting with a lead"""
        # Get lead
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise ValueError(f"Lead with ID {lead_id} not found")
        
        # Generate meeting title if not provided
        if not title:
            title = f"Discovery Call - {lead.company_name}"
        
        # Generate meeting description if not provided
        if not description:
            description = f"Initial discovery call with {lead.contact_name} from {lead.company_name}"
        
        # Create meeting record
        meeting = Meeting(
            lead_id=lead.id,
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            status="scheduled"
        )
        
        self.db.add(meeting)
        
        # Update lead status
        lead.status = LeadStatus.MEETING_SCHEDULED
        lead.updated_at = datetime.utcnow()
        
        # Generate meeting agenda using AI
        lead_data = {
            "company_name": lead.company_name,
            "industry": lead.industry,
            "pain_points": lead.pain_points
        }
        agenda = self.watsonx.suggest_meeting_agenda(lead_data, lead.qualification_notes or "")
        meeting.notes = "Suggested Agenda:\n" + "\n".join([f"- {item}" for item in agenda])
        
        # Log activity
        activity = Activity(
            lead_id=lead.id,
            activity_type="meeting_scheduled",
            description=f"Meeting scheduled: {title}",
            activity_metadata=f"meeting_id: {meeting.id}, scheduled_at: {scheduled_at.isoformat()}"
        )
        self.db.add(activity)
        
        self.db.commit()
        self.db.refresh(meeting)
        
        return {
            "meeting_id": meeting.id,
            "lead_id": lead.id,
            "title": meeting.title,
            "scheduled_at": meeting.scheduled_at.isoformat(),
            "duration_minutes": meeting.duration_minutes,
            "agenda": agenda,
            "status": meeting.status
        }
    
    def get_upcoming_meetings(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get all upcoming meetings"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)
        
        meetings = self.db.query(Meeting).filter(
            Meeting.scheduled_at >= start_date,
            Meeting.scheduled_at <= end_date,
            Meeting.status == "scheduled"
        ).order_by(Meeting.scheduled_at).all()
        
        result = []
        for meeting in meetings:
            lead = self.db.query(Lead).filter(Lead.id == meeting.lead_id).first()
            result.append({
                "meeting_id": meeting.id,
                "lead_id": meeting.lead_id,
                "company_name": lead.company_name if lead else "Unknown",
                "contact_name": lead.contact_name if lead else "Unknown",
                "title": meeting.title,
                "scheduled_at": meeting.scheduled_at.isoformat(),
                "duration_minutes": meeting.duration_minutes
            })
        
        return result
    
    def complete_meeting(self, meeting_id: int, notes: str, next_steps: str) -> Dict[str, Any]:
        """Mark a meeting as completed with notes"""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            raise ValueError(f"Meeting with ID {meeting_id} not found")
        
        meeting.status = "completed"
        meeting.notes = notes
        meeting.next_steps = next_steps
        meeting.updated_at = datetime.utcnow()
        
        # Log activity
        activity = Activity(
            lead_id=meeting.lead_id,
            activity_type="meeting_completed",
            description=f"Meeting completed: {meeting.title}",
            activity_metadata=f"meeting_id: {meeting.id}"
        )
        self.db.add(activity)
        
        self.db.commit()
        
        return {
            "meeting_id": meeting.id,
            "status": "completed",
            "notes": notes,
            "next_steps": next_steps
        }
    
    def cancel_meeting(self, meeting_id: int, reason: str = "") -> Dict[str, Any]:
        """Cancel a scheduled meeting"""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            raise ValueError(f"Meeting with ID {meeting_id} not found")
        
        meeting.status = "cancelled"
        meeting.notes = f"Cancelled: {reason}"
        meeting.updated_at = datetime.utcnow()
        
        # Log activity
        activity = Activity(
            lead_id=meeting.lead_id,
            activity_type="meeting_cancelled",
            description=f"Meeting cancelled: {meeting.title}",
            activity_metadata=f"meeting_id: {meeting.id}, reason: {reason}"
        )
        self.db.add(activity)
        
        self.db.commit()
        
        return {
            "meeting_id": meeting.id,
            "status": "cancelled"
        }
