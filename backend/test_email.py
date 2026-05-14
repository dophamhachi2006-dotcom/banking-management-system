"""Quick test email sender. Usage: python backend/test_email.py you@example.com"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.notification_service import notifier

if __name__ == "__main__":
    to = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    ok = notifier.send_email(to, "BMS Test Email",
                             "<h1>Hello from Banking System!</h1><p>SMTP works.</p>")
    print("OK" if ok else "FAILED")
