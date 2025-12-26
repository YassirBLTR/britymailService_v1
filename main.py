# main.py
import asyncio
import logging
import base64
import json
import sys
from pathlib import Path
from email.parser import Parser

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import uvicorn
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging # You can use Debugging for more verbose SMTP logs if needed

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration for Brittymail API ---
BRITTYMAIL_SEND_URL = "https://www.brityworks.com/mail/rest/v1/mails/send"
ACCOUNTS_CONFIG_FILE = Path(__file__).parent / "accounts.json"

# --- Multi-Account Management ---
class BrityworksAccountManager:
    """Manages multiple Brityworks accounts for sending emails"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.accounts = {}
        self.selected_accounts = []  # List of account IDs to use (empty means use all)
        self.load_accounts()
    
    def load_accounts(self):
        """Load accounts from JSON configuration file"""
        if not self.config_file.exists():
            logger.warning(f"Accounts config file not found: {self.config_file}")
            logger.warning("Creating default account configuration...")
            self._create_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                accounts_list = json.load(f)
            
            for account in accounts_list:
                account_id = account.get('account_id')
                if account_id:
                    self.accounts[account_id] = account
                    logger.info(f"Loaded account: {account_id} ({account.get('email')})")
            
            if not self.accounts:
                raise ValueError("No valid accounts found in configuration")
                
        except Exception as e:
            logger.error(f"Error loading accounts configuration: {e}")
            raise
    
    def _create_default_config(self):
        """Create a default accounts.json file with the original account"""
        default_config = [
            {
                "account_id": "account_1",
                "email": "blawsompirow22@brityworks.com",
                "display_name": "Account 1",
                "cookies": {
                    "SCOUTER": "x490vgmqhm4nk2",
                    "saveLanguage": "en_US.EUC-KR",
                    "logimage.index": "0",
                    "BRITY_K8S": "1748696144.735.15186.853933|dbbcfaa59e333e6be4fcc8a34a9fa462",
                    "EPV8PTSID": "-qvKp501QqM04JLus3FR2aK4VeBImF6c8Ly70l0",
                    "saveLoginId": "blawsompirow22@brityworks.com",
                    "EP6_UTOKEN": "4FTGYEZmNKLOHLnRNF2CBn5lv1kewXgfNMks4qO6TcKY7WC0bDWnJoe0eWWd92tCbC5kZQRGJGBZX+fYA3XwxI0YJYuUXceCsngI+5BpzPhTOk3WZIaBZJ4fdneR+aLogNMJLDDuPvcUL9kfEm3wEFrKdad7jk58097XE/uV2WBEGy0XwWa0TWvTjrECj8/4QAlBtFp2c793leonzbKb7y5IFlKVvT+1nRRGXAwvjJVVFMaM5dKAHtyaYhUedqij8RqyHY4icqqTB7HoOO9kbzDv7YjUtk5Ynq1FhcTq9fildtKSkiq0HzbGJOFdAkxaf9lnnFivjtcpeAiTsqZUglM3MnUOCusvSlGux7rFk4I=",
                    "EP_BROWSERID": "1748696300881",
                    "EP_LOGINID": "blawsompirow22@brityworks.com",
                    "EPV8EMSID": "eCxmhfzvQQ2ozOBIoBbk9GJaACkcZX9uDtgOYdaL",
                    "EPV8BBSID": "ftJp6FOkD-Lec7ZhDMRvMgGF-AVcuHQYSpG6kUhG",
                    "EPV8APSID": "UmePUQvsbDIwOD2JBKsw4FuSzXphTmRR8yXPHjur",
                    "EPV8PISID": "8U9D98Zu9MfCx7uTU2W3SxWyR_ww6Q71RWMF9gWp",
                    "EPV8MLSID": "DzffUUdnbZKTomHC-ZhDmdoQCUPY8nZyYWU-9VtJ"
                },
                "headers": {
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "access-control-allow-credentials": "true",
                    "access-control-allow-methods": "GET,PUT,POST,DELETE,PATCH,OPTIONS",
                    "access-control-allow-origin": "*",
                    "content-type": "application/json;charset=UTF-8",
                    "origin": "https://www.brityworks.com",
                    "priority": "u=1, i",
                    "referer": "https://www.brityworks.com/formapp/?initModule=mail&userId=blawsompirow22@brityworks.com",
                    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                }
            }
        ]
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Created default accounts configuration at: {self.config_file}")

    def save_accounts(self):
        """Persist current accounts to the config file atomically.

        Ensures the parent directory exists and writes to a temporary
        file before atomically replacing the target file. This guarantees
        that `accounts.json` will be created if it does not exist.
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = self.config_file.with_suffix('.tmp')
            accounts_list = list(self.accounts.values())
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(accounts_list, f, indent=2)
            tmp_file.replace(self.config_file)
            logger.info(f"Saved accounts configuration to: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save accounts configuration: {e}")
            return False
    
    def get_account(self, account_id: str = None):
        """Get account by ID, or return first account if no ID specified"""
        if account_id:
            account = self.accounts.get(account_id)
            if not account:
                logger.warning(f"Account '{account_id}' not found. Available accounts: {list(self.accounts.keys())}")
                return None
            return account
        else:
            # Return first account as default
            if self.accounts:
                return list(self.accounts.values())[0]
            return None
    
    def list_accounts(self):
        """Return list of available account IDs"""
        return list(self.accounts.keys())
    
    def set_selected_accounts(self, account_ids: list):
        """Set which accounts to use for sending (empty list means use all)"""
        if not account_ids:
            self.selected_accounts = list(self.accounts.keys())
            logger.info("Using all available accounts")
        else:
            # Validate account IDs
            valid_accounts = [aid for aid in account_ids if aid in self.accounts]
            if not valid_accounts:
                logger.error(f"No valid accounts in selection: {account_ids}")
                return False
            self.selected_accounts = valid_accounts
            logger.info(f"Selected accounts: {', '.join(valid_accounts)}")
        return True
    
    def get_account_by_email(self, sender_email: str):
        """Find account that matches the sender email from selected accounts"""
        if not sender_email:
            return None
        
        # Normalize email to lowercase for comparison
        sender_email_lower = sender_email.lower().strip()
        
        # Search through selected accounts for matching email
        for account_id in self.selected_accounts:
            account = self.accounts.get(account_id)
            if account:
                account_email = account.get('email', '').lower().strip()
                if account_email == sender_email_lower:
                    logger.info(f"Found matching account '{account_id}' for sender '{sender_email}'")
                    return account
        
        logger.warning(f"No account found matching sender email: {sender_email}")
        return None
    
    def get_all_selected_accounts(self):
        """Get all selected accounts as a list"""
        accounts_list = []
        for account_id in self.selected_accounts:
            account = self.accounts.get(account_id)
            if account:
                accounts_list.append(account)
        return accounts_list
    
    def get_selected_account(self, account_id: str = None, sender_email: str = None):
        """Get account by ID, sender email, or return first selected account"""
        # Priority 1: Explicit account_id specified (via X-Brityworks-Account header)
        if account_id:
            if account_id in self.selected_accounts:
                logger.info(f"Using explicitly requested account: {account_id}")
                return self.accounts.get(account_id)
            logger.warning(f"Account '{account_id}' not in selected accounts")
            return None
        
        # Priority 2: Match sender email to account
        if sender_email:
            account = self.get_account_by_email(sender_email)
            if account:
                return account
            logger.warning(f"Sender email '{sender_email}' doesn't match any selected account")
        
        # Priority 3: Fallback to first selected account
        if self.selected_accounts:
            fallback_account_id = self.selected_accounts[0]
            logger.info(f"Using fallback account: {fallback_account_id}")
            return self.accounts.get(fallback_account_id)
        
        return None
    
    def display_accounts_menu(self):
        """Display interactive menu for account selection"""
        print("\n" + "="*60)
        print("BRITYWORKS ACCOUNT SELECTION")
        print("="*60)
        
        if not self.accounts:
            print("❌ No accounts available!")
            return False
        
        print("\nAvailable accounts:")
        account_list = list(self.accounts.items())
        for idx, (account_id, account) in enumerate(account_list, 1):
            print(f"  {idx}. {account.get('display_name', account_id)} - {account.get('email')}")
        
        print(f"\n  0. Use ALL accounts ({len(account_list)} accounts)")
        print("\n" + "="*60)
        
        while True:
            try:
                choice = input("\nSelect option (0 for all, or account numbers separated by commas): ").strip()
                
                if choice == "0":
                    # Use all accounts
                    self.set_selected_accounts([])
                    return True
                
                # Parse comma-separated numbers
                selected_indices = [int(x.strip()) for x in choice.split(',')]
                
                # Validate indices
                if any(idx < 1 or idx > len(account_list) for idx in selected_indices):
                    print(f"❌ Invalid selection. Please enter numbers between 1 and {len(account_list)}")
                    continue
                
                # Get account IDs from indices
                selected_account_ids = [account_list[idx-1][0] for idx in selected_indices]
                
                if self.set_selected_accounts(selected_account_ids):
                    print(f"\n✅ Selected {len(selected_account_ids)} account(s)")
                    return True
                else:
                    print("❌ Failed to set selected accounts")
                    return False
                    
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas (e.g., 1,2,3) or 0 for all")
            except KeyboardInterrupt:
                print("\n\n❌ Selection cancelled by user")
                return False
            except Exception as e:
                print(f"❌ Error: {e}")
                return False

