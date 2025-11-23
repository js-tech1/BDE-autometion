"""
IBM Watson AI integration for BDE Automation System
"""
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from config import settings
from typing import Dict, Any, Optional
import json


class IBMWatsonClient:
    """Client for IBM Watson Assistant integration"""
    
    def __init__(self):
        self.authenticator = IAMAuthenticator(settings.ibm_watson_api_key)
        self.assistant = AssistantV2(
            version='2023-06-15',
            authenticator=self.authenticator
        )
        self.assistant.set_service_url(settings.ibm_watson_url)
        self.session_id = None
    
    def create_session(self) -> str:
        """Create a new Watson Assistant session"""
        try:
            response = self.assistant.create_session(
                assistant_id=settings.ibm_watson_project_id
            ).get_result()
            self.session_id = response['session_id']
            return self.session_id
        except Exception as e:
            print(f"Error creating Watson session: {e}")
            raise
    
    def send_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to Watson Assistant"""
        if not session_id and not self.session_id:
            self.create_session()
        
        try:
            response = self.assistant.message(
                assistant_id=settings.ibm_watson_project_id,
                session_id=session_id or self.session_id,
                input={'text': message}
            ).get_result()
            return response
        except Exception as e:
            print(f"Error sending message to Watson: {e}")
            raise
    
    def analyze_lead_context(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead context using Watson"""
        prompt = f"""
        Analyze this lead and provide insights:
        Company: {lead_data.get('company_name')}
        Industry: {lead_data.get('industry')}
        Company Size: {lead_data.get('company_size')}
        Location: {lead_data.get('location')}
        
        Provide:
        1. Lead quality score (0-1)
        2. Potential pain points
        3. Recommended approach
        4. Estimated budget range
        """
        
        response = self.send_message(prompt)
        return self._parse_analysis_response(response)
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Watson response into structured format"""
        # Extract text from Watson response
        text = ""
        if 'output' in response and 'generic' in response['output']:
            for item in response['output']['generic']:
                if item.get('response_type') == 'text':
                    text += item.get('text', '')
        
        # Return structured data (simplified for demo)
        return {
            "analysis": text,
            "raw_response": response
        }
    
    def delete_session(self, session_id: Optional[str] = None):
        """Delete Watson Assistant session"""
        try:
            self.assistant.delete_session(
                assistant_id=settings.ibm_watson_project_id,
                session_id=session_id or self.session_id
            )
        except Exception as e:
            print(f"Error deleting Watson session: {e}")


# Global Watson client instance
watson_client = IBMWatsonClient()
