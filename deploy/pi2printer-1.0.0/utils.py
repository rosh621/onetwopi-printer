#!/usr/bin/env python3
"""
PI2PRINTER Utilities
Shared functions for Gmail and Gemini API operations
"""

import os
import base64
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Google APIs
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Gmail permissions
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

logger = logging.getLogger(__name__)


def setup_gmail_service():
    """Setup Gmail API service with credential handling"""
    logger.debug("Setting up Gmail API service...")
    
    if not os.path.exists('token.json'):
        raise FileNotFoundError("Gmail credentials not found. Run: python3 -c \"from utils import *; setup_gmail_auth()\"")
    
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Gmail token...")
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        if creds and creds.valid:
            service = build('gmail', 'v1', credentials=creds)
            logger.debug("Gmail API service ready")
            return service
        else:
            raise ValueError("Invalid Gmail credentials")
            
    except Exception as e:
        logger.error(f"Failed to setup Gmail service: {e}")
        raise


def setup_gemini_model(model_name: str = 'gemini-2.5-flash'):
    """Setup Gemini AI model with API key validation"""
    logger.debug("Setting up Gemini API...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set!")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        logger.debug(f"Gemini model '{model_name}' ready")
        return model
    except Exception as e:
        logger.error(f"Failed to setup Gemini: {e}")
        raise


def decode_base64_email_data(data: str) -> str:
    """Decode base64url encoded email data"""
    try:
        return base64.urlsafe_b64decode(data + '===').decode('utf-8', errors='ignore')
    except Exception as e:
        logger.warning(f"Failed to decode base64 data: {e}")
        return ""


def extract_email_body(payload: Dict) -> str:
    """Extract text body from Gmail message payload"""
    body = ""
    
    try:
        if 'parts' in payload:
            # Multi-part message
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    body = decode_base64_email_data(part['body']['data'])
                    break
                # Also check nested parts
                elif 'parts' in part:
                    for nested_part in part['parts']:
                        if (nested_part.get('mimeType') == 'text/plain' and 
                            'data' in nested_part.get('body', {})):
                            body = decode_base64_email_data(nested_part['body']['data'])
                            break
                    if body:
                        break
        else:
            # Single part message
            if (payload.get('mimeType') == 'text/plain' and 
                'data' in payload.get('body', {})):
                body = decode_base64_email_data(payload['body']['data'])
        
        return body or "No text content found"
        
    except Exception as e:
        logger.error(f"Failed to extract email body: {e}")
        return "Could not extract email content"


def create_task_analysis_prompt(email_data: Dict[str, Any]) -> str:
    """Create standardized prompt for email task analysis"""
    return f"""
Analyze this email and determine if it contains actionable tasks that require the user's attention.

EMAIL DETAILS:
Subject: {email_data['subject']}
From: {email_data['from']}
Date: {email_data['date']}
Body: {email_data['body']}

FILTERING CRITERIA:
- Skip promotional emails, newsletters, marketing content
- Skip automated notifications that don't require action
- Skip social media notifications, app updates
- Focus on emails requiring human response or action
- Prioritize work emails, personal requests, deadlines, meetings

Return JSON response with this exact structure:
{{
    "has_task": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation why this is/isn't actionable",
    "mission_briefing": {{
        "title": "Clear, actionable mission title (max 60 chars)",
        "urgency": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
        "deadline": "Specific date/time or 'ASAP' or null",
        "action_required": "Specific next step to take",
        "context": "Brief context (1 sentence max)",
        "people_involved": ["person1", "person2"],
        "mission_id": "MI-{email_data['id'][:8]}"
    }}
}}

URGENCY GUIDELINES:
- CRITICAL: Response needed within 2 hours (urgent meetings, emergency situations)
- HIGH: Response needed today/tomorrow (important work emails, time-sensitive requests)
- MEDIUM: Response needed within 3-7 days (follow-ups, scheduled tasks)
- LOW: Can be addressed when convenient (nice-to-have items)
- INFO: No action required, just informational

If no actionable task is found, set "has_task": false and omit "mission_briefing".
Return ONLY valid JSON, no markdown or extra text.
"""


def parse_gmail_message(message: Dict) -> Optional[Dict[str, Any]]:
    """Parse Gmail message into structured email data"""
    try:
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        # Extract body
        body = extract_email_body(message['payload'])
        
        # Get timestamp
        from datetime import datetime, timezone
        timestamp = int(message['internalDate']) / 1000
        email_date = datetime.fromtimestamp(timestamp, timezone.utc)
        
        email_data = {
            'id': message['id'],
            'subject': headers.get('Subject', 'No Subject'),
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', ''),
            'date': email_date.isoformat(),
            'body': body[:3000],  # Limit for AI processing
            'labels': message.get('labelIds', []),
            'thread_id': message.get('threadId', ''),
            'raw_message': message
        }
        
        return email_data
        
    except Exception as e:
        logger.error(f"Failed to parse Gmail message: {e}")
        return None


def setup_gmail_auth():
    """Interactive Gmail authentication setup (for initial setup only)"""
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    print("🔐 Setting up Gmail authentication...")
    
    if not os.path.exists('credentials.json'):
        print("❌ Error: credentials.json not found!")
        print("\nTo fix this:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable the Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download as 'credentials.json' and put it in this folder")
        return False
    
    print("   🔐 Starting login process...")
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    
    # Use manual flow for WSL/headless environments
    print("\n📋 Please follow these steps:")
    print("1. Copy this URL and open it in your browser:")
    
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f"\n{auth_url}\n")
    
    print("2. After authorizing, Google will show you an authorization code")
    print("3. Copy that authorization code and paste it below:")
    
    auth_code = input("\nPaste the authorization code here: ").strip()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return False
    
    # Exchange the authorization code for credentials
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    
    # Save the credentials for future use
    print("   💾 Saving credentials for future use")
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("✅ Gmail authentication setup complete!")
    return True


# Test functions
def test_gmail_connection():
    """Test Gmail API connection"""
    try:
        service = setup_gmail_service()
        
        # Try to list 1 message
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            print(f"✅ Gmail connection working - found {len(messages)} message(s)")
            return True
        else:
            print("📭 Gmail connection working but no messages found")
            return True
            
    except Exception as e:
        print(f"❌ Gmail connection failed: {e}")
        return False


def test_gemini_connection():
    """Test Gemini API connection"""
    try:
        model = setup_gemini_model()
        
        # Simple test query
        response = model.generate_content("Say 'Hello from Gemini!' in JSON format: {\"message\": \"...\"}}")
        print(f"✅ Gemini connection working - response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini connection failed: {e}")
        return False


if __name__ == '__main__':
    """Quick connection tests"""
    print("🧪 Testing API connections...")
    print("-" * 40)
    
    gmail_ok = test_gmail_connection()
    gemini_ok = test_gemini_connection()
    
    print("-" * 40)
    if gmail_ok and gemini_ok:
        print("🎉 All API connections working!")
    else:
        print("⚠️  Some connections failed - check configuration")