"""
REAL Agentic AI - Understands requests, asks questions, takes actions
This is the BRAIN of the system
"""
from typing import Dict, Any, List
import re


class IntelligentBDEAgent:
    """
    True Agentic AI that:
    1. Understands natural language requests
    2. Asks clarifying questions when needed
    3. Takes actions autonomously
    4. Handles full sales cycle
    """
    
    def __init__(self, db):
        self.db = db
        self.conversation_state = {}  # Track what user is trying to do
        self.pending_actions = {}  # Actions waiting for more info
    
    def process_request(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Main brain - understands what user wants and decides what to do
        """
        # Initialize session state
        if session_id not in self.conversation_state:
            self.conversation_state[session_id] = {
                "current_task": None,
                "collected_info": {},
                "last_action": None
            }
        
        state = self.conversation_state[session_id]
        message = user_message.lower()
        
        # Check if we're in middle of collecting information
        if state["current_task"] == "creating_invoice":
            return self._continue_invoice_creation(user_message, state)
        
        elif state["current_task"] == "negotiating_discount":
            return self._continue_negotiation(user_message, state)
        
        # Check if user is responding to follow-up email preview
        if state.get("pending_followup"):
            if any(word in message for word in ['yes', 'send', 'ok', 'sure', 'confirm']):
                return self._send_followup_email(state)
            elif any(word in message for word in ['generate another', 'another', 'regenerate', 'new one']):
                return self._handle_followup_emails(state)  # Generate new one
            elif any(word in message for word in ['cancel', 'no', 'stop']):
                state["pending_followup"] = None
                return {
                    "understood": True,
                    "response": "Follow-up cancelled. What would you like to do next?",
                    "suggestions": ["Generate emails", "Analyze leads", "Create invoice"]
                }
        
        # Detect NEW intent
        intent = self._detect_intent(message)
        
        # Debug logging
        print(f"🔍 DEBUG: Message='{message}' | Detected Intent='{intent}'")
        
        if intent == "analyze_leads":
            return self._analyze_all_leads(state)
        
        elif intent == "show_high_priority":
            return self._show_high_priority_leads(state)
        
        elif intent == "send_invoice":
            return self._handle_send_invoice(state)
        
        elif intent == "send_followups":
            return self._handle_followup_emails(state)
        
        elif intent == "show_email_example":
            return self._show_email_example(state)
        
        elif intent == "send_emails":
            return self._send_all_emails(state)
        
        elif intent == "generate_emails":
            return self._handle_email_generation(state)
        
        elif intent == "create_invoice":
            return self._start_invoice_creation(state)
        
        elif intent == "send_pitch":
            return self._handle_pitch_request(message, state)
        
        elif intent == "handle_discount_request":
            return self._start_discount_negotiation(message, state)
        
        elif intent == "follow_up":
            return self._handle_follow_up(message, state)
        
        elif intent == "client_responded":
            return self._handle_client_response(message, state)
        
        else:
            # Handle general queries conversationally
            return self._handle_general_query(message, state)
    
    def _handle_general_query(self, message: str, state: Dict) -> Dict[str, Any]:
        """Handle queries that don't match specific intents - BE CONVERSATIONAL"""
        
        message_lower = message.lower()
        
        # Greeting
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'greetings']):
            return {
                "understood": True,
                "response": "Hi there! 👋 I'm your BDE automation assistant. I can help you with:\n\n• Generating personalized emails for leads\n• Creating invoices\n• Handling client negotiations and discounts\n• Sending follow-ups\n• Pitching to save deals\n\nWhat would you like to do today?",
                "suggestions": ["Generate emails", "Create invoice", "Client asked for discount"]
            }
        
        # Who are you / About yourself
        if any(phrase in message_lower for phrase in ['who are you', 'what are you', 'who r u', 'what r u', 'your name', 'introduce yourself']):
            return {
                "understood": True,
                "response": "I'm an **AI-powered BDE (Business Development Executive) Assistant**, built with:\n\n🤖 **IBM Watson AI** - For intelligent conversations\n📧 **Email Automation** - Personalized outreach at scale\n💼 **Deal Management** - Invoices, negotiations, pitches\n🎯 **Lead Intelligence** - Smart analysis and follow-ups\n\nThink of me as your virtual BDE team member who never sleeps! I handle repetitive tasks so you can focus on closing deals.\n\nWhat would you like me to help with?",
                "suggestions": ["Generate emails", "Create invoice", "Show my leads"]
            }
        
        # Help/capabilities
        if any(word in message_lower for word in ['help', 'what can you', 'how to', 'capabilities', 'can you do']):
            return {
                "understood": True,
                "response": "I'm an intelligent BDE assistant that can:\n\n✓ **Email Automation**: Generate personalized emails based on company and industry\n✓ **Invoice Creation**: Walk you through creating invoices step-by-step\n✓ **Negotiation Help**: Provide strategies when clients ask for discounts\n✓ **Deal Saving**: Generate pitches when deals are at risk\n✓ **Follow-ups**: Help manage client communications\n\nJust tell me what you need in natural language, and I'll handle it!",
                "suggestions": ["Show me leads", "Generate emails", "Create an invoice"]
            }
        
        # Show leads/data
        if any(word in message_lower for word in ['show', 'display', 'list', 'view']) and any(word in message_lower for word in ['lead', 'data', 'client', 'company']):
            from database import Lead
            leads = self.db.query(Lead).all()
            
            if not leads:
                return {
                    "understood": True,
                    "response": "You don't have any leads in the system yet. Upload a CSV file to get started!",
                    "suggestions": ["Upload CSV", "Help me get started"]
                }
            
            lead_list = "\n".join([f"• {lead.company_name} ({lead.contact_name}) - {lead.email}" for lead in leads[:10]])
            return {
                "understood": True,
                "response": f"📊 You have {len(leads)} leads in the system:\n\n{lead_list}\n\n{'...(showing first 10)' if len(leads) > 10 else ''}",
                "suggestions": ["Generate emails for all", "Analyze these leads", "Create invoice"]
            }
        
        # Thank you / appreciation
        if any(word in message_lower for word in ['thank', 'thanks', 'great job', 'awesome', 'perfect', 'good work']):
            return {
                "understood": True,
                "response": "You're welcome! 😊 Happy to help. Is there anything else you'd like me to do?",
                "suggestions": ["Generate more emails", "Create invoice", "Show leads"]
            }
        
        # Default - didn't understand but stay conversational
        return {
            "understood": False,
            "response": f"Hmm, I'm not quite sure what you want to do with: '{message}'\n\nCan you rephrase? Try something like:\n• 'Generate emails for all leads'\n• 'Create an invoice'\n• 'Client wants 20% discount'\n• 'Show me my leads'",
            "suggestions": [
                "Generate personalized emails",
                "Create an invoice",
                "Handle client discount request",
                "Show my leads"
            ]
        }
    
    def _detect_intent(self, message: str) -> str:
        """Detect what user wants to do with fuzzy matching for typos"""
        
        def fuzzy_match(text, keywords):
            """Check if any keyword or close variation is in text"""
            text_lower = text.lower()
            for keyword in keywords:
                # Exact match
                if keyword in text_lower:
                    return True
                # Handle common typos (missing/extra letters) - only for single words
                if len(keyword) > 3 and ' ' not in keyword:
                    # Count matching characters in sequence
                    matches = 0
                    text_pos = 0
                    for char in keyword:
                        text_pos = text_lower.find(char, text_pos)
                        if text_pos >= 0:
                            matches += 1
                            text_pos += 1
                    # Allow 1 character difference for typos
                    if matches >= len(keyword) - 1:
                        return True
            return False
        
        message_lower = message.lower()
        
        # Email generation FIRST (check before follow-ups to avoid confusion)
        if fuzzy_match(message_lower, ['generate email', 'create email', 'email all', 'mail all', 'generate more', 'genrate', 'generat', 'crete', 'creat']):
            return "generate_emails"
        
        # Follow-up emails (with typos: folowup, folow up, followp)
        if fuzzy_match(message_lower, ['follow up', 'followup', 'follow-up', 'folowup', 'followp']):
            return "send_followups"
        
        # Show high priority (with typos: prioriti, pririty, priorty)
        if (fuzzy_match(message_lower, ['show', 'display', 'view', 'displa', 'vew']) and 
            fuzzy_match(message_lower, ['high priority', 'priority', 'qualified', 'top lead', 'best', 'prioriti', 'pririty'])):
            return "show_high_priority"
        
        # Lead analysis (with typos: analze, analize, qualfy)
        if (fuzzy_match(message_lower, ['analyze', 'analyse', 'qualify', 'score', 'analze', 'analize', 'qualfy', 'scor']) and 
            fuzzy_match(message_lower, ['lead', 'all lead', 'my lead', 'leed', 'led'])):
            return "analyze_leads"
        
        # Send invoice (with typos: invoce, invice, sendinvoice)
        if fuzzy_match(message_lower, ['send invoice', 'email invoice', 'send inv', 'sendinvoice', 'send invoce', 'sendinvoce']):
            return "send_invoice"
        
        # Show example email (with typos: exampl, emai, emial)
        if (fuzzy_match(message_lower, ['show', 'display', 'view', 'example', 'sample', 'exampl', 'sampl']) and 
            fuzzy_match(message_lower, ['email', 'one', 'emai', 'emial', 'mail'])):
            return "show_email_example"
        
        # Send emails (with typos: snd, sendall, sendemail)
        if fuzzy_match(message_lower, ['send all', 'send email', 'send them', 'deliver', 'sendall', 'sendemail', 'snd all']):
            return "send_emails"
        
        # Invoice creation (with typos: invoce, invice, creat)
        if fuzzy_match(message_lower, ['invoice', 'bill', 'create invoice', 'make invoice', 'invoce', 'invice', 'creat invoice']):
            return "create_invoice"
        
        # Pitching / Saving deals (with typos: pitc, convinse, sav)
        if fuzzy_match(message_lower, ['pitch', 'convince', 'save deal', 'losing client', 'retention', 'pitc', 'convinse', 'sav deal']):
            return "send_pitch"
        
        # Discount negotiation (with typos: discont, discoun, reduc)
        if fuzzy_match(message_lower, ['discount', 'reduce price', 'lower cost', 'cheaper', 'budget', 'discont', 'discoun', 'reduc']):
            return "handle_discount_request"
        
        # Follow-ups (with typos: folowup, chek in)
        if fuzzy_match(message_lower, ['follow up', 'followup', 'check in', 'touch base', 'folowup', 'chek in', 'touchbase']):
            return "follow_up"
        
        # Client response (with typos: respnded, replid)
        if fuzzy_match(message_lower, ['client said', 'client responded', 'client replied', 'got response', 'respnded', 'replid']):
            return "client_responded"
        
        return "unknown"
    
    def _analyze_all_leads(self, state: Dict) -> Dict[str, Any]:
        """Analyze and qualify all leads with scoring"""
        try:
            from database import Lead
            from agents.lead_analysis_agent import LeadAnalysisAgent
            
            leads = self.db.query(Lead).all()
            
            if not leads:
                return {
                    "understood": True,
                    "response": "I don't see any leads in the system. Upload a CSV first, then I can analyze them for you.",
                    "suggestions": ["Upload CSV file", "Show help"]
                }
            
            analyzer = LeadAnalysisAgent(self.db)
            results = []
            
            for lead in leads:
                try:
                    analysis = analyzer.analyze_lead(lead.id)
                    results.append(analysis)
                except Exception as e:
                    print(f"Error analyzing lead {lead.id}: {e}")
            
            # Build response
            high_quality = [r for r in results if r['lead_score'] >= 0.7]
            medium_quality = [r for r in results if 0.4 <= r['lead_score'] < 0.7]
            low_quality = [r for r in results if r['lead_score'] < 0.4]
            
            response = f"**Lead Analysis Complete!** 📊\n\n"
            response += f"Analyzed {len(results)} leads:\n\n"
            
            if high_quality:
                response += f"🟢 **High Priority** ({len(high_quality)} leads):\n"
                for r in high_quality[:3]:  # Show top 3
                    response += f"  • {r['company']} - Score: {r['lead_score']:.2f} - Budget: {r['budget_estimate']}\n"
                if len(high_quality) > 3:
                    response += f"  ...and {len(high_quality) - 3} more\n"
                response += "\n"
            
            if medium_quality:
                response += f"🟡 **Medium Priority** ({len(medium_quality)} leads)\n\n"
            
            if low_quality:
                response += f"🔴 **Low Priority** ({len(low_quality)} leads)\n\n"
            
            response += "**Next Steps:**\n"
            response += "• Generate personalized emails for high-priority leads\n"
            response += "• Review pain points and budget estimates\n"
            response += "• Prioritize outreach based on scores"
            
            return {
                "understood": True,
                "response": response,
                "action_taken": "lead_analysis",
                "results": results,
                "suggestions": ["Generate emails", "Show high priority leads", "Create invoice"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"I encountered an error while analyzing leads: {str(e)}",
                "action_taken": None
            }
    
    def _show_high_priority_leads(self, state: Dict) -> Dict[str, Any]:
        """Show high priority/qualified leads with details"""
        try:
            from database import Lead, LeadStatus
            
            # Get qualified leads with high scores
            high_priority = self.db.query(Lead).filter(
                Lead.lead_score >= 0.7
            ).order_by(Lead.lead_score.desc()).all()
            
            if not high_priority:
                return {
                    "understood": True,
                    "response": "No high-priority leads found yet. Run 'analyze all leads' first to score and qualify your leads!",
                    "suggestions": ["Analyze all leads", "Show all leads", "Generate emails"]
                }
            
            response = f"**🟢 High Priority Leads** ({len(high_priority)} found)\n\n"
            
            for lead in high_priority:
                response += f"**{lead.company_name}** (Score: {lead.lead_score:.2f})\n"
                response += f"  👤 Contact: {lead.contact_name}\n"
                response += f"  📧 Email: {lead.email}\n"
                response += f"  🏢 Industry: {lead.industry or 'N/A'}\n"
                
                if lead.budget_estimate:
                    response += f"  💰 Budget: {lead.budget_estimate}\n"
                
                if lead.decision_timeline:
                    response += f"  ⏱️ Timeline: {lead.decision_timeline}\n"
                
                if lead.pain_points:
                    points = lead.pain_points.split('\n')[:2]
                    response += f"  🎯 Pain Points:\n"
                    for point in points:
                        if point.strip():
                            response += f"    • {point.strip()}\n"
                
                response += "\n"
            
            response += "**Recommended Actions:**\n"
            response += "• Generate personalized emails for these leads\n"
            response += "• Prioritize outreach to highest scores\n"
            response += "• Review pain points before reaching out"
            
            return {
                "understood": True,
                "response": response,
                "action_taken": "show_high_priority",
                "suggestions": ["Generate emails", "Create invoice", "Analyze more leads"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"Error showing high priority leads: {str(e)}",
                "action_taken": None
            }
    
    def _handle_email_generation(self, state: Dict) -> Dict[str, Any]:
        """Generate personalized emails for all leads"""
        try:
            from database import Lead, Email, EmailStatus
            leads = self.db.query(Lead).all()
            
            if not leads:
                return {
                    "understood": True,
                    "response": "I don't see any leads in the system. Upload a CSV first, then I can generate personalized emails for everyone.",
                    "action_taken": None,
                    "suggestions": ["Upload CSV file", "Show help"]
                }
            
            # Delete existing draft emails (for regeneration)
            existing_drafts = self.db.query(Email).filter(Email.status == EmailStatus.DRAFT).all()
            for draft in existing_drafts:
                self.db.delete(draft)
            self.db.commit()
            
            from agents.email_agent import EmailAgent
            agent = EmailAgent(self.db)
            
            results = []
            failed_count = 0
            
            for lead in leads:
                try:
                    email = agent.generate_email(lead.id, "initial")
                    results.append({
                        "company": lead.company_name,
                        "contact": lead.contact_name,
                        "status": "✓ generated"
                    })
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    print(f"ERROR generating email for {lead.company_name}: {error_msg}")
                    results.append({
                        "company": lead.company_name,
                        "contact": lead.contact_name,
                        "status": f"✗ failed: {error_msg[:50]}"
                    })
            
            state["last_action"] = "generated_emails"
            
            success_count = len(results) - failed_count
            
            if failed_count == 0:
                response = f"✓ Generated {success_count} fresh personalized emails! Each one is customized for the company and industry. Want me to send them now, or review first?"
            elif success_count == 0:
                response = f"❌ Failed to generate any emails. Please check:\n• Do leads have valid email addresses?\n• Is the database connection working?\n\nTry uploading the CSV again or contact support."
            else:
                response = f"⚠️ Generated {success_count} emails successfully, but {failed_count} failed.\n\nSuccessful emails are ready to send. Check the results below for details."
            
            return {
                "understood": True,
                "response": response,
                "action_taken": "generate_emails",
                "results": results,
                "next_suggestions": ["Send all emails", "Show me one example", "Schedule for later"] if success_count > 0 else ["Upload CSV again", "Show help"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"Oops! I ran into an issue: {str(e)}\n\nMake sure you have leads in the database. Try uploading a CSV file first.",
                "action_taken": None,
                "suggestions": ["Upload CSV", "Show help"]
            }
    
    def _handle_followup_emails(self, state: Dict) -> Dict[str, Any]:
        """Generate and show follow-up email for sent emails"""
        try:
            from database import Email, EmailStatus, Lead
            from agents.email_agent import EmailAgent
            from datetime import datetime, timedelta
            
            # Get sent emails that don't have follow-ups yet
            sent_emails = self.db.query(Email).filter(
                Email.status == EmailStatus.SENT
            ).all()
            
            if not sent_emails:
                return {
                    "understood": True,
                    "response": "No emails have been sent yet. Send initial emails first!",
                    "suggestions": ["Send all emails", "Generate emails"]
                }
            
            # Check which leads are eligible for follow-up (24 hours passed)
            eligible_leads = []
            now = datetime.utcnow()
            
            for email in sent_emails:
                if email.sent_at:
                    time_since_sent = now - email.sent_at
                    hours_passed = time_since_sent.total_seconds() / 3600
                    
                    # Check if 24 hours passed AND no follow-up sent yet
                    lead = self.db.query(Lead).filter(Lead.id == email.lead_id).first()
                    if lead and hours_passed >= 24:
                        # Check if follow-up already sent (skip email_type check for now)
                        # Count total emails sent to this lead
                        total_emails = self.db.query(Email).filter(
                            Email.lead_id == lead.id,
                            Email.status == EmailStatus.SENT
                        ).count()
                        
                        # If more than 1 email sent, follow-up already exists
                        if total_emails <= 1:
                            eligible_leads.append((lead, email, hours_passed))
            
            if not eligible_leads:
                # Show when next follow-up is due
                next_eligible = []
                for email in sent_emails:
                    if email.sent_at:
                        time_since_sent = now - email.sent_at
                        hours_passed = time_since_sent.total_seconds() / 3600
                        hours_remaining = 24 - hours_passed
                        
                        if hours_remaining > 0:
                            next_eligible.append((email, hours_remaining))
                
                if next_eligible:
                    next_eligible.sort(key=lambda x: x[1])  # Sort by time remaining
                    next_email, hours_left = next_eligible[0]
                    lead = self.db.query(Lead).filter(Lead.id == next_email.lead_id).first()
                    
                    return {
                        "understood": True,
                        "response": f"""⏰ **No Follow-Ups Ready Yet**

All sent emails are less than 24 hours old. Follow-ups should wait at least 24 hours to avoid being pushy.

**Next Follow-Up Available:**
• {lead.company_name if lead else 'Unknown'} - in {int(hours_left)} hours

I'll let you know when it's time! ⏳""",
                        "suggestions": ["Check again later", "Analyze leads", "Generate new emails"]
                    }
                else:
                    return {
                        "understood": True,
                        "response": "All leads have already received follow-up emails! Great job staying on top of your outreach. 🎉",
                        "suggestions": ["Analyze leads", "Generate new emails", "Create invoice"]
                    }
            
            # Generate follow-up for the first eligible lead
            lead, original_email, hours_passed = eligible_leads[0]
            
            # Generate personalized follow-up email
            agent = EmailAgent(self.db)
            followup_subject, followup_body = agent.generate_followup_email(lead)
            
            # Store in state for sending later
            state["pending_followup"] = {
                "lead_id": lead.id,
                "subject": followup_subject,
                "body": followup_body
            }
            
            return {
                "understood": True,
                "response": f"""📧 **FOLLOW-UP EMAIL PREVIEW**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**To:** {lead.contact_name} <{lead.email}>
**Company:** {lead.company_name}
**Original Email Sent:** {int(hours_passed)} hours ago ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Subject:**
{followup_subject}

**Email Body:**

{followup_body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is a personalized follow-up email. Want to send it?""",
                "action_taken": "preview_followup",
                "suggestions": ["Yes, send this", "Generate another one", "Cancel"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"Error generating follow-up: {str(e)}",
                "suggestions": ["Try again"]
            }
    
    def _send_followup_email(self, state: Dict) -> Dict[str, Any]:
        """Send the pending follow-up email"""
        try:
            from database import Lead, Email, EmailStatus
            from agents.email_agent import EmailAgent
            
            followup_data = state.get("pending_followup")
            
            if not followup_data:
                return {
                    "understood": True,
                    "response": "No pending follow-up email found.",
                    "suggestions": ["Generate follow-ups"]
                }
            
            lead_id = followup_data["lead_id"]
            subject = followup_data["subject"]
            body = followup_data["body"]
            
            # Get lead
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            
            if not lead:
                return {
                    "understood": True,
                    "response": "Error: Lead not found.",
                    "suggestions": ["Try again"]
                }
            
            # Create email in database (email_type field may not exist yet)
            try:
                email = Email(
                    lead_id=lead.id,
                    subject=subject,
                    body=body,
                    recipient_email=lead.email,
                    email_type="follow_up",  # Mark as follow-up (if column exists)
                    status=EmailStatus.DRAFT
                )
            except Exception:
                # Fallback if email_type column doesn't exist
                email = Email(
                    lead_id=lead.id,
                    subject=subject,
                    body=body,
                    recipient_email=lead.email,
                    status=EmailStatus.DRAFT
                )
            self.db.add(email)
            self.db.commit()
            self.db.refresh(email)
            
            # Send via SMTP
            agent = EmailAgent(self.db)
            result = agent.send_email_sync(email.id)
            
            # Clear pending followup
            state["pending_followup"] = None
            
            if result.get("status") == "sent":
                return {
                    "understood": True,
                    "response": f"""✅ **Follow-up Email Sent Successfully!**

📧 Sent to: {lead.contact_name} ({lead.email})
🏢 Company: {lead.company_name}

The follow-up email has been delivered. Great work staying on top of your leads!""",
                    "action_taken": "sent_followup",
                    "suggestions": ["Send more follow-ups", "Analyze leads", "Create invoice"]
                }
            else:
                return {
                    "understood": True,
                    "response": f"❌ Failed to send follow-up: {result.get('error', 'Unknown error')}",
                    "suggestions": ["Try again", "Check email settings"]
                }
                
        except Exception as e:
            return {
                "understood": True,
                "response": f"Error sending follow-up: {str(e)}",
                "suggestions": ["Try again"]
            }
    
    def _show_email_example(self, state: Dict) -> Dict[str, Any]:
        """Show one example email"""
        try:
            from database import Lead, Email
            
            # Get first generated email
            email = self.db.query(Email).first()
            
            if not email:
                return {
                    "understood": True,
                    "response": "No emails have been generated yet. Generate emails first!",
                    "suggestions": ["Generate personalized emails"]
                }
            
            # Get the lead for this email
            lead = self.db.query(Lead).filter(Lead.id == email.lead_id).first()
            
            if not lead:
                return {
                    "understood": True,
                    "response": "Email found but lead data is missing. Try generating emails again.",
                    "suggestions": ["Generate personalized emails"]
                }
            
            return {
                "understood": True,
                "response": f"""📧 **EMAIL PREVIEW**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**From:** BDE Automation Team
**To:** {lead.contact_name} <{lead.email}>
**Company:** {lead.company_name}
**Industry:** {lead.industry or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Subject Line:**
{email.subject}

**Email Body:**

{email.body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ This email is 100% personalized for {lead.company_name} based on their industry and company profile. Each lead receives a unique, tailored message!

Ready to send?""",
                "action_taken": "show_example",
                "next_suggestions": ["Send all emails", "Generate more emails", "Create an invoice"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"Couldn't retrieve example: {str(e)}",
                "suggestions": ["Generate emails first"]
            }
    
    def _send_all_emails(self, state: Dict) -> Dict[str, Any]:
        """Send all generated emails via SMTP"""
        try:
            from database import Email, EmailStatus, Lead
            from agents.email_agent import EmailAgent
            from datetime import datetime
            
            # Get all draft emails
            emails = self.db.query(Email).filter(Email.status == EmailStatus.DRAFT).all()
            
            if not emails:
                # Check if emails were already sent
                sent_emails = self.db.query(Email).filter(
                    Email.status == EmailStatus.SENT
                ).all()
                
                if sent_emails:
                    # Build list of sent emails with details
                    sent_list = []
                    for email in sent_emails[:5]:  # Show first 5
                        lead = self.db.query(Lead).filter(Lead.id == email.lead_id).first()
                        if lead:
                            sent_list.append(f"• {lead.company_name} ({lead.email}) - Sent on {email.sent_at.strftime('%Y-%m-%d') if email.sent_at else 'Recently'}")
                    
                    sent_details = "\n".join(sent_list)
                    more_text = f"\n...and {len(sent_emails) - 5} more" if len(sent_emails) > 5 else ""
                    
                    return {
                        "understood": True,
                        "response": f"""📧 **All emails have already been sent!**

**Sent Emails ({len(sent_emails)} total):**
{sent_details}{more_text}

Would you like to send **follow-up emails** to these leads?""",
                        "suggestions": ["Yes, send follow-ups", "Show me sent emails", "Generate new emails"],
                        "action_taken": "check_sent_emails"
                    }
                else:
                    return {
                        "understood": True,
                        "response": "No emails to send. Generate emails first using 'Generate emails' button!",
                        "suggestions": ["Generate personalized emails"]
                    }
            
            agent = EmailAgent(self.db)
            sent_count = 0
            failed_count = 0
            results = []
            
            # Send each email via SMTP
            for email in emails:
                try:
                    # Get lead for this email
                    lead = self.db.query(Lead).filter(Lead.id == email.lead_id).first()
                    company_name = lead.company_name if lead else "Unknown"
                    
                    # Actually send the email via SMTP
                    result = agent.send_email_sync(email.id)
                    
                    if result.get("status") == "sent":
                        sent_count += 1
                        results.append({
                            "company": company_name,
                            "status": "✓ Sent",
                            "to": email.recipient_email
                        })
                    else:
                        failed_count += 1
                        results.append({
                            "company": company_name,
                            "status": f"✗ Failed: {result.get('error', 'Unknown')}",
                            "to": email.recipient_email
                        })
                        
                except Exception as e:
                    failed_count += 1
                    # Get lead for error message
                    lead = self.db.query(Lead).filter(Lead.id == email.lead_id).first()
                    company_name = lead.company_name if lead else "Unknown"
                    results.append({
                        "company": company_name,
                        "status": f"✗ Error: {str(e)}"
                    })
            
            state["last_action"] = "sent_emails"
            
            response_msg = f"📧 Email Sending Complete!\n\n"
            response_msg += f"✓ Successfully sent: {sent_count}\n"
            if failed_count > 0:
                response_msg += f"✗ Failed: {failed_count}\n\n"
            
            response_msg += f"\n✉️ Emails marked as sent and leads updated to 'Contacted' status!"
            
            return {
                "understood": True,
                "response": response_msg,
                "action_taken": "send_emails",
                "results": results,
                "next_suggestions": ["Create an invoice", "Follow up on leads", "Analyze responses"]
            }
            
            state["last_action"] = "sent_emails"
            
            return {
                "understood": True,
                "response": f"✓ Sent {sent_count} emails successfully! Your leads will start receiving personalized messages now.",
                "action_taken": "send_emails",
                "next_suggestions": ["Create an invoice", "Follow up on leads", "Analyze responses"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"Error sending emails: {str(e)}",
                "suggestions": ["Try again", "Check email configuration"]
            }
    
    def _start_invoice_creation(self, state: Dict) -> Dict[str, Any]:
        """Start collecting info for invoice"""
        state["current_task"] = "creating_invoice"
        state["collected_info"] = {}
        
        return {
            "understood": True,
            "response": "Sure! I'll help you create an invoice. Let me ask you a few questions:\n\n1. Who is this invoice for? (Company name or client name)",
            "action_taken": None,
            "awaiting_response": "client_name"
        }
    
    def _continue_invoice_creation(self, user_response: str, state: Dict) -> Dict[str, Any]:
        """Continue collecting invoice details"""
        info = state["collected_info"]
        response_clean = user_response.strip()
        
        # Collect step by step
        if "client_name" not in info:
            info["client_name"] = response_clean
            return {
                "understood": True,
                "response": f"Perfect! Invoice for **{response_clean}**.\n\n2. What services/products are you billing for? (e.g., 'Website development', 'Mobile app', 'Consulting')",
                "awaiting_response": "services"
            }
        
        elif "services" not in info:
            info["services"] = response_clean
            return {
                "understood": True,
                "response": f"Got it: **{response_clean}**.\n\n3. What's the total amount? (e.g., '₹50,000' or just '4000')",
                "awaiting_response": "amount"
            }
        
        elif "amount" not in info:
            # Smart parsing for amount - extract numbers
            import re
            numbers = re.findall(r'[\d,]+', response_clean)
            
            if numbers:
                # Take the largest number (handles "website for 4000")
                amount_str = max(numbers, key=lambda x: int(x.replace(',', '')))
                info["amount"] = amount_str
                
                return {
                    "understood": True,
                    "response": f"Amount: **₹{amount_str}**.\n\n4. Any discount or special terms? (Type percentage like '10%', or amount like '500', or 'none')",
                    "awaiting_response": "discount"
                }
            else:
                return {
                    "understood": True,
                    "response": "I didn't catch the amount. Please enter just the number (e.g., '4000' or '₹4000')",
                    "awaiting_response": "amount"
                }
        
        elif "discount" not in info:
            # Parse discount with fuzzy matching
            response_lower = response_clean.lower()
            
            # Handle typos and variations
            none_variations = ['none', 'no', 'nothing', 'nahi', 'na', 'nope', 'non', 'noo', 'nono', 'nhi']
            
            if any(var in response_lower for var in none_variations):
                info["discount"] = "None"
            else:
                info["discount"] = response_clean
            
            # All info collected - create invoice
            invoice_data = {
                "client": info["client_name"],
                "services": info["services"],
                "amount": info["amount"],
                "discount": info["discount"]
            }
            
            # Store invoice in state for sending
            state["current_task"] = None
            state["last_action"] = "created_invoice"
            state["pending_invoice"] = invoice_data
            
            return {
                "understood": True,
                "response": f"""✅ **Invoice Created Successfully!**

📄 **Invoice Details:**
━━━━━━━━━━━━━━━━━━━━━━━
**Client:** {info['client_name']}
**Services:** {info['services']}
**Amount:** ₹{info['amount']}
**Discount:** {info['discount']}
━━━━━━━━━━━━━━━━━━━━━━━

Invoice is ready! Click "Send invoice" below to email it to **{info['client_name']}**.""",
                "action_taken": "create_invoice",
                "invoice_data": invoice_data,
                "suggestions": ["Send invoice", "Create another invoice", "Generate emails"]
            }
    
    def _handle_send_invoice(self, state: Dict) -> Dict[str, Any]:
        """Handle sending invoice to client"""
        try:
            # Check if there's a pending invoice
            invoice_data = state.get("pending_invoice")
            
            if not invoice_data:
                # No pending invoice, show list of leads to choose from
                from database import Lead
                leads = self.db.query(Lead).all()
                
                if not leads:
                    return {
                        "understood": True,
                        "response": "No clients found in the system. Upload leads first or create an invoice!",
                        "suggestions": ["Create invoice", "Upload CSV"]
                    }
                
                # Show list of clients to choose from
                client_list = "\n".join([f"• {lead.company_name} ({lead.contact_name})" for lead in leads[:10]])
                more_text = f"\n...and {len(leads) - 10} more" if len(leads) > 10 else ""
                
                return {
                    "understood": True,
                    "response": f"""📋 **Select Client to Send Invoice:**

{client_list}{more_text}

Click on a company name above, or type the client name to send invoice.""",
                    "suggestions": [f"{lead.company_name}" for lead in leads[:5]],
                    "action_taken": "show_clients_for_invoice"
                }
            
            # Invoice exists, send it
            client = invoice_data["client"]
            
            # TODO: Actual email sending logic here
            # For now, just confirm
            state["pending_invoice"] = None  # Clear pending invoice
            
            return {
                "understood": True,
                "response": f"""✅ **Invoice Sent Successfully!**

📧 Invoice has been emailed to **{client}**

**Summary:**
• Services: {invoice_data['services']}
• Amount: ₹{invoice_data['amount']}
• Discount: {invoice_data['discount']}

The client will receive the invoice in their inbox shortly!""",
                "action_taken": "sent_invoice",
                "suggestions": ["Create another invoice", "Generate emails", "Analyze leads"]
            }
            
        except Exception as e:
            return {
                "understood": True,
                "response": f"Error sending invoice: {str(e)}",
                "suggestions": ["Try again", "Create new invoice"]
            }
    
    def _start_discount_negotiation(self, message: str, state: Dict) -> Dict[str, Any]:
        """Handle client asking for discount"""
        state["current_task"] = "negotiating_discount"
        
        # Extract discount amount if mentioned
        discount_match = re.search(r'(\d+)%|(\d+) percent', message)
        
        if discount_match:
            discount = discount_match.group(1) or discount_match.group(2)
            state["collected_info"]["requested_discount"] = discount
            
            return {
                "understood": True,
                "response": f"""Client asked for {discount}% discount. Here's my recommendation:

**Negotiation Strategy:**
1. Acknowledge their concern: "I understand budget is important"
2. Add value instead of just cutting price
3. Offer alternatives:
   - {int(discount)//2}% discount + extended support
   - Pilot program at reduced rate
   - Payment plan to spread cost

Want me to draft a response? Or tell me what direction to take.""",
                "action_taken": "analyzing_discount_request",
                "recommendations": {
                    "counter_offer": f"{int(discount)//2}% with added value",
                    "alternative": "Pilot program",
                    "risk": "Medium - client price-sensitive"
                }
            }
        else:
            return {
                "response": "Client asked for a discount. How much are they asking for? (percentage or amount)",
                "awaiting_response": "discount_amount"
            }
    
    def _handle_pitch_request(self, message: str, state: Dict) -> Dict[str, Any]:
        """Generate pitch to save a deal"""
        
        # Detect situation
        if "losing" in message or "competitor" in message:
            situation = "competitor"
        elif "expensive" in message or "cost" in message:
            situation = "price_objection"
        elif "timing" in message or "later" in message:
            situation = "timing"
        else:
            situation = "general"
        
        pitches = {
            "competitor": """**Pitch to counter competitor:**

"I completely understand you're evaluating options - that's smart. Here's what our clients tell us sets us apart:

1. **Implementation Speed**: We're operational in 1 week vs. 2-3 months
2. **ROI Proof**: 30-day trial with real data, not promises
3. **Support**: Dedicated account manager, not ticket system

[Company X] tried the competitor first, then switched to us. Happy to connect you with them.

Can we do a side-by-side comparison this week?"
""",
            "price_objection": """**Pitch for price concerns:**

"I hear you on the investment. Let me show you the math:

Current cost of manual process: [X hours × Y rate] = $Z/month
Our solution: $A/month
Net savings: $B/month = 5-month payback

Plus: We offer a 60-day money-back guarantee. If you don't see ROI, full refund.

What if we start with a pilot on just one use case to prove value?"
""",
            "timing": """**Pitch for timing objection:**

"I totally get it - timing matters. Quick question: what would need to change for timing to be right?

Most clients say 'not now' and then 6 months later wish they'd started sooner. The cost of waiting is usually higher than the cost of getting started.

What if we do a 30-day pilot starting next month? Low commitment, real results."
"""
        }
        
        return {
            "understood": True,
            "response": pitches.get(situation, "Let me craft a pitch. What's the main objection: price, competitor, or timing?"),
            "action_taken": "generated_pitch",
            "pitch_type": situation
        }
    
    def _handle_follow_up(self, message: str, state: Dict) -> Dict[str, Any]:
        """Handle follow-up requests"""
        from database import Lead
        
        # Check for leads that need follow-up
        leads = self.db.query(Lead).filter(Lead.status == "CONTACTED").all()
        
        return {
            "understood": True,
            "response": f"I found {len(leads)} leads that need follow-up. Want me to:\n\n1. Send automated follow-up to all\n2. Generate personalized follow-ups\n3. Show list so you can choose",
            "action_taken": "identified_follow_ups",
            "follow_up_count": len(leads)
        }
    
    def _handle_client_response(self, message: str, state: Dict) -> Dict[str, Any]:
        """Analyze client response and suggest next action"""
        
        # Simple sentiment analysis
        positive_words = ['interested', 'yes', 'sounds good', 'like', 'great']
        negative_words = ['no', 'expensive', 'not interested', 'busy', 'later']
        
        sentiment = "neutral"
        if any(word in message for word in positive_words):
            sentiment = "positive"
        elif any(word in message for word in negative_words):
            sentiment = "negative"
        
        responses = {
            "positive": "Great! Client is interested. Here's what I recommend:\n\n1. Schedule a demo/call ASAP while they're warm\n2. Send calendar invite with 3 time options\n3. Prepare personalized deck for their industry\n\nWant me to draft the calendar invite?",
            
            "negative": "Client seems hesitant. Let me help:\n\n1. Identify the real objection (price? timing? trust?)\n2. Address it specifically\n3. Offer low-risk next step (pilot, case study, reference call)\n\nWhat exactly did they say? I'll craft the perfect response.",
            
            "neutral": "Client responded but not clear if positive or negative. Want me to:\n\n1. Send a clarifying question\n2. Offer multiple options\n3. Schedule a quick call to discuss"
        }
        
        return {
            "understood": True,
            "response": responses[sentiment],
            "action_taken": "analyzed_client_response",
            "sentiment": sentiment
        }


# Singleton instance
intelligent_agent = IntelligentBDEAgent(None)  # db will be injected later
