# Instagram Brute-Force Project

This project demonstrates a brute-force attack against a simulated Instagram login page using Flask and Python. It includes a simple web server (`app.py`) and a brute-force script (`bruteforce.py`).

## Structure
- `app.py`: Flask web server with brute-force protection
- `bruteforce.py`: Multi-threaded brute-force script
- `requirements.txt`: Python dependencies
- `wordlist.txt`: Password list for brute-force attempts
- `Dockerfile`: Containerization setup

## Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run the Flask server: `python app.py`
3. Run the brute-force script: `python bruteforce.py`
4. Optionally, use Docker to containerize the app

## Disclaimer
**This project is only for educational purposes.**

Do not use this code for unauthorized testing or attacks on real systems. Always have permission before performing any security testing.
