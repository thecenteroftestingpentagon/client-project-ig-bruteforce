from flask import Flask, request, render_template_string
import time

app = Flask(__name__)

# --- Hardcoded Credentials ---
VALID_USERNAME = "testuser"
VALID_PASSWORD = "mypassword123"

# --- Brute-Force Protection ---
# Dictionary to store failed login attempts: {ip: [timestamp1, timestamp2, ...]}
failed_attempts = {}
# Dictionary to store when an IP is blocked: {ip: block_end_time}
blocked_ips = {}
MAX_ATTEMPTS = 5
LOCKOUT_PERIOD_SECONDS = 60 # 1 minute

# --- HTML Template for the Login Page ---
LOGIN_FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Login</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
    <div style="background-color: white; border: 1px solid #dbdbdb; padding: 40px; text-align: center; max-width: 350px; width: 100%;">
        <h1 style="font-family: 'Billabong', 'Grand Hotel', cursive; font-size: 50px; font-weight: normal; margin: 0 0 20px 0;">Instagram</h1>
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Phone number, username, or email" style="width: 90%; padding: 10px; margin-bottom: 10px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa;">
            <input type="password" name="password" placeholder="Password" style="width: 90%; padding: 10px; margin-bottom: 20px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa;">
            <button type="submit" style="width: 95%; padding: 10px; border: none; border-radius: 8px; background-color: #4cb5f9; color: white; font-weight: bold; cursor: pointer;">Log In</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Serves the login page."""
    return render_template_string(LOGIN_FORM_HTML)

@app.route('/login', methods=['POST'])
def login():
    """Handles login attempts and implements brute-force protection."""
    ip_addr = request.remote_addr

    # --- Check if IP is currently blocked ---
    if ip_addr in blocked_ips:
        if time.time() < blocked_ips[ip_addr]:
            remaining_time = int(blocked_ips[ip_addr] - time.time())
            print(f"INFO: Blocked IP {ip_addr} tried to log in. Blocked for {remaining_time} more seconds.")
            return "Too many failed attempts. Try again later.", 429
        else:
            # Block has expired, remove it
            del blocked_ips[ip_addr]
            if ip_addr in failed_attempts:
                del failed_attempts[ip_addr]

    # --- Process Login ---
    username = request.form.get('username')
    password = request.form.get('password')

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        # On successful login, clear any failed attempts from this IP
        if ip_addr in failed_attempts:
            del failed_attempts[ip_addr]
        print(f"SUCCESS: Successful login for user '{username}' from IP {ip_addr}.")
        return "Login successful", 200
    else:
        # --- Handle Failed Login Attempt ---
        print(f"FAILURE: Failed login attempt for user '{username}' from IP {ip_addr}.")
        
        # Log the failed attempt
        now = time.time()
        if ip_addr not in failed_attempts:
            failed_attempts[ip_addr] = []
        
        # Add current timestamp and filter out old attempts (older than 1 minute)
        failed_attempts[ip_addr].append(now)
        failed_attempts[ip_addr] = [t for t in failed_attempts[ip_addr] if now - t < LOCKOUT_PERIOD_SECONDS]
        
        # Check if the number of recent attempts exceeds the limit
        if len(failed_attempts[ip_addr]) >= MAX_ATTEMPTS:
            blocked_ips[ip_addr] = now + LOCKOUT_PERIOD_SECONDS
            print(f"BLOCK: IP {ip_addr} has been blocked for {LOCKOUT_PERIOD_SECONDS} seconds.")
            return "Too many failed attempts. Try again later.", 429

        return "Invalid credentials", 401

if __name__ == '__main__':
    # Running on 0.0.0.0 makes it accessible from the network,
    # but for this local-only project, 127.0.0.1 is also fine.
    app.run(host='0.0.0.0', port=5000)
