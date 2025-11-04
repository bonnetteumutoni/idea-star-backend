import smtplib, os, sys

host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
port = int(os.getenv("EMAIL_PORT", 587))
user = os.getenv("EMAIL_HOST_USER")
password = os.getenv("EMAIL_HOST_PASSWORD")

print("host:", host, "port:", port)
print("user repr:", repr(user))
print("password set:", bool(password))

try:
    s = smtplib.SMTP(host, port, timeout=10)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(user, password)
    print("SMTP login succeeded")
except Exception as e:
    print("SMTP login failed:", repr(e))
    sys.exit(1)
finally:
    try: s.quit()
    except: pass