# Initialize account manager (will be configured after user selection)
account_manager = None

# --- FastAPI Application Setup ---
fastapi_app = FastAPI(
    title="Brittymail HTTP Forwarder",
    description="Receives parsed email content via HTTP and forwards it to Brittymail.",
    version="1.0.0"
)

# Define a Pydantic model for the incoming email data from the SMTP Handler
class ParsedEmailPayload(BaseModel):
    raw_email: str
    sender_email: str
    recipient_email: str
    subject: str
    account_id: Optional[str] = None  # Optional: User can specify which Brityworks account to use
    attachments: list = [] # List of dicts: {"filename": "name", "content": "base64_encoded_string"}

# --- FastAPI Middleware (Optional) ---
@fastapi_app.middleware("http")
async def log_fastapi_requests(request: Request, call_next):
    logger.info(f"FastAPI: Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"FastAPI: Outgoing response: {response.status_code}")
    return response

# --- FastAPI Endpoint to receive parsed email from the SMTP Handler ---
@fastapi_app.post("/forward-email/")
async def forward_email_to_brittymail(payload: ParsedEmailPayload):
    logger.info("FastAPI: Received parsed email payload for forwarding.")

    # Extract data from the payload
    sender_email = payload.sender_email
    recipient_email = payload.recipient_email
    subject = payload.subject
    raw_email_content = payload.raw_email
    attachments_for_brittymail = payload.attachments
    requested_account_id = payload.account_id

    # Get the account to use for sending (prioritize sender email matching)
    account = account_manager.get_selected_account(requested_account_id, sender_email)
    if not account:
        logger.error(f"No valid account found. Requested: {requested_account_id}, Sender: {sender_email}")
        raise HTTPException(status_code=400, detail=f"No matching account found for sender: {sender_email}")
    
    account_email = account.get('email')
    account_cookies = account.get('cookies', {})
    account_headers = account.get('headers', {})
    
    logger.info(f"FastAPI: Using account '{account.get('account_id')}' ({account_email}) to send email")
    logger.info(f"FastAPI: Preparing to send: From='{sender_email}', To='{recipient_email}', Subject='{subject}'")

    # Construct the json_data for Brittymail based on your send.py script
    brittymail_json_data = {
        'priority': '3',
        'docSecuType': 'PERSONAL',
        'demandReply': False,
        'senderEngExprYN': True,
        'openAlert': False,
        'openAlertTargets': [],
        'deleteSecurityPhrase': False,
        'cpgsPassed': False,
        'originalFolderID': 0,
        'originalMailSeq': 0,
        'preMailSeq': 0,
        'processCode': 'NONE',
        'preFolderID': 0,
        'contentText': raw_email_content, # Send the whole raw email here
        'contentType': 'MIME', # Based on your script, this should be MIME
        'individualMail': False,
        'isConfidentialExtMail': False,
        'topMailID': None,
        'originalMessageID': None,
        'from': {
            'email': sender_email,
            'dcomp': 'O',
            'userID': sender_email, # Often same as email
            'sendrIndiVal': f"{sender_email}<{sender_email}>", # Format as per your script
        },
        'attachs': attachments_for_brittymail, # Use the parsed attachments
        'subject': subject,
        'recipients': [
            {
                'email': recipient_email,
                'recipientType': 'TO',
                'directKeyin': False,
                'rcvrName': recipient_email,
                'displayName': recipient_email,
            },
        ],
        'nonEncMail': False,
        'disabledMailOption': {
            'disabledConfidential': False,
            'disabledConfidential_Strict': False,
        },
        'approvalList': [],
    }

    # Make the HTTP request to Brittymail using the selected account
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                BRITTYMAIL_SEND_URL,
                cookies=account_cookies,
                headers=account_headers,
                json=brittymail_json_data
            )
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            logger.info(f"FastAPI: Successfully sent email to Brittymail. Status: {response.status_code}")
            return {"message": "Email forwarded successfully!", "brittymail_response": response.json()}
        except httpx.HTTPStatusError as e:
            logger.error(f"FastAPI: Error sending email to Brittymail: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail=f"Failed to forward email to Brittymail: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"FastAPI: Network error sending email to Brittymail: {e}")
            raise HTTPException(status_code=500, detail=f"Network error forwarding email to Brittymail: {e}")
        except Exception as e:
            logger.error(f"FastAPI: An unexpected error occurred: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# --- FastAPI Health Check Endpoint ---
@fastapi_app.get("/health/")
async def fastapi_health_check():
    return {"status": "ok", "component": "fastapi_forwarder"}

# --- Account Management Endpoints ---

@fastapi_app.get("/accounts/")
async def list_accounts():
    """List all configured accounts"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    accounts_list = []
    for account_id, account in account_manager.accounts.items():
        accounts_list.append({
            "account_id": account_id,
            "email": account.get("email"),
            "display_name": account.get("display_name"),
            "is_selected": account_id in account_manager.selected_accounts
        })
    
    return {
        "total": len(accounts_list),
        "selected": len(account_manager.selected_accounts),
        "accounts": accounts_list
    }

@fastapi_app.get("/accounts/{account_id}")
async def get_account(account_id: str):
    """Get details of a specific account (without sensitive data)"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    account = account_manager.accounts.get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    
    return {
        "account_id": account_id,
        "email": account.get("email"),
        "display_name": account.get("display_name"),
        "is_selected": account_id in account_manager.selected_accounts,
        "has_cookies": bool(account.get("cookies")),
        "has_headers": bool(account.get("headers"))
    }

class AccountCreate(BaseModel):
    account_id: str
    email: str
    display_name: str
    cookies: dict
    headers: dict

@fastapi_app.post("/accounts/")
async def create_account(account: AccountCreate):
    """Add a new account"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    if account.account_id in account_manager.accounts:
        raise HTTPException(status_code=400, detail=f"Account '{account.account_id}' already exists")
    
    # Add to memory
    new_account = {
        "account_id": account.account_id,
        "email": account.email,
        "display_name": account.display_name,
        "cookies": account.cookies,
        "headers": account.headers
    }
    account_manager.accounts[account.account_id] = new_account

    # Persist to disk (create file if missing)
    if not account_manager.save_accounts():
        raise HTTPException(status_code=500, detail="Failed to persist account configuration")

    logger.info(f"Created new account: {account.account_id} ({account.email})")

    return {"message": "Account created successfully", "account_id": account.account_id}

@fastapi_app.put("/accounts/{account_id}")
async def update_account(account_id: str, account: AccountCreate):
    """Update an existing account"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    if account_id not in account_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    
    # Update in memory
    updated_account = {
        "account_id": account.account_id,
        "email": account.email,
        "display_name": account.display_name,
        "cookies": account.cookies,
        "headers": account.headers
    }
    
    # If account_id changed, remove old and add new
    if account_id != account.account_id:
        del account_manager.accounts[account_id]
        # Update selected accounts list if needed
        if account_id in account_manager.selected_accounts:
            account_manager.selected_accounts.remove(account_id)
            account_manager.selected_accounts.append(account.account_id)
    
    account_manager.accounts[account.account_id] = updated_account

    # Persist changes
    if not account_manager.save_accounts():
        raise HTTPException(status_code=500, detail="Failed to persist account configuration")

    logger.info(f"Updated account: {account.account_id} ({account.email})")

    return {"message": "Account updated successfully", "account_id": account.account_id}

@fastapi_app.delete("/accounts/{account_id}")
async def delete_account(account_id: str):
    """Delete an account"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    if account_id not in account_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    
    # Remove from memory
    del account_manager.accounts[account_id]
    
    # Remove from selected accounts if present
    if account_id in account_manager.selected_accounts:
        account_manager.selected_accounts.remove(account_id)
    
    # Persist changes
    if not account_manager.save_accounts():
        raise HTTPException(status_code=500, detail="Failed to persist account configuration")

    logger.info(f"Deleted account: {account_id}")

    return {"message": "Account deleted successfully", "account_id": account_id}

@fastapi_app.post("/accounts/{account_id}/select")
async def select_account(account_id: str):
    """Add account to selected accounts"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    if account_id not in account_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    
    if account_id not in account_manager.selected_accounts:
        account_manager.selected_accounts.append(account_id)
        logger.info(f"Selected account: {account_id}")
    
    return {"message": "Account selected", "account_id": account_id}

@fastapi_app.post("/accounts/{account_id}/deselect")
async def deselect_account(account_id: str):
    """Remove account from selected accounts"""
    if not account_manager:
        raise HTTPException(status_code=500, detail="Account manager not initialized")
    
    if account_id not in account_manager.accounts:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    
    if account_id in account_manager.selected_accounts:
        account_manager.selected_accounts.remove(account_id)
        logger.info(f"Deselected account: {account_id}")
    
    return {"message": "Account deselected", "account_id": account_id}

# --- SMTP Listener Setup ---
SMTP_LISTENER_HOST = '0.0.0.0'
SMTP_LISTENER_PORT = 2525
FASTAPI_INTERNAL_URL = 'http://127.0.0.1:8000/forward-email/' # FastAPI endpoint for internal calls

class CustomSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        logger.info(f"SMTP Listener: Received DATA from {envelope.mail_from} for {envelope.rcpt_tos}")

        # Extract raw email content (bytes)
        raw_email_bytes = envelope.content
        raw_email_str = raw_email_bytes.decode('utf-8', errors='ignore') # Decode to string for email.parser

        # Parse the raw email content using Python's built-in email library
        msg = Parser().parsestr(raw_email_str)

        # Use SMTP envelope sender/recipients (more reliable than parsing headers)
        # envelope.mail_from is the actual sender from SMTP MAIL FROM command
        # envelope.rcpt_tos is the list of recipients from SMTP RCPT TO commands
        sender_email = envelope.mail_from if envelope.mail_from else "unknown_sender@example.com"
        recipient_email = envelope.rcpt_tos[0] if envelope.rcpt_tos else "unknown_recipient@example.com"
        
        # Get subject from email headers
        subject = msg.get("Subject", "No Subject")
        
        # Extract account_id from custom header (X-Brityworks-Account)
        # User can specify which account to use by adding this header to the email
        # Special value "ALL" means send from all selected accounts
        account_id = msg.get("X-Brityworks-Account", None)
        send_from_all = False
        
        if account_id:
            if account_id.upper() == "ALL":
                send_from_all = True
                logger.info(f"SMTP Listener: Multi-account mode enabled - will send from ALL selected accounts")
            else:
                logger.info(f"SMTP Listener: Account selection header found: {account_id}")
        
        logger.info(f"SMTP Listener: Parsed - From: {sender_email}, To: {recipient_email}, Subject: {subject}")

        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))

                # Only process attachments, as full raw_email is sent as contentText
                if "attachment" in cdispo:
                    filename = part.get_filename()
                    if filename:
                        attachment_content_bytes = part.get_payload(decode=True)
                        attachments.append({
                            "filename": filename,
                            "content": base64.b64encode(attachment_content_bytes).decode('utf-8')
                        })

        # Determine which accounts to use for sending
        if send_from_all:
            # Send from all selected accounts
            accounts_to_use = account_manager.get_all_selected_accounts()
            logger.info(f"SMTP Listener: Will send from {len(accounts_to_use)} accounts")
        else:
            # Use single account (matched or specified)
            single_account = account_manager.get_selected_account(account_id, sender_email)
            accounts_to_use = [single_account] if single_account else []
        
        if not accounts_to_use:
            logger.error("SMTP Listener: No accounts available for sending")
            return '250 OK'  # Still return OK to SMTP client
        
        # Send email from each account
        success_count = 0
        failed_count = 0
        
        async with httpx.AsyncClient() as client:
            for account in accounts_to_use:
                account_id_str = account.get('account_id')
                account_email = account.get('email')
                
                logger.info(f"SMTP Listener: Sending from account '{account_id_str}' ({account_email})")
                
                # Prepare payload for FastAPI with specific account
                fastapi_payload = {
                    "raw_email": raw_email_str,
                    "sender_email": account_email,  # Use account's email as sender
                    "recipient_email": recipient_email,
                    "subject": subject,
                    "account_id": account_id_str,  # Force this specific account
                    "attachments": attachments
                }

                try:
                    response = await client.post(FASTAPI_INTERNAL_URL, json=fastapi_payload)
                    response.raise_for_status()
                    logger.info(f"SMTP Listener: ✅ Successfully sent from {account_email}. Status: {response.status_code}")
                    success_count += 1
                except httpx.HTTPStatusError as e:
                    logger.error(f"SMTP Listener: ❌ Error sending from {account_email}: {e.response.status_code} - {e.response.text}")
                    failed_count += 1
                except httpx.RequestError as e:
                    logger.error(f"SMTP Listener: ❌ Network error sending from {account_email}: {e}")
                    failed_count += 1
                except Exception as e:
                    logger.error(f"SMTP Listener: ❌ Unexpected error sending from {account_email}: {e}", exc_info=True)
                    failed_count += 1
        
        logger.info(f"SMTP Listener: Completed - {success_count} succeeded, {failed_count} failed out of {len(accounts_to_use)} accounts")
        return '250 OK' # Respond positively to PowerMTA

