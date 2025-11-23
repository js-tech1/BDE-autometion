"""
Email Agent - Handles automated email generation and sending
"""
from typing import Dict, Any, Optional
from database import Lead, Email, EmailStatus, Activity
from sqlalchemy.orm import Session
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings


class EmailAgent:
    """Agent responsible for email generation and outreach"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_email(self, lead_id: int, email_type: str = "initial") -> Dict[str, Any]:
        """Generate a personalized email for a lead using AI agent"""
        try:
            # Get lead from database
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            
            if not lead:
                raise ValueError(f"Lead with ID {lead_id} not found")
            
            # Ensure lead has required fields with safe defaults
            company_name = lead.company_name or "Your Company"
            contact_name = lead.contact_name or "there"
            industry = lead.industry or "Business"
            
            # Generate subject line based on lead data
            subject_templates = [
                f"Partnership Opportunity for {company_name}",
                f"How {company_name} Can Increase Efficiency by 40%",
                f"Quick Question for {contact_name}",
                f"Helping {industry} Companies Scale Faster",
                f"{contact_name}, I Have an Idea for {company_name}",
                f"Revolutionizing {industry} with AI Automation",
                f"{contact_name} - Let's Talk About {company_name}'s Growth",
                f"Exclusive Offer for {company_name}",
                f"Transform {company_name}'s Operations",
                f"Quick Win for {industry} Leaders Like You"
            ]
            
            import random
            subject = random.choice(subject_templates)
        
            # Multiple body templates for variety
            body_templates = [
                # Template 1: ROI Focus
                f"""Hi {contact_name},

I came across {company_name} and was impressed by your work in the {industry} space.

We've helped similar companies in {industry} increase their operational efficiency by 40% and reduce manual tasks by 70% through intelligent automation. Companies like yours typically see ROI within 2-3 months.

Would you be open to a quick 15-minute conversation to explore how we could help {company_name} achieve similar results? No pressure – just sharing what's worked for others.

Best regards,
BDE Automation Team

