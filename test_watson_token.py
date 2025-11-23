"""
Test IBM Watson IAM Token Generation
Run this to verify your Watson credentials work
"""
import requests
import sys

def test_iam_token():
    """Test IAM Token Generation with IBM Watson API Key"""
    
    # Your API key from .env
    api_key = "W_Qh1vBXvIeJzO6OdwfTsRB_i969rrQXKvcON77Fs3y-"
    
    print("=" * 60)
    print("IBM Watson IAM Token Test")
    print("=" * 60)
    print(f"\nAPI Key: {api_key[:20]}...")
    print("\nRequesting IAM token from IBM Cloud...")
    
    try:
        # IAM Token endpoint
        response = requests.post(
            'https://iam.cloud.ibm.com/identity/token',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                'apikey': api_key
            },
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token", "")
            
            print("\n" + "=" * 60)
            print("SUCCESS! IAM Token Generated")
            print("=" * 60)
            print(f"\nToken Length: {len(token)} characters")
            print(f"Token Preview: {token[:50]}...")
            print(f"Token Type: {result.get('token_type')}")
            print(f"Expires In: {result.get('expires_in')} seconds ({result.get('expires_in')//60} minutes)")
            print(f"Refresh Token: {'Yes' if result.get('refresh_token') else 'No'}")
            
            print("\n" + "=" * 60)
            print("Your IBM Watson API key is VALID!")
            print("=" * 60)
            
            return True
            
        elif response.status_code == 400:
            print("\nERROR 400: Bad Request")
            print("Response:", response.text)
            print("\nPossible issues:")
            print("- Invalid API key format")
            print("- Check if API key is correct in .env file")
            return False
            
        elif response.status_code == 401:
            print("\nERROR 401: Unauthorized")
            print("Your API key is invalid or expired")
            print("\nPlease:")
            print("1. Go to: https://cloud.ibm.com/iam/apikeys")
            print("2. Generate a new API key")
            print("3. Update .env file with new key")
            return False
            
        else:
            print(f"\nERROR {response.status_code}")
            print("Response:", response.text[:200])
            return False
            
    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out")
        print("Check your internet connection")
        return False
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Connection failed")
        print("Check your internet connection")
        return False
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False


def test_watson_orchestrate_endpoints():
    """Test Watson Orchestrate API endpoints"""
    
    print("\n\n" + "=" * 60)
    print("Testing Watson Orchestrate Endpoints")
    print("=" * 60)
    
    # Get IAM token first
    api_key = "W_Qh1vBXvIeJzO6OdwfTsRB_i969rrQXKvcON77Fs3y-"
    
    try:
        response = requests.post(
            'https://iam.cloud.ibm.com/identity/token',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                'apikey': api_key
            }
        )
        
        if response.status_code != 200:
            print("Failed to get IAM token")
            return False
        
        token = response.json().get('access_token')
        print(f"\nGot IAM token: {token[:30]}...")
        
        # Test Watson Orchestrate endpoints
        base_url = "https://api.au-syd.watson-orchestrate.cloud.ibm.com/instances/5911ac83-16da-49fb-b92d-8b4498635048"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        endpoints = [
            "",
            "/v1/skills",
            "/v1/teams",
            "/health",
        ]
        
        print("\nTesting endpoints:")
        print("-" * 60)
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                status = "SUCCESS" if resp.status_code == 200 else f"ERROR {resp.status_code}"
                print(f"{endpoint or '/ (base)':<20} | {status}")
            except Exception as e:
                print(f"{endpoint or '/ (base)':<20} | ERROR: {str(e)[:30]}")
        
        print("-" * 60)
        print("\nNote: Watson Orchestrate is a platform, not a REST API")
        print("404 errors are expected - credentials are valid though!")
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    success = test_iam_token()
    
    if success:
        test_watson_orchestrate_endpoints()
        print("\n" + "=" * 60)
        print("SUMMARY: Your IBM Watson credentials are working!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("FAILED: Fix your IBM Watson credentials")
        print("=" * 60)
        sys.exit(1)