# --- Main function to run both servers ---
async def main():
    # 1. Setup Uvicorn server for FastAPI
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    fastapi_server = uvicorn.Server(config)

    # 2. Setup aiosmtpd controller for SMTP listener
    smtp_handler = CustomSMTPHandler()
    smtp_controller = Controller(smtp_handler, hostname=SMTP_LISTENER_HOST, port=SMTP_LISTENER_PORT)

    logger.info("Starting both FastAPI and SMTP Listener...")

    # Start both servers concurrently
    # The `serve()` method of uvicorn.Server is an awaitable.
    # The `start()` method of aiosmtpd.Controller is not awaitable, it starts a background thread.
    # We need to ensure the main asyncio loop stays alive for aiosmtpd.
    
    # Start SMTP controller in a separate thread (as it's not asyncio-native)
    smtp_controller.start()
    logger.info(f"SMTP Listener: Server started on {SMTP_LISTENER_HOST}:{SMTP_LISTENER_PORT}")

    # Run FastAPI server in the current asyncio loop
    await fastapi_server.serve()
    
    # The smtp_controller.stop() would ideally be called on shutdown,
    # but for a simple script, it might not be explicitly handled here
    # as the script will exit. For graceful shutdown, you'd add signal handlers.

if __name__ == '__main__':
    # Initialize account manager and show selection menu
    try:
        account_manager = BrityworksAccountManager(ACCOUNTS_CONFIG_FILE)

        # If running interactively, show account selection menu. When running as a service
        # (non-interactive), automatically select all accounts so the service doesn't block.
        try:
            if sys.stdin.isatty():
                if not account_manager.display_accounts_menu():
                    logger.error("Failed to select accounts. Exiting.")
                    exit(1)
            else:
                account_manager.set_selected_accounts([])  # select all accounts
                logger.info("Non-interactive startup: selected all accounts")
        except Exception as e:
            logger.warning(f"Account selection skipped: {e}")

        # Run the main asynchronous function
        # Python 3.6 compatible: use get_event_loop() instead of asyncio.run()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main())
        finally:
            loop.close()
    except KeyboardInterrupt:
        logger.info("Application stopped by user (Ctrl+C).")
    except Exception as e:
        logger.critical(f"Unhandled exception in main application: {e}", exc_info=True)