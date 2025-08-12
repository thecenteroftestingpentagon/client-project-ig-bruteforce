import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import bcrypt
from datetime import datetime
import re

class Database:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URI')
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI environment variable is not set")
        
        try:
            self.client = MongoClient(self.mongo_uri)
            # Test the connection
            self.client.admin.command('ismaster')
            self.db = self.client.ig_bruteforce
            self.users = self.db.users
            
            # Create unique index on username and email
            self.users.create_index("username", unique=True)
            self.users.create_index("email", unique=True)
            
            print("Successfully connected to MongoDB!")
        except ConnectionFailure:
            raise ConnectionFailure("Failed to connect to MongoDB")
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username):
        """Validate username format (alphanumeric, underscore, dot allowed)"""
        pattern = r'^[a-zA-Z0-9._]{3,30}$'
        return re.match(pattern, username) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, "Password is valid"
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def create_user(self, username, email, password, full_name=None):
        """Create a new user with validation"""
        # Validate inputs
        if not self.validate_username(username):
            return False, "Invalid username format. Use 3-30 alphanumeric characters, dots, or underscores."
        
        if not self.validate_email(email):
            return False, "Invalid email format."
        
        is_valid_password, password_message = self.validate_password(password)
        if not is_valid_password:
            return False, password_message
        
        # Check if user already exists
        if self.users.find_one({"username": username}):
            return False, "Username already exists."
        
        if self.users.find_one({"email": email}):
            return False, "Email already registered."
        
        try:
            user_data = {
                "username": username,
                "email": email,
                "password": self.hash_password(password),
                "full_name": full_name or "",
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True,
                "login_attempts": 0,
                "last_failed_login": None
            }
            
            result = self.users.insert_one(user_data)
            return True, f"User {username} created successfully!"
            
        except DuplicateKeyError:
            return False, "Username or email already exists."
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        try:
            # Find user by username or email
            user = self.users.find_one({
                "$or": [
                    {"username": username},
                    {"email": username}
                ]
            })
            
            if not user:
                return False, "User not found."
            
            if not user.get('is_active', True):
                return False, "Account is deactivated."
            
            # Check password
            if self.verify_password(password, user['password']):
                # Update last login and reset failed attempts
                self.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "last_login": datetime.utcnow(),
                            "login_attempts": 0,
                            "last_failed_login": None
                        }
                    }
                )
                return True, "Login successful!"
            else:
                # Increment failed login attempts
                failed_attempts = user.get('login_attempts', 0) + 1
                update_data = {
                    "login_attempts": failed_attempts,
                    "last_failed_login": datetime.utcnow()
                }
                
                # Deactivate account after 5 failed attempts
                if failed_attempts >= 5:
                    update_data["is_active"] = False
                
                self.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": update_data}
                )
                
                if failed_attempts >= 5:
                    return False, "Account locked due to too many failed login attempts."
                else:
                    return False, f"Invalid password. {5 - failed_attempts} attempts remaining."
                
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def get_user(self, username):
        """Get user information (excluding password)"""
        user = self.users.find_one(
            {"$or": [{"username": username}, {"email": username}]},
            {"password": 0}  # Exclude password from result
        )
        return user
    
    def get_all_users(self):
        """Get all users for bruteforce testing (excluding passwords)"""
        users = list(self.users.find({}, {"username": 1, "email": 1, "_id": 0}))
        return users
    
    def close_connection(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
