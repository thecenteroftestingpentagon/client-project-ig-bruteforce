from flask import Flask, request, render_template_string, jsonify, redirect, url_for, flash, session
import time
import os
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize database
try:
    db = Database()
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Database connection error: {e}")
    db = None

# --- Brute-Force Protection ---
failed_attempts = {}
blocked_ips = {}
MAX_ATTEMPTS = 5
LOCKOUT_PERIOD_SECONDS = 60  # 1 minute

# --- HTML Template for the Login Page ---
LOGIN_FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Grand+Hotel&display=swap" rel="stylesheet">
    <style>
        .error-message {
            color: #ed4956;
            font-size: 14px;
            text-align: center;
            margin: 10px 0;
        }
        .success-message {
            color: #00376b;
            font-size: 14px;
            text-align: center;
            margin: 10px 0;
        }
    </style>
</head>
<body style="font-family: Arial, sans-serif; background-color: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
    <div style="background-color: white; border: 1px solid #dbdbdb; padding: 40px; text-align: center; max-width: 350px; width: 100%;">
        <h1 style="font-family: 'Grand Hotel', cursive; font-size: 50px; font-weight: normal; margin: 0 0 20px 0; color: #262626;">Instagram</h1>
        
        {% if error %}
        <div class="error-message">{{ error }}</div>
        {% endif %}
        
        {% if success %}
        <div class="success-message">{{ success }}</div>
        {% endif %}
        
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Phone number, username, or email" 
                   style="width: 90%; padding: 10px; margin-bottom: 10px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa; font-size: 14px;" required>
            <input type="password" name="password" placeholder="Password" 
                   style="width: 90%; padding: 10px; margin-bottom: 20px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa; font-size: 14px;" required>
            <button type="submit" style="width: 95%; padding: 10px; border: none; border-radius: 8px; background-color: #4cb5f9; color: white; font-weight: bold; cursor: pointer; font-size: 14px;">Log In</button>
        </form>
        
        <div style="margin: 20px 0; color: #8e8e8e; font-size: 13px;">
            <span>OR</span>
        </div>
        
        <div style="margin: 20px 0;">
            <span style="color: #8e8e8e; font-size: 14px;">Don't have an account? </span>
            <a href="/signup" style="color: #0095f6; text-decoration: none; font-weight: 600;">Sign up</a>
        </div>
    </div>
</body>
</html>
"""

# --- HTML Template for the Sign Up Page ---
SIGNUP_FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Sign Up</title>
    <link href="https://fonts.googleapis.com/css2?family=Grand+Hotel&display=swap" rel="stylesheet">
    <style>
        .error-message {
            color: #ed4956;
            font-size: 14px;
            text-align: center;
            margin: 10px 0;
        }
        .success-message {
            color: #00376b;
            font-size: 14px;
            text-align: center;
            margin: 10px 0;
        }
    </style>
</head>
<body style="font-family: Arial, sans-serif; background-color: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
    <div style="background-color: white; border: 1px solid #dbdbdb; padding: 40px; text-align: center; max-width: 350px; width: 100%;">
        <h1 style="font-family: 'Grand Hotel', cursive; font-size: 50px; font-weight: normal; margin: 0 0 20px 0; color: #262626;">Instagram</h1>
        <p style="color: #8e8e8e; font-size: 17px; font-weight: 600; margin: 0 0 20px 0;">Sign up to see photos and videos from your friends.</p>
        
        {% if error %}
        <div class="error-message">{{ error }}</div>
        {% endif %}
        
        {% if success %}
        <div class="success-message">{{ success }}</div>
        {% endif %}
        
        <form action="/signup" method="post">
            <input type="email" name="email" placeholder="Email" 
                   style="width: 90%; padding: 10px; margin-bottom: 10px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa; font-size: 14px;" required>
            <input type="text" name="fullname" placeholder="Full Name" 
                   style="width: 90%; padding: 10px; margin-bottom: 10px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa; font-size: 14px;" required>
            <input type="text" name="username" placeholder="Username" 
                   style="width: 90%; padding: 10px; margin-bottom: 10px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa; font-size: 14px;" required>
            <input type="password" name="password" placeholder="Password" 
                   style="width: 90%; padding: 10px; margin-bottom: 20px; border: 1px solid #dbdbdb; border-radius: 3px; background-color: #fafafa; font-size: 14px;" required>
            <button type="submit" style="width: 95%; padding: 10px; border: none; border-radius: 8px; background-color: #4cb5f9; color: white; font-weight: bold; cursor: pointer; font-size: 14px;">Sign Up</button>
        </form>
        
        <p style="color: #8e8e8e; font-size: 12px; margin: 20px 0;">
            By signing up, you agree to our Terms, Data Policy and Cookies Policy.
        </p>
        
        <div style="margin: 20px 0;">
            <span style="color: #8e8e8e; font-size: 14px;">Have an account? </span>
            <a href="/" style="color: #0095f6; text-decoration: none; font-weight: 600;">Log in</a>
        </div>
    </div>
</body>
</html>
"""

