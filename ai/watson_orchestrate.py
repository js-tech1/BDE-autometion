"""
IBM Watson Orchestrate Integration
Uses real IBM credentials for AI-powered automation
"""
import requests
from typing import Dict, Any, Optional
from config import settings


class WatsonOrchestrate:
    """Client for IBM Watson Orchestrate API"""
    
    def __init__(self):
        self.api_key = settings.ibm_watson_api_key
        self.base_url = settings.ibm_watson_url
        self.instance_id = settings.ibm_watson_project_id
        self._iam_token = None
        
    def _get_iam_token(self) -> Optional[str]:
        """Get IAM access token from IBM Cloud"""
        if self._iam_token:
            return self._iam_token
            
        try:
            # IBM Cloud IAM token endpoint
            iam_url = "https://iam.cloud.ibm.com/identity/token"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            data = {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key
            }
            
            response = requests.post(iam_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self._iam_token = result.get("access_token")
                return self._iam_token
            else:
                print(f"IAM Token Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"IAM Token Exception: {e}")
            return None
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Create proper authorization headers for Watson"""
        token = self._get_iam_token()
        if not token:
            return {}
            
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test if Watson Orchestrate credentials work"""
        # Try multiple possible endpoints
        endpoints_to_try = [
            f"{self.base_url}/v1/health",
            f"{self.base_url}/v1/skills",
            f"{self.base_url}/v1/teams",
            f"{self.base_url}/health",
            f"{self.base_url}/api/v1/health",
            "https://api.au-syd.assistant.watson.cloud.ibm.com/instances/{}/v2/assistants".format(self.instance_id),
        ]
        
        headers = self._get_auth_header()
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    return {
                        "connected": True,
                        "status_code": 200,
                        "endpoint": endpoint,
                        "message": "Watson Orchestrate connected!"
                    }
                elif response.status_code == 401:
                    return {
                        "connected": False,
                        "status_code": 401,
                        "message": "Invalid API key"
                    }
                    
            except Exception as e:
                continue
        
        # All endpoints failed
        return {
            "connected": False,
            "status_code": 404,
            "message": "Watson endpoints not accessible - using local AI"
        }
    
    def enhance_response(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Try to use Watson, fallback to intelligent local AI
        """
        # Test connection first
        connection = self.test_connection()
        
        if connection.get("connected"):
            # Watson is available - log it
            print(f"✓ Using IBM Watson Orchestrate API")
            return self._generate_with_watson(user_input, context)
        else:
            # Use local intelligent AI
            print(f"ℹ Watson unavailable - using local Agentic AI")
            return self._generate_locally(user_input, context)
    
    def _generate_with_watson(self, user_input: str, context: Dict) -> str:
        """
        Attempt to use Watson Orchestrate skills/automation APIs
        """
        try:
            headers = self._get_auth_header()
            
            # Try Watson Assistant API format
            assistant_endpoints = [
                f"{self.base_url}/v2/assistants",
                f"https://api.au-syd.assistant.watson.cloud.ibm.com/instances/{self.instance_id}/v2/assistants",
            ]
            
            for endpoint in assistant_endpoints:
                try:
                    response = requests.post(
                        f"{endpoint}/message",
                        headers=headers,
                        json={
                            "input": {"text": user_input},
                            "context": context
                        },
                        timeout=5
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("output", {}).get("generic", [{}])[0].get("text", self._generate_locally(user_input, context))
                except:
                    continue
            
            # If Watson doesn't work, use local
            return self._generate_locally(user_input, context)
            
        except Exception as e:
            print(f"Watson API error: {e}")
            return self._generate_locally(user_input, context)
    
    def _generate_locally(self, user_input: str, context: Dict) -> str:
        """
        Local intelligent response generation
        This is the actual AI that works
        """
        from agents.intelligent_agent import intelligent_agent
        
        # This already works - it's our intelligent agent
        result = intelligent_agent.process_request(user_input)
        return result.get("response", "I understand. Let me help you with that.")


# Create singleton
watson_orchestrate = WatsonOrchestrate()
