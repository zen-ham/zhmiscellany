import hashlib

STORED = hashlib.sha256(b"actual-password").hexdigest()

def authenticate(pw):
    return hashlib.sha256(pw.encode()).hexdigest() == STORED

for attempt in ["password", "admin", "actual-password"]:
    print(attempt, "GRANTED" if authenticate(attempt) else "DENIED")