# SUCCESS/DASHBOARD TEMPLATE
SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Grand+Hotel&display=swap" rel="stylesheet">
</head>
<body style="font-family: Arial, sans-serif; background-color: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
    <div style="background-color: white; border: 1px solid #dbdbdb; padding: 40px; text-align: center; max-width: 400px; width: 100%;">
        <h1 style="font-family: 'Grand Hotel', cursive; font-size: 40px; font-weight: normal; margin: 0 0 20px 0; color: #262626;">Instagram</h1>
        <h2 style="color: #262626; margin-bottom: 10px;">Welcome, {{ user.username }}! 🎉</h2>
        <p style="color: #8e8e8e; margin-bottom: 20px;">{{ message }}</p>
        
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left;">
            <h3 style="color: #262626; margin-top: 0;">Account Information:</h3>
            <p><strong>Username:</strong> {{ user.username }}</p>
            <p><strong>Email:</strong> {{ user.email }}</p>
            <p><strong>Full Name:</strong> {{ user.full_name or 'Not provided' }}</p>
            <p><strong>Member Since:</strong> {{ user.created_at.strftime('%B %d, %Y') if user.created_at else 'Unknown' }}</p>
            <p><strong>Last Login:</strong> {{ user.last_login.strftime('%B %d, %Y at %I:%M %p') if user.last_login else 'First login' }}</p>
        </div>
        
        <div style="margin-top: 30px;">
            <a href="/logout" style="color: #0095f6; text-decoration: none; font-weight: 600; margin-right: 20px;">Logout</a>
            <a href="/" style="color: #8e8e8e; text-decoration: none;">Back to Login</a>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Serves the login page."""
    error = session.pop('error', None)
    success = session.pop('success', None)
    return render_template_string(LOGIN_FORM_HTML, error=error, success=success)

@app.route('/signup')
def signup_page():
    """Serves the sign up page."""
    error = session.pop('error', None)
    success = session.pop('success', None)
    return render_template_string(SIGNUP_FORM_HTML, error=error, success=success)

@app.route('/signup', methods=['POST'])
def signup():
    """Handles user registration with MongoDB."""
    if not db:
        session['error'] = "Database connection unavailable"
        return redirect(url_for('signup_page'))
    
    email = request.form.get('email', '').strip()
    fullname = request.form.get('fullname', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # Basic validation
    if not all([email, fullname, username, password]):
        session['error'] = "All fields are required"
        return redirect(url_for('signup_page'))
    
    # Create user in MongoDB
    success, message = db.create_user(username, email, password, fullname)
    
    if success:
        session['success'] = message
        print(f"✅ SUCCESS: New user registered - Username: '{username}', Email: '{email}', Full Name: '{fullname}'")
        return redirect(url_for('home'))
    else:
        session['error'] = message
        print(f"❌ SIGNUP ERROR: {message} for username '{username}'")
        return redirect(url_for('signup_page'))

@app.route('/login', methods=['POST'])
def login():
    """Handles login attempts with MongoDB and brute-force protection."""
    if not db:
        session['error'] = "Database connection unavailable"
        return redirect(url_for('home'))
    
    ip_addr = request.remote_addr

    # --- Check if IP is currently blocked ---
    if ip_addr in blocked_ips:
        if time.time() < blocked_ips[ip_addr]:
            remaining_time = int(blocked_ips[ip_addr] - time.time())
            session['error'] = f"Too many failed attempts. Try again in {remaining_time} seconds."
            print(f"🚫 BLOCKED: IP {ip_addr} tried to log in. Blocked for {remaining_time} more seconds.")
            return redirect(url_for('home'))
        else:
            # Block has expired, remove it
            del blocked_ips[ip_addr]
            if ip_addr in failed_attempts:
                del failed_attempts[ip_addr]

    # --- Process Login ---
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        session['error'] = "Username and password are required"
        return redirect(url_for('home'))

    # Authenticate with MongoDB
    success, message = db.authenticate_user(username, password)

    if success:
        # On successful login, clear any failed attempts from this IP
        if ip_addr in failed_attempts:
            del failed_attempts[ip_addr]
        
        # Get user info for dashboard
        user = db.get_user(username)
        session['username'] = user['username']
        
        print(f"✅ SUCCESS: Successful login for user '{username}' from IP {ip_addr}.")
        return render_template_string(SUCCESS_TEMPLATE, user=user, message=message)
    else:
        # --- Handle Failed Login Attempt ---
        print(f"❌ FAILURE: Failed login attempt for user '{username}' from IP {ip_addr}. Reason: {message}")
        
        # Log the failed attempt for brute force protection
        now = time.time()
        if ip_addr not in failed_attempts:
            failed_attempts[ip_addr] = []
        
        # Add current timestamp and filter out old attempts
        failed_attempts[ip_addr].append(now)
        failed_attempts[ip_addr] = [t for t in failed_attempts[ip_addr] if now - t < LOCKOUT_PERIOD_SECONDS]
        
        # Check if the number of recent attempts exceeds the limit
        if len(failed_attempts[ip_addr]) >= MAX_ATTEMPTS:
            blocked_ips[ip_addr] = now + LOCKOUT_PERIOD_SECONDS
            session['error'] = f"Too many failed attempts. IP blocked for {LOCKOUT_PERIOD_SECONDS} seconds."
            print(f"🚫 BLOCK: IP {ip_addr} has been blocked for {LOCKOUT_PERIOD_SECONDS} seconds.")
        else:
            attempts_left = MAX_ATTEMPTS - len(failed_attempts[ip_addr])
            session['error'] = f"{message} ({attempts_left} attempts remaining)"

        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    session['success'] = "Successfully logged out"
    return redirect(url_for('home'))

@app.route('/api/users')
def api_users():
    """API endpoint to get all users (for bruteforce testing)."""
    if not db:
        return jsonify({"error": "Database connection unavailable"}), 500
    
    try:
        users = db.get_all_users()
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "database": "connected" if db else "disconnected",
        "timestamp": time.time()
    }
    return jsonify(status)

if __name__ == '__main__':
    print("🚀 Starting Instagram Clone with MongoDB...")
    print("📝 Available endpoints:")
    print("   - / (Login page)")
    print("   - /signup (Sign up page)")
    print("   - /api/users (Get all users)")
    print("   - /health (Health check)")
    
    # Running on 0.0.0.0 makes it accessible from the network
    app.run(host='0.0.0.0', port=5000, debug=True)
