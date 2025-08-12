import requests
import random
import json

# Test users data
test_users = [
    {"username": "testuser1", "email": "test1@example.com", "fullname": "Test User One", "password": "password123"},
    {"username": "admin", "email": "admin@example.com", "fullname": "Administrator", "password": "admin123"},
    {"username": "john_doe", "email": "john@example.com", "fullname": "John Doe", "password": "john2024"},
    {"username": "sarah_wilson", "email": "sarah@example.com", "fullname": "Sarah Wilson", "password": "sarah789"},
    {"username": "mike_test", "email": "mike@example.com", "fullname": "Mike Test", "password": "mikepass"},
    {"username": "demo_user", "email": "demo@example.com", "fullname": "Demo User", "password": "demo456"},
    {"username": "test_account", "email": "test@example.com", "fullname": "Test Account", "password": "testpass"},
    {"username": "user123", "email": "user123@example.com", "fullname": "User One Two Three", "password": "123456"},
    {"username": "instagram_test", "email": "ig@example.com", "fullname": "Instagram Test", "password": "igtest2024"},
    {"username": "bruteforce_target", "email": "target@example.com", "fullname": "Bruteforce Target", "password": "weakpass"}
]

target_url = "http://localhost:5000"
session = requests.Session()

print("🚀 Creating test users...")
created_users = []
failed_users = []

for user in test_users:
    try:
        # Sign up the user
        signup_data = {
            'username': user['username'],
            'email': user['email'],
            'fullname': user['fullname'],
            'password': user['password']
        }
        
        response = session.post(f"{target_url}/signup", data=signup_data)
        
        if response.status_code in [200, 302]:  # Success or redirect
            print(f"✅ Created user: {user['username']} with password: {user['password']}")
            created_users.append(user)
        else:
            print(f"❌ Failed to create user: {user['username']} - Status: {response.status_code}")
            failed_users.append(user)
            
    except Exception as e:
        print(f"💥 Error creating user {user['username']}: {e}")
        failed_users.append(user)

print(f"\n📊 Summary:")
print(f"✅ Successfully created: {len(created_users)} users")
print(f"❌ Failed to create: {len(failed_users)} users")

# Save created users to a text file
with open("test_users.txt", "w") as f:
    f.write("# Test Users Created for Bruteforce Testing\n")
    f.write("# Format: username:password:email:fullname\n")
    f.write("# " + "="*50 + "\n\n")
    
    for user in created_users:
        f.write(f"{user['username']}:{user['password']}:{user['email']}:{user['fullname']}\n")
    
    if failed_users:
        f.write(f"\n# Failed to create:\n")
        for user in failed_users:
            f.write(f"# {user['username']}:{user['password']}:{user['email']}:{user['fullname']}\n")

print(f"💾 Test users saved to: test_users.txt")

# Test login for created users
print(f"\n🔐 Testing login for created users...")
successful_logins = []

for user in created_users:
    try:
        login_data = {
            'username': user['username'],
            'password': user['password']
        }
        
        response = session.post(f"{target_url}/login", data=login_data)
        
        if response.status_code == 200 and 'welcome' in response.text.lower():
            print(f"✅ Login successful: {user['username']}")
            successful_logins.append(user)
        else:
            print(f"❌ Login failed: {user['username']} - Status: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Login error for {user['username']}: {e}")

print(f"\n🎯 Ready for bruteforce testing!")
print(f"📧 Created {len(created_users)} users")
print(f"🔑 {len(successful_logins)} users can login successfully")

# Extract passwords for wordlist
passwords = [user['password'] for user in created_users]
print(f"\n🔤 Test passwords to add to wordlist:")
for password in passwords:
    print(f"   - {password}")