P.S. If timing isn't right, I completely understand. Feel free to reach out when it makes sense.""",

                # Template 2: Problem-Solution
                f"""Hello {contact_name},

I noticed {company_name} is doing great work in {industry}. I wanted to reach out because we're helping companies like yours solve a common challenge.

Many {industry} leaders tell us they're spending too much time on repetitive tasks. Our AI-powered automation has helped clients:
• Save 15+ hours per week
• Reduce errors by 85%
• Scale without hiring more staff

Would you be interested in a brief call to see if we could help {company_name} achieve similar results?

Warm regards,
BDE Automation Team""",

                # Template 3: Social Proof
                f"""Hi {contact_name},

I've been following {company_name}'s growth in the {industry} sector and wanted to share something that might interest you.

We recently helped three companies in {industry} automate their workflows, resulting in:
→ 40% faster deal closure
→ 70% reduction in manual data entry
→ 3x increase in lead conversion

I'd love to show you how {company_name} could achieve similar outcomes. Are you available for a quick 10-minute call this week?

Cheers,
BDE Automation Team""",

                # Template 4: Direct Value
                f"""Dear {contact_name},

Quick question: Is {company_name} looking to streamline operations and boost productivity?

We specialize in helping {industry} businesses like yours automate time-consuming tasks. Our clients typically:
✓ Reduce operational costs by 30%
✓ Improve team productivity by 50%
✓ Close deals 40% faster

If you're open to exploring how this could work for {company_name}, I'd be happy to share a quick demo.

Best,
BDE Automation Team

P.S. No obligation – just sharing what's helped other {industry} leaders.""",

                # Template 5: Personalized Insight
                f"""Hi {contact_name},

I came across {company_name} while researching innovative companies in {industry}.

What caught my attention is how companies like yours can benefit from AI-powered automation. We've worked with similar organizations to:
• Automate lead qualification and follow-ups
• Generate personalized client communications
• Track and analyze sales metrics in real-time

I believe {company_name} could see significant value. Would you be open to a brief conversation?

Looking forward to connecting,
BDE Automation Team"""
            ]
            
            # Pick a random body template
            body = random.choice(body_templates)
            
            # Ensure email field exists and is valid
            recipient_email = lead.email
            if not recipient_email or "@" not in recipient_email:
                raise ValueError(f"Invalid email address for lead {lead_id}")
            
            # Create email record in database
            email = Email(
                lead_id=lead.id,
                subject=subject,
                body=body,
                recipient_email=recipient_email,
                status=EmailStatus.DRAFT
            )
            
            self.db.add(email)
            self.db.commit()
            self.db.refresh(email)
            
            return {
                "email_id": email.id,
                "lead_id": lead.id,
                "subject": email.subject,
                "body": email.body,
                "status": email.status.value
            }
            
        except Exception as e:
            # Rollback on error and re-raise with clear message
            self.db.rollback()
            raise ValueError(f"Failed to generate email for lead {lead_id}: {str(e)}")
    
    def generate_followup_email(self, lead: Lead) -> tuple:
        """Generate a personalized follow-up email for a lead"""
        import random
        from datetime import datetime
        
        # Add variety with time-based and random elements
        time_of_day = datetime.now().hour
        greeting = "Hi" if time_of_day < 12 else "Hello" if time_of_day < 17 else "Good evening"
        
        # Follow-up subject lines (8 variations)
        followup_subjects = [
            f"Following up - {lead.company_name}",
            f"{greeting} {lead.contact_name}, quick question",
            f"Re: Automation opportunities for {lead.company_name}",
            f"Still interested, {lead.contact_name}?",
            f"Thought you'd find this interesting",
            f"{lead.company_name} + Automation = 💡",
            f"Quick check-in about our last conversation",
            f"Did you get a chance to review this?"
        ]
        
        # Industry-specific pain points for personalization
        industry_examples = {
            'saas': 'reducing customer onboarding time by 50%',
            'fintech': 'automating compliance reports and saving 20 hours/week',
            'retail': 'streamlining inventory management and reducing stockouts',
            'healthcare': 'digitizing patient workflows and improving appointment scheduling',
            'construction': 'automating project tracking and resource allocation',
            'edtech': 'increasing student engagement through automated personalization',
            'ecommerce': 'reducing cart abandonment by 30% with smart automation'
        }
        
        industry_example = industry_examples.get(
            lead.industry.lower() if lead.industry else '',
            'automating repetitive tasks and saving 10+ hours/week'
        )
        
        # Follow-up email bodies (6 unique variations)
        followup_bodies = [
            # Template 1: Soft reminder with value
            f"""{greeting} {lead.contact_name},

I hope you've had a great week! I'm following up on my email about automation solutions for {lead.company_name}.

I know inboxes get crowded, so I wanted to resurface this because I genuinely think it could help. We recently worked with a {lead.industry or 'similar'} company on {industry_example}.

No pressure at all - but if you're curious, I'd love to share a 5-minute overview. Would Thursday or Friday work for a quick call?

Cheers,
BDE Automation Team

P.S. If timing isn't right, just let me know when would be better!""",

            # Template 2: Case study approach
            f"""Hello {lead.contact_name},

Quick follow-up - I wanted to share something relevant to {lead.company_name}.

**Real Results:** A {lead.industry or 'company'} we worked with last month saw:
→ 45% faster deal cycles
→ 3x improvement in lead response time  
→ Team freed up to focus on high-value work

The best part? Implementation took just 10 days.

Interested in seeing how this could work for {lead.company_name}? Let's schedule 15 minutes this week.

Best regards,
BDE Automation Team""",

            # Template 3: Problem-solution
            f"""{greeting} {lead.contact_name},

Circling back on my last email. I've been thinking about challenges {lead.industry or 'companies like yours'} typically face.

Most tell us they're frustrated with:
• Manual data entry eating up valuable time
• Leads slipping through the cracks
• Inconsistent follow-up processes

Does any of this resonate with {lead.company_name}'s situation?

If so, I have some ideas that might help. Want to chat briefly?

Warm regards,
BDE Automation Team""",

            # Template 4: Direct and concise
            f"""{lead.contact_name},

Following up on my automation proposal for {lead.company_name}.

**3 Quick Questions:**
1. Are manual processes slowing your team down?
2. Interested in {industry_example}?
3. Have 10 minutes this week for a demo?

If yes to any of these, let's talk. If not, no worries - I'll stop reaching out.

Reply either way so I know where you stand?

Thanks,
BDE Automation Team""",

            # Template 5: Resource sharing
            f"""Hi {lead.contact_name},

I don't want to clutter your inbox, but I thought this might be valuable for {lead.company_name}.

I put together a brief overview of how {lead.industry or 'businesses'} are using automation to:
✓ Save 15-20 hours per week on admin tasks
✓ Increase conversion rates by 40%
✓ Eliminate data entry errors

Would you like me to send it over? It's a 2-minute read with real examples.

Looking forward to your thoughts!

Best,
BDE Automation Team""",

            # Template 6: Personalized insight
            f"""Hello {lead.contact_name},

I was researching {lead.company_name} and noticed you're in the {lead.industry or 'business'} space - exciting work!

Based on what I've seen, there might be some quick wins with automation:
• {industry_example.capitalize()}
• Faster customer response times
• Better pipeline visibility

Worth a conversation? I can show you exactly what this looks like in 10 minutes.

What does your calendar look like Thursday afternoon?

Cheers,
BDE Automation Team"""
        ]
        
        subject = random.choice(followup_subjects)
        body = random.choice(followup_bodies)
        
        return (subject, body)
    
    def send_email_sync(self, email_id: int) -> Dict[str, Any]:
        """Send an email using synchronous SMTP"""
        # Get email from database
        email = self.db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            raise ValueError(f"Email with ID {email_id} not found")
        
        if email.status == EmailStatus.SENT:
            return {
                "email_id": email.id,
                "status": "already_sent",
                "message": "Email was already sent"
            }
        
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = f"{settings.sender_name} <{settings.sender_email}>"
            message["To"] = email.recipient_email
            message["Subject"] = email.subject
            
            # Add body
            message.attach(MIMEText(email.body, "plain"))
            
            # Send email using synchronous SMTP
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                smtp.starttls()  # Secure connection
                smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
            
            # Update email status
            email.status = EmailStatus.SENT
            email.sent_at = datetime.utcnow()
            
            # Update lead
            lead = self.db.query(Lead).filter(Lead.id == email.lead_id).first()
            if lead:
                lead.last_contacted_at = datetime.utcnow()
                if lead.status.value == "new" or lead.status.value == "qualified":
                    from database import LeadStatus
                    lead.status = LeadStatus.CONTACTED
            
            # Log activity
            activity = Activity(
                lead_id=email.lead_id,
                activity_type="email_sent",
                description=f"Email sent: {email.subject}",
                activity_metadata=f"email_id: {email.id}"
            )
            self.db.add(activity)
            
            self.db.commit()
            
            return {
                "email_id": email.id,
                "status": "sent",
                "sent_at": email.sent_at.isoformat()
            }
            
        except Exception as e:
            # Update email with error
            email.status = EmailStatus.FAILED
            email.error_message = str(e)
            email.retry_count += 1
            self.db.commit()
            
            return {
                "email_id": email.id,
                "status": "failed",
                "error": str(e)
            }
    
    async def send_email(self, email_id: int) -> Dict[str, Any]:
        """Send an email (async version - kept for compatibility)"""
        return self.send_email_sync(email_id)
    
    def get_pending_emails(self) -> list:
        """Get all draft emails ready to send"""
        emails = self.db.query(Email).filter(Email.status == EmailStatus.DRAFT).all()
        
        return [
            {
                "email_id": email.id,
                "lead_id": email.lead_id,
                "recipient": email.recipient_email,
                "subject": email.subject
            }
            for email in emails
        ]
    
    def retry_failed_emails(self) -> list:
        """Retry sending failed emails"""
        failed_emails = self.db.query(Email).filter(
            Email.status == EmailStatus.FAILED,
            Email.retry_count < settings.max_email_retries
        ).all()
        
        results = []
        for email in failed_emails:
            email.status = EmailStatus.DRAFT
            self.db.commit()
            results.append({"email_id": email.id, "status": "queued_for_retry"})
        
        return results
