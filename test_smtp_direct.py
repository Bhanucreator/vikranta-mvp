"""
Test SMTP connection directly
Run this locally to verify SMTP credentials work
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your Railway SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "tech.pheonix03@gmail.com"
SMTP_PASSWORD = "ieraheabmcfqfiyn"  # Your app password

def test_smtp():
    print("🔧 Testing SMTP connection...")
    print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"   Username: {SMTP_USERNAME}")
    
    try:
        # Create SMTP connection
        print("\n📡 Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # Show detailed logs
        
        print("\n🔒 Starting TLS...")
        server.starttls()
        
        print("\n🔐 Logging in...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        print("\n✅ Login successful!")
        
        # Send test email
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = SMTP_USERNAME  # Send to yourself
        msg['Subject'] = "VIKRANTA Test Email"
        
        body = """
        This is a test email from VIKRANTA backend.
        
        Your OTP is: 123456
        
        If you received this, email sending is working!
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"\n📧 Sending test email to {SMTP_USERNAME}...")
        server.send_message(msg)
        
        print("\n✅ Email sent successfully!")
        print(f"\n📬 Check your inbox at {SMTP_USERNAME}")
        
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPossible issues:")
        print("1. App password is incorrect")
        print("2. 2FA not enabled on Gmail")
        print("3. App password has expired")
        print("4. Gmail is blocking less secure access")
        return False

if __name__ == '__main__':
    test_smtp()
