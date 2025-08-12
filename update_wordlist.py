import random

# Read current wordlist
with open('wordlist.txt', 'r') as f:
    current_passwords = [line.strip() for line in f if line.strip()]

# Test passwords from our created users
test_passwords = [
    'password123',
    'admin123', 
    'john2024',
    'sarah789',
    'mikepass',
    'demo456',
    'testpass',
    '123456',
    'igtest2024',
    'weakpass'
]

# Remove duplicates and add new passwords
new_passwords = []
for password in test_passwords:
    if password not in current_passwords:
        new_passwords.append(password)

print(f"Adding {len(new_passwords)} new passwords to wordlist...")

# Insert new passwords at random positions
combined_passwords = current_passwords.copy()
for password in new_passwords:
    # Insert at random position
    insert_position = random.randint(0, len(combined_passwords))
    combined_passwords.insert(insert_position, password)
    print(f"✅ Added '{password}' at position {insert_position}")

# Write updated wordlist
with open('wordlist.txt', 'w') as f:
    for password in combined_passwords:
        f.write(password + '\n')

print(f"\n📊 Updated wordlist statistics:")
print(f"   Original passwords: {len(current_passwords)}")
print(f"   New passwords added: {len(new_passwords)}")
print(f"   Total passwords: {len(combined_passwords)}")
print(f"💾 Updated wordlist saved to: wordlist.txt")
