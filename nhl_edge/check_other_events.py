import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nhl.com/"
}

# Check Event 94 (Blocked Shot)
url_94 = "https://wsr.nhle.com/sprites/20252026/2025020360/ev94.json"
print(f"Checking Event 94 (Blocked Shot): {url_94}")
resp_94 = requests.get(url_94, headers=headers)
print(f"Status: {resp_94.status_code}")

# Check Event 97 (Goal) - Known Good
url_97 = "https://wsr.nhle.com/sprites/20252026/2025020360/ev97.json"
print(f"Checking Event 97 (Goal): {url_97}")
resp_97 = requests.get(url_97, headers=headers)
print(f"Status: {resp_97.status_code}")

