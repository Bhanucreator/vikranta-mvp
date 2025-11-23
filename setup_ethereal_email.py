"""
Generate Ethereal Email credentials for testing
Run this script to get test SMTP credentials
"""
import requests

print("🔧 Generating test email credentials...")

response = requests.post('https://api.nodemailer.com/user')
if response.status_code == 200:
    data = response.json()
    print("\n✅ Test Email Credentials Generated!")
    print("=" * 60)
    print(f"SMTP_SERVER = smtp.ethereal.email")
    print(f"SMTP_PORT = 587")
    print(f"SMTP_USERNAME = {data['user']}")
    print(f"SMTP_PASSWORD = {data['pass']}")
    print("=" * 60)
    print(f"\n📧 Web Interface: {data['web']}")
    print("View all emails sent to this address at the web interface above")
    print("\nAdd these to Railway backend variables!")
else:
    print("❌ Failed to generate credentials")
