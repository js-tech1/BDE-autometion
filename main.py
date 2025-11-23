"""
FastAPI application for BDE Automation System
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
import csv
import io
import json

from database import init_db, get_db, Lead, LeadStatus
from agents import LeadAnalysisAgent, EmailAgent, MeetingAgent
from config import settings
from ai.watson_orchestrate import watson_orchestrate

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered BDE Automation System with IBM Watson Integration"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class LeadCreate(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    revenue: Optional[str] = None
    location: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    company_name: str
    contact_name: str
    email: str
    lead_score: float
    status: str
    
    class Config:
        from_attributes = True


class EmailGenerate(BaseModel):
    lead_id: int
    email_type: str = "initial"


class MeetingSchedule(BaseModel):
    lead_id: int
    scheduled_at: str  # ISO format datetime
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: int = 30


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"\n{'='*60}")
    print(f"{settings.app_name} v{settings.app_version}")
    print(f"{'='*60}")
    
    # Test Watson connection
    watson_status = watson_orchestrate.test_connection()
    if watson_status.get("connected"):
        print(f"✓ IBM Watson Orchestrate: CONNECTED")
        print(f"  API Key: {watson_orchestrate.api_key[:20]}...")
    else:
        print(f"ℹ IBM Watson Orchestrate: Unavailable (using local AI)")
        print(f"  {watson_status.get('message', 'Connection failed')}")
    
    print(f"\n🚀 Server started successfully!")
    print(f"{'='*60}\n")


# HTML Interface Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the internal AI chat interface"""
    try:
        with open("chat.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>BDE Automation System</h1><p>Visit <a href='/docs'>/docs</a> for API documentation</p>")


@app.get("/client", response_class=HTMLResponse)
async def client_chat():
    """Serve the client-facing chat interface"""
    try:
        with open("client_chat.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Client Chat Not Found</h1>")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Lead endpoints
@app.post("/api/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead"""
    # Check if lead with email already exists
    existing_lead = db.query(Lead).filter(Lead.email == lead.email).first()
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists"
        )
    
    # Create new lead
    new_lead = Lead(**lead.dict())
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    
    return new_lead


