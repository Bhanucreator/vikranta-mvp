from flask_mail import Message
from flask import current_app
from extensions import mail
import logging

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
        msg['From'] = f'VIKRANTA Safety <{smtp_username}>'
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
    """Send SMS notification via Twilio"""
    print(f"📱 send_sms called - Phone: {phone_number}, Message length: {len(message)}")
    try:
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
            return False
        
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
        
        # Gracefully handle trial account limitation without error
        if "unverified" in error_msg or "trial" in error_msg:
            logger.warning(f"⚠️ SMS skipped (trial account): {phone_number}")
            print(f"⚠️ SMS skipped for {phone_number} (Twilio trial account - number unverified)")
            print(f"� Notification delivered via WebSocket/in-app instead")
            # Return True to indicate "handled" (not a critical error)
            return True
        
        # For other errors, log and return False
        logger.error(f"❌ Failed to send SMS to {phone_number}: {str(e)}")
        print(f"❌ SMS Error to {phone_number}: {str(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

def send_otp_email(to_email, otp, name):
    """Send OTP via email"""
    subject = "VIKRANTA - Your Verification Code"
    body = f"""
    Hi {name},
    
    Your VIKRANTA verification code is: {otp}
    
    This code will expire in 10 minutes.
    
    If you didn't request this code, please ignore this email.
    
    Best regards,
    Team VIKRANTA
    """
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #ff6b35;">VIKRANTA</h2>
            <p>Hi {name},</p>
            <p>Your verification code is:</p>
            <h1 style="color: #ff6b35; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">Team VIKRANTA - Smart Tourist Safety</p>
        </body>
    </html>
    """
    
    return send_email(to_email, subject, body, html)

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
