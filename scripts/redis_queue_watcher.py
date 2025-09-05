import sys
import time
from datetime import datetime

import requests

INTERVAL = 10
TIMEOUT = 10
API_BASE_URL = "http://localhost:8000"


def process_jobs() -> bool:
    try:
        response = requests.post(
            f"{API_BASE_URL}/process_job_results",
            timeout=TIMEOUT,
        )

        if response.status_code == 200:
            result = response.json()
            print(f"[{datetime.now()}] SUCCESS: {result['message']}")
            return True
        else:
            print(
                f"[{datetime.now()}] ERROR: Request failed with status {response.status_code}"
            )
            if response.text:
                print(f"[{datetime.now()}] Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"[{datetime.now()}] ERROR: Request timed out after {TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now()}] ERROR: Could not connect to {API_BASE_URL}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ERROR: Request failed: {e}")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: Unexpected error: {e}")
        return False


def main():
    print(f"[{datetime.now()}] Starting job processor...")
    print(f"[{datetime.now()}] API URL: {API_BASE_URL}")
    print(f"[{datetime.now()}] Interval: {INTERVAL} seconds")
    print(f"[{datetime.now()}] Timeout: {TIMEOUT} seconds")

    try:
        while True:
            success = process_jobs()
            time.sleep(INTERVAL)
    except Exception as e:
        print(f"[{datetime.now()}] FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