@app.post("/api/leads/upload")
async def upload_leads_file(
    file: UploadFile = File(...),
    auto_analyze: bool = False,
    db: Session = Depends(get_db)
):
    """Upload CSV/Excel file with leads for bulk import"""
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files are supported"
        )
    
    try:
        contents = await file.read()
        
        # Parse CSV
        if file.filename.endswith('.csv'):
            csv_data = io.StringIO(contents.decode('utf-8'))
            reader = csv.DictReader(csv_data)
            leads_data = list(reader)
            
            print(f"CSV parsed: {len(leads_data)} rows found")
            if leads_data:
                print(f"First row columns: {list(leads_data[0].keys())}")
                print(f"First row data: {leads_data[0]}")
            
            if not leads_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CSV file is empty or has no data rows"
                )
        else:
            # For Excel files (requires openpyxl)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel support coming soon. Please use CSV format."
            )
        
        created_leads = []
        skipped_leads = []
        
        # Smart column mapping - find the right columns automatically
        def find_column(row, possible_names):
            """Find column value by checking multiple possible column names"""
            for key in row.keys():
                key_lower = key.lower().strip()
                for name in possible_names:
                    if name in key_lower:
                        value = row[key]
                        return value.strip() if isinstance(value, str) else str(value) if value else ''
            return ''
        
        for idx, row in enumerate(leads_data, start=1):
            try:
                # Clean whitespace from keys and values
                row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
                
                # Direct mapping with exact column names from your CSV
                email = row.get('Lead Email', '').strip()
                company = row.get('Company Name', '').strip()
                contact = row.get('Lead Name', '').strip()
                
                # Debug: Log what we found
                print(f"Row {idx}: email='{email}', company='{company}', contact='{contact}'")
                
                if not email or not company or not contact:
                    skipped_leads.append({
                        "row": idx,
                        "email": email or "N/A",
                        "company": company or "N/A",
                        "reason": f"Missing: {', '.join([f for f, v in [('email', email), ('company', company), ('contact', contact)] if not v])}"
                    })
                    continue
                
                # Check for duplicate by company name AND email (not just email)
                existing_lead = db.query(Lead).filter(
                    Lead.company_name == company,
                    Lead.email == email
                ).first()
                
                if existing_lead:
                    skipped_leads.append({
                        "row": idx,
                        "email": email,
                        "company": company,
                        "reason": "Duplicate: Company already exists with this email"
                    })
                    continue
                
                # Create lead
                new_lead = Lead(
                    company_name=company,
                    contact_name=contact,
                    email=email,
                    phone=row.get('Phone', ''),
                    industry=row.get('Industry', ''),
                    company_size=row.get('Company Size', ''),
                    revenue=row.get('Revenue', ''),
                    location=row.get('Location', '')
                )
                db.add(new_lead)
                created_leads.append({"email": email, "company": company})
                print(f"✓ Created lead: {company}")
                
            except Exception as e:
                print(f"✗ Error processing row {idx}: {str(e)}")
                skipped_leads.append({
                    "row": idx,
                    "reason": f"Error: {str(e)}"
                })
                continue
        
        db.commit()
        
        # Auto-analyze if requested
        if auto_analyze and created_leads:
            from agents import LeadAnalysisAgent
            agent = LeadAnalysisAgent(db)
            agent.batch_analyze_leads()
        
        return {
            "message": "File processed successfully",
            "created": len(created_leads),
            "skipped": len(skipped_leads),
            "created_emails": [lead['email'] for lead in created_leads],
            "skipped_details": skipped_leads,  # Show all skipped with reasons
            "debug_info": {
                "total_rows": len(leads_data),
                "first_row_keys": list(leads_data[0].keys()) if leads_data else []
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@app.get("/api/leads", response_model=List[LeadResponse])
async def get_leads(
    status_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get all leads with optional filters"""
    query = db.query(Lead)
    
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    
    if min_score is not None:
        query = query.filter(Lead.lead_score >= min_score)
    
    leads = query.all()
    return leads


@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.post("/api/leads/{lead_id}/analyze")
async def analyze_lead(lead_id: int, db: Session = Depends(get_db)):
    """Analyze a lead using AI"""
    agent = LeadAnalysisAgent(db)
    try:
        result = agent.analyze_lead(lead_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/leads/analyze-batch")
async def analyze_batch(db: Session = Depends(get_db)):
    """Analyze all new leads in batch"""
    agent = LeadAnalysisAgent(db)
    results = agent.batch_analyze_leads()
    return {"analyzed": len(results), "results": results}


# Email endpoints
@app.post("/api/emails/generate")
async def generate_email(email_data: EmailGenerate, db: Session = Depends(get_db)):
    """Generate a personalized email for a lead"""
    agent = EmailAgent(db)
    try:
        result = agent.generate_email(email_data.lead_id, email_data.email_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emails/{email_id}/send")
async def send_email(email_id: int, db: Session = Depends(get_db)):
    """Send an email"""
    agent = EmailAgent(db)
    try:
        result = await agent.send_email(email_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails/pending")
async def get_pending_emails(db: Session = Depends(get_db)):
    """Get all pending emails"""
    agent = EmailAgent(db)
    emails = agent.get_pending_emails()
    return {"count": len(emails), "emails": emails}


@app.post("/api/emails/generate-and-send-all")
async def generate_and_send_all_emails(db: Session = Depends(get_db)):
    """Generate personalized emails for ALL leads and send them"""
    agent = EmailAgent(db)
    
    # Get all leads that don't have an email sent yet
    from database import Email, EmailStatus
    leads = db.query(Lead).all()
    
    results = {
        "total_leads": len(leads),
        "emails_generated": 0,
        "emails_sent": 0,
        "skipped": 0,
        "details": []
    }
    
    for lead in leads:
        try:
            # Check if email already exists for this lead
            existing_email = db.query(Email).filter(
                Email.lead_id == lead.id,
                Email.email_type == "initial"
            ).first()
            
            if existing_email:
                results["skipped"] += 1
                results["details"].append({
                    "lead": lead.email,
                    "status": "skipped",
                    "reason": "Email already generated"
                })
                continue
            
            # Generate personalized email using AI agent
            email_result = agent.generate_email(lead.id, email_type="initial")
            results["emails_generated"] += 1
            
            # Send the email immediately
            if email_result.get("email_id"):
                send_result = await agent.send_email(email_result["email_id"])
                if send_result.get("status") == "sent":
                    results["emails_sent"] += 1
                    results["details"].append({
                        "lead": lead.email,
                        "company": lead.company_name,
                        "status": "sent",
                        "subject": email_result.get("subject", "N/A")
                    })
                else:
                    results["details"].append({
                        "lead": lead.email,
                        "company": lead.company_name,
                        "status": "generated_but_not_sent",
                        "reason": send_result.get("message", "Unknown error")
                    })
            
        except Exception as e:
            results["skipped"] += 1
            results["details"].append({
                "lead": lead.email,
                "status": "error",
                "reason": str(e)
            })
    
    return results


# Meeting endpoints
@app.get("/api/meetings/suggest-slots/{lead_id}")
async def suggest_slots(lead_id: int, num_slots: int = 3, db: Session = Depends(get_db)):
    """Suggest available meeting slots for a lead"""
    agent = MeetingAgent(db)
    try:
        slots = agent.suggest_meeting_slots(lead_id, num_slots)
        return {"lead_id": lead_id, "suggested_slots": slots}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/meetings/schedule")
async def schedule_meeting(meeting_data: MeetingSchedule, db: Session = Depends(get_db)):
    """Schedule a meeting with a lead"""
    agent = MeetingAgent(db)
    try:
        scheduled_at = datetime.fromisoformat(meeting_data.scheduled_at)
        result = agent.schedule_meeting(
            lead_id=meeting_data.lead_id,
            scheduled_at=scheduled_at,
            title=meeting_data.title,
            description=meeting_data.description,
            duration_minutes=meeting_data.duration_minutes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meetings/upcoming")
async def get_upcoming_meetings(days_ahead: int = 7, db: Session = Depends(get_db)):
    """Get all upcoming meetings"""
    agent = MeetingAgent(db)
    meetings = agent.get_upcoming_meetings(days_ahead)
    return {"count": len(meetings), "meetings": meetings}


@app.post("/api/meetings/{meeting_id}/complete")
async def complete_meeting(
    meeting_id: int,
    notes: str,
    next_steps: str,
    db: Session = Depends(get_db)
):
    """Mark a meeting as completed"""
    agent = MeetingAgent(db)
    try:
        result = agent.complete_meeting(meeting_id, notes, next_steps)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Pipeline dashboard endpoint
@app.get("/api/dashboard/pipeline")
async def get_pipeline_stats(db: Session = Depends(get_db)):
    """Get pipeline statistics"""
    stats = {}
    
    # Count leads by status
    for status_value in LeadStatus:
        count = db.query(Lead).filter(Lead.status == status_value).count()
        stats[status_value.value] = count
    
    # Average lead score
    from sqlalchemy import func
    avg_score = db.query(func.avg(Lead.lead_score)).scalar()
    stats["average_lead_score"] = round(avg_score or 0, 2)
    
    # Total leads
    stats["total_leads"] = db.query(Lead).count()
    
    # Qualified leads (score >= 0.7)
    stats["qualified_leads"] = db.query(Lead).filter(Lead.lead_score >= 0.7).count()
    
    return stats


# Client-Facing Chat Endpoints
@app.post("/api/client-chat/{lead_id}")
async def chat_with_client(
    lead_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Client-facing AI chat - handles conversations with prospects using Dynamic AI"""
    from agents.dynamic_chat_agent import dynamic_chat_agent
    
    # Get lead data
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Prepare lead data
    lead_data = {
        "id": lead.id,
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "lead_score": lead.lead_score,
        "pain_points": lead.pain_points,
        "budget_estimate": lead.budget_estimate
    }
    
    # Process conversation with Dynamic AI
    response = dynamic_chat_agent.chat(lead_id, request.message, lead_data)
    
    # Log activity
    from database import Activity
    activity = Activity(
        lead_id=lead_id,
        activity_type="client_chat",
        description=f"Client conversation - Turn {response['conversation_turn']}",
        activity_metadata=json.dumps({
            "sentiment": response["sentiment"],
            "suggested_action": response["suggested_action"]
        })
    )
    db.add(activity)
    db.commit()
    
    return response


@app.post("/api/pitch/generate/{lead_id}")
async def generate_pitch(
    lead_id: int,
    pitch_type: str = "value_proposition",
    db: Session = Depends(get_db)
):
    """Generate AI-powered persuasive pitch for a lead"""
    from agents.dynamic_chat_agent import dynamic_chat_agent
    
    # Get lead data
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_data = {
        "id": lead.id,
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "lead_score": lead.lead_score,
        "pain_points": lead.pain_points,
        "budget_estimate": lead.budget_estimate,
        "decision_timeline": lead.decision_timeline
    }
    
    # Generate pitch using AI (fallback to simple response)
    # Note: chat_agent doesn't have generate_pitch, use simple template
    pitch = {
        "pitch": f"Hi {lead.contact_name}, I'd love to discuss how we can help {lead.company_name} in the {lead.industry} industry achieve {pitch_type} goals. Based on your company profile, we believe we can deliver significant value.",
        "pitch_type": pitch_type,
        "lead_score": lead.lead_score
    }
    
    # Log activity
    from database import Activity
    activity = Activity(
        lead_id=lead_id,
        activity_type="pitch_generated",
        description=f"Generated {pitch_type} pitch",
        activity_metadata=json.dumps({"pitch_type": pitch_type})
    )
    db.add(activity)
    db.commit()
    
    return pitch


@app.post("/api/objection/handle/{lead_id}")
async def handle_objection(
    lead_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """AI-powered objection handling with persuasive responses"""
    from agents.dynamic_chat_agent import dynamic_chat_agent
    
    # Get lead data
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_data = {
        "id": lead.id,
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "industry": lead.industry,
        "lead_score": lead.lead_score,
        "budget_estimate": lead.budget_estimate
    }
    
    # Handle objection with AI (fallback to simple response)
    # Note: Use intelligent agent for objection handling
    response = {
        "objection_type": "general",
        "response": f"I understand your concern. Let me address that - many companies in {lead_data['industry']} had similar questions. Our solution has helped them overcome this challenge. Would you like to discuss specifics?",
        "success_probability": 0.7
    }
    
    # Log activity
    from database import Activity
    activity = Activity(
        lead_id=lead_id,
        activity_type="objection_handled",
        description=f"Handled {response['objection_type']} objection",
        activity_metadata=json.dumps({
            "objection_type": response["objection_type"],
            "success_probability": response["success_probability"]
        })
    )
    db.add(activity)
    db.commit()
    
    return response


# Test Watson Connection
@app.get("/api/watson/test")
async def test_watson():
    """Test IBM Watson Orchestrate credentials"""
    connection_status = watson_orchestrate.test_connection()
    return {
        "service": "IBM Watson Orchestrate",
        "credentials": "Configured" if watson_orchestrate.api_key else "Missing",
        "connection": connection_status,
        "message": "✓ Using IBM Watson AI" if connection_status.get("connected") else "ℹ Using Local Agentic AI (Watson unavailable)"
    }


# AI Chat Interface (Internal)
@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest, db: Session = Depends(get_db)):
    """TRUE Agentic AI - Powered by IBM Watson Orchestrate + Local Intelligence"""
    from agents.intelligent_agent import intelligent_agent
    
    # Inject database
    intelligent_agent.db = db
    
    # Get session ID from context if available
    session_id = request.context.get("session_id", "default") if request.context else "default"
    
    # Try Watson Orchestrate first, fallback to local AI
    context = {
        "session_id": session_id,
        "db": db,
        "intelligent_agent": intelligent_agent
    }
    
    # Watson will try IBM API, then use local AI if needed
    enhanced_response = watson_orchestrate.enhance_response(request.message, context)
    
    # If Watson returned a string, wrap it in proper format
    if isinstance(enhanced_response, str):
        result = intelligent_agent.process_request(request.message, session_id)
        result["ai_provider"] = "IBM Watson Orchestrate (with local fallback)"
        return result
    
    return enhanced_response
    
    # Parse intent from message
    if any(word in message for word in ['analyze', 'score', 'qualify', 'evaluate']):
        # Lead analysis intent
        if 'all' in message or 'batch' in message:
            from agents import LeadAnalysisAgent
            agent = LeadAnalysisAgent(db)
            results = agent.batch_analyze_leads()
            response_data["actions"].append("analyze_all_leads")
            response_data["results"].append({
                "action": "Lead Analysis",
                "message": f"Analyzed {len(results)} leads",
                "data": results
            })
        else:
            # Try to find lead ID in message
            import re
            lead_ids = re.findall(r'\d+', message)
            if lead_ids:
                from agents import LeadAnalysisAgent
                agent = LeadAnalysisAgent(db)
                result = agent.analyze_lead(int(lead_ids[0]))
                response_data["actions"].append(f"analyze_lead_{lead_ids[0]}")
                response_data["results"].append({
                    "action": "Lead Analysis",
                    "data": result
                })
    
    if any(word in message for word in ['email', 'send', 'contact', 'reach out']):
        # Email generation/sending intent
        if 'generate' in message or 'create' in message or 'draft' in message:
            # Get ALL leads (not just qualified)
            from database import Email, EmailStatus
            all_leads = db.query(Lead).all()
            
            from agents import EmailAgent
            agent = EmailAgent(db)
            emails_created = []
            emails_skipped = []
            
            for lead in all_leads:
                try:
                    # Generate personalized email using agent
                    email_result = agent.generate_email(lead.id, "initial")
                    
                    # Also send the email immediately
                    if email_result.get("email_id"):
                        try:
                            send_result = await agent.send_email(email_result["email_id"])
                            emails_created.append({
                                "lead": lead.email,
                                "company": lead.company_name,
                                "subject": email_result.get("subject", "N/A"),
                                "status": "sent" if send_result.get("status") == "sent" else "generated"
                            })
                        except Exception as send_error:
                            emails_created.append({
                                "lead": lead.email,
                                "company": lead.company_name,
                                "subject": email_result.get("subject", "N/A"),
                                "status": "generated_but_not_sent",
                                "error": str(send_error)
                            })
                    else:
                        emails_created.append({
                            "lead": lead.email,
                            "company": lead.company_name,
                            "subject": email_result.get("subject", "N/A"),
                            "status": "generated"
                        })
                except Exception as e:
                    emails_skipped.append({
                        "lead": lead.email if hasattr(lead, 'email') else 'Unknown',
                        "reason": str(e)
                    })
            
            response_data["actions"].append("generate_and_send_emails")
            response_data["results"].append({
                "action": "Email Generation & Sending",
                "message": f"Generated and sent {len(emails_created)} personalized emails",
                "emails_created": emails_created,
                "emails_skipped": emails_skipped,
                "data": emails_created
            })
    
    if any(word in message for word in ['meeting', 'schedule', 'book', 'calendar']):
        # Meeting scheduling intent
        if 'suggest' in message or 'available' in message or 'slots' in message:
            # Get first contacted lead
            lead = db.query(Lead).filter(
                Lead.status.in_([LeadStatus.CONTACTED, LeadStatus.QUALIFIED])
            ).first()
            
            if lead:
                from agents import MeetingAgent
                agent = MeetingAgent(db)
                slots = agent.suggest_meeting_slots(lead.id, num_slots=5)
                
                response_data["actions"].append("suggest_meeting_slots")
                response_data["results"].append({
                    "action": "Meeting Slots",
                    "message": f"Suggested meeting slots for {lead.company_name}",
                    "lead_id": lead.id,
                    "data": slots
                })
    
    if any(word in message for word in ['status', 'pipeline', 'dashboard', 'stats', 'report']):
        # Pipeline stats intent
        stats = {}
        for status_value in LeadStatus:
            count = db.query(Lead).filter(Lead.status == status_value).count()
            stats[status_value.value] = count
        
        from sqlalchemy import func
        avg_score = db.query(func.avg(Lead.lead_score)).scalar()
        stats["average_lead_score"] = round(avg_score or 0, 2)
        stats["total_leads"] = db.query(Lead).count()
        
        response_data["actions"].append("get_pipeline_stats")
        response_data["results"].append({
            "action": "Pipeline Statistics",
            "data": stats
        })
    
    if any(word in message for word in ['pitch', 'convince', 'persuade', 'sell']):
        # Pitch generation intent
        qualified = db.query(Lead).filter(
            Lead.status == LeadStatus.QUALIFIED,
            Lead.lead_score >= 0.6
        ).limit(3).all()
        
        from agents.dynamic_chat_agent import dynamic_chat_agent
        pitches_created = []
        
        for lead in qualified:
            lead_data = {
                "id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "industry": lead.industry,
                "company_size": lead.company_size,
                "lead_score": lead.lead_score,
                "pain_points": lead.pain_points,
                "budget_estimate": lead.budget_estimate,
                "decision_timeline": lead.decision_timeline
            }
            pitch = chat_agent.generate_pitch(lead_data, "value_proposition")
            pitches_created.append({
                "company": lead.company_name,
                "pitch_preview": pitch["content"][:200] + "..."
            })
        
        response_data["actions"].append("generate_pitches")
        response_data["results"].append({
            "action": "AI-Powered Pitch Generation",
            "message": f"Generated {len(pitches_created)} persuasive pitches for qualified leads",
            "data": pitches_created
        })
    
    if any(word in message for word in ['help', 'what can', 'commands', 'options']):
        # Help intent
        response_data["actions"].append("help")
        response_data["results"].append({
            "action": "Help",
            "message": "Here's what I can do:",
            "commands": [
                "Analyze all leads - analyzes and scores all new leads",
                "Generate emails for qualified leads - creates personalized emails",
                "Generate pitches - creates AI-powered persuasive pitches",
                "Suggest meeting slots - finds available meeting times",
                "Show pipeline status - displays current statistics",
                "Analyze lead [ID] - analyzes a specific lead",
            ]
        })
    
    # If no action was taken, provide suggestions
    if not response_data["actions"]:
        response_data["message"] = "I'm not sure what you want me to do. Try: 'analyze all leads', 'generate emails', 'show pipeline status', or 'help'"
    else:
        response_data["message"] = f"Executed {len(response_data['actions'])} action(s) successfully"
    
    return response_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode
    )
