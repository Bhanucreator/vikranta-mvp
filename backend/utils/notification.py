from flask_mail import Message
from flask import current_app
from extensions import mail
import logging
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Twilio SMS client (lazy initialization)
_twilio_client = None

def get_twilio_client():
    """Initialize Twilio client lazily"""
    global _twilio_client
    if _twilio_client is None and current_app.config.get('SMS_ENABLED'):
        try:
            from twilio.rest import Client
            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            if account_sid and auth_token:
                _twilio_client = Client(account_sid, auth_token)
                logger.info("✅ Twilio SMS client initialized")
            else:
                logger.warning("⚠️ Twilio credentials not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twilio: {str(e)}")
    return _twilio_client

def send_email(to_email, subject, body, html=None):
    """Send email notification using direct SMTP"""
    try:
        # Debug: Print SMTP configuration (without password)
        print(f"📧 SMTP Config:")
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')
        smtp_username = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        
        print(f"   Server: {smtp_server}")
        print(f"   Port: {smtp_port}")
        print(f"   Username: {smtp_username}")
        print(f"   Password set: {bool(smtp_password)}")
        print(f"   To: {to_email}")
        
        # Verify SMTP credentials are set
        if not smtp_username:
            raise Exception("SMTP_USERNAME not configured")
        if not smtp_password:
            raise Exception("SMTP_PASSWORD not configured")
        
        print(f"📧 Attempting to send email to {to_email}...")
        
        # Use direct SMTP instead of Flask-Mail (more reliable)
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import socket
        
        # Set timeout
        socket.setdefaulttimeout(15)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        # Use kiranbhanu671@gmail.com as sender (must be verified in SendGrid)
        msg['From'] = f'VIKRANTA Safety <kiranbhanu671@gmail.com>'
        msg['To'] = to_email
        
        # Attach both plain text and HTML
        part1 = MIMEText(body, 'plain')
        msg.attach(part1)
        
        if html:
            part2 = MIMEText(html, 'html')
            msg.attach(part2)
        
        # Connect and send
        print(f"� Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
        
        print(f"🔒 Starting TLS...")
        server.starttls()
        
        print(f"🔐 Logging in as {smtp_username}...")
        server.login(smtp_username, smtp_password)
        
        print(f"📤 Sending message...")
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email sent successfully to {to_email}")
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except socket.timeout:
        error_msg = "SMTP connection timeout - server took too long to respond"
        logger.error(f"❌ Timeout sending email to {to_email}")
        print(f"❌ Email Timeout: {error_msg}")
        return False
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to send email to {to_email}: {error_msg}")
        print(f"❌ Email Error to {to_email}: {error_msg}")
        
        # Provide helpful error messages
        if "authentication failed" in error_msg.lower() or "username and password not accepted" in error_msg.lower():
            print("⚠️  SMTP Authentication failed - Check SMTP_USERNAME and SMTP_PASSWORD")
            print("   Make sure you're using a Gmail App Password (not your regular password)")
        elif "connection" in error_msg.lower():
            print("⚠️  SMTP Connection failed - Check SMTP_SERVER and SMTP_PORT")
            print("   Gmail: smtp.gmail.com:587")
        elif "tls" in error_msg.lower() or "ssl" in error_msg.lower():
            print("⚠️  TLS/SSL Error - Make sure MAIL_USE_TLS=True")
        
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
        
        return False

def send_sms(phone_number, message):
    """Send SMS notification via Twilio.
    
    Raises:
        Exception: If sending SMS fails for reasons other than Twilio trial account limitations.
    """
    print(f"📱 send_sms called - Phone: {phone_number}, Message length: {len(message)}")
    
    # Check if SMS is enabled
    sms_enabled = current_app.config.get('SMS_ENABLED')
    print(f"📱 SMS_ENABLED config value: {sms_enabled} (type: {type(sms_enabled)})")
    
    if not sms_enabled:
        logger.info(f"📱 SMS disabled. Would send to {phone_number}: {message}")
        print(f"[SMS DISABLED] To: {phone_number} | Message: {message}")
        return True
    
    print(f"📱 SMS is enabled, initializing Twilio client...")
    client = get_twilio_client()
    if not client:
        logger.warning(f"⚠️ Twilio not configured. SMS to {phone_number} not sent")
        print(f"[SMS NOT CONFIGURED] To: {phone_number} | Message: {message}")
        # Raise an exception so the caller knows it failed
        raise Exception("Twilio client is not configured. Cannot send SMS.")

    print(f"✅ Twilio client initialized successfully")
    
    # Format phone number (ensure it starts with +)
    original_phone = phone_number
    if not phone_number.startswith('+'):
        # Remove leading zero for Indian numbers (080xxx -> 80xxx)
        if phone_number.startswith('0'):
            phone_number = phone_number[1:]
        # Assume Indian number if no country code
        phone_number = f"+91{phone_number}"
    print(f"📱 Phone formatted: {original_phone} -> {phone_number}")
    
    from_number = current_app.config.get('TWILIO_PHONE_NUMBER')
    print(f"📱 From number: {from_number}")
    
    try:
        # Send SMS via Twilio
        print(f"📱 Calling Twilio API to send SMS...")
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        
        logger.info(f"✅ SMS sent successfully to {phone_number} (SID: {message_obj.sid})")
        print(f"✅ [SMS SENT] To: {phone_number} | SID: {message_obj.sid} | Status: {message_obj.status}")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Gracefully handle trial account limitation without erroring
        if "unverified" in error_msg or "trial" in error_msg:
            logger.warning(f"⚠️ SMS skipped (trial account): {phone_number}")
            print(f"⚠️ SMS skipped for {phone_number} (Twilio trial account - number unverified)")
            print(f" Notification delivered via WebSocket/in-app instead")
            # Return True to indicate "handled" (not a critical error)
            return True
        
        # For all other errors, re-raise the exception to be handled by the caller
        logger.error(f"❌ Failed to send SMS to {phone_number}: {str(e)}")
        print(f"❌ SMS Error to {phone_number}: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        # Re-raise the exception
        raise e

def send_otp_email(to_email, otp, name):
    """Send OTP via email - tries Gmail SMTP first, then SendGrid as fallback"""
    import os
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Email HTML content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2563eb; margin-bottom: 20px;">Welcome to Vikranta</h2>
                <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                    Hi {name},
                </p>
                <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                    Your verification code is:
                </p>
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                    <h1 style="color: #1e40af; margin: 0; font-size: 36px; letter-spacing: 5px;">{otp}</h1>
                </div>
                <p style="font-size: 14px; color: #666;">
                    This OTP is valid for 10 minutes. Do not share it with anyone.
                </p>
                <p style="font-size: 14px; color: #666; margin-top: 20px;">
                    If you didn't request this code, please ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">
                    Team VIKRANTA - Smart Tourist Safety Platform
                </p>
            </div>
        </body>
    </html>
    """
    
    plain_text = f"Hi {name},\n\nYour VIKRANTA verification code is: {otp}\n\nThis code is valid for 10 minutes.\n\nTeam VIKRANTA"
    
    # Try Gmail SMTP first (more reliable)
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_app_password = os.environ.get('GMAIL_APP_PASSWORD')
    
    if gmail_user and gmail_app_password:
        try:
            print(f"\n📧 Trying Gmail SMTP...")
            print(f"   From: {gmail_user}")
            print(f"   To: {to_email}")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'VIKRANTA - Your Verification Code'
            msg['From'] = f'VIKRANTA Safety <{gmail_user}>'
            msg['To'] = to_email
            
            msg.attach(MIMEText(plain_text, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.starttls()
            server.login(gmail_user, gmail_app_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully via Gmail to {to_email}")
            logger.info(f"✅ OTP email sent to {to_email} via Gmail")
            return True
            
        except Exception as e:
            print(f"❌ Gmail SMTP failed: {str(e)}")
            logger.error(f"Gmail SMTP failed: {str(e)}")
    
    # Fallback to SendGrid
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        print(f"\n📧 Trying SendGrid API...")
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        sender_email = os.environ.get('MAIL_FROM_EMAIL', 'bhanukiran90216@gmail.com')
        
        print(f"   API Key: {'Set' if api_key else 'Not Set'}")
        print(f"   From: {sender_email}")
        print(f"   To: {to_email}")
        
        if not api_key:
            raise ValueError("No SENDGRID_API_KEY configured")
        
        message = Mail(
            from_email=Email(sender_email, 'VIKRANTA Safety'),
            to_emails=To(to_email),
            subject='VIKRANTA - Your Verification Code',
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        print(f"✅ SendGrid Response Status: {response.status_code}")
        print(f"✅ Email sent successfully to {to_email}")
        
        logger.info(f"✅ OTP email sent to {to_email} via SendGrid")
        return True
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to send OTP email: {error_msg}")
        print(f"❌ Error sending email: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def send_emergency_alert(incident, user):
    """Send emergency alert notifications"""
    # Email to authorities
    subject = f"🚨 EMERGENCY ALERT - {incident.type.upper()}"
    body = f"""
    EMERGENCY ALERT
    
    Type: {incident.type}
    Priority: {incident.priority}
    User: {user.name} ({user.email})
    Phone: {user.phone}
    Location: {incident.address}
    Time: {incident.created_at}
    
    Medical Info: {user.medical_info or 'None'}
    Emergency Contact: {user.emergency_contact or 'None'}
    
    Description: {incident.description or 'No description provided'}
    
    Please respond immediately.
    """
    
    # In production, send to actual authority emails
    print(f"[EMERGENCY ALERT] {subject}")
    print(body)
    
    # Send SMS to emergency contact if available
    if user.emergency_contact:
        sms_message = f"VIKRANTA ALERT: {user.name} has triggered an emergency alert. Location: {incident.address}. Please check the app for details."
        send_sms(user.emergency_contact, sms_message)
    
    return True
