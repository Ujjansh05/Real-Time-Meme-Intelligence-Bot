import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server(timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        print("Waiting for server...")
    print("Server timed out.")
    return False

def test_endpoints():
    if not wait_for_server():
        sys.exit(1)

    print("\n--- Testing /trending ---")
    try:
        response = requests.get(f"{BASE_URL}/trending")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Testing /explain ---")
    try:
        meme_text = "When the code works on the first try"
        response = requests.get(f"{BASE_URL}/explain", params={"meme": meme_text})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Testing /remix ---")
    try:
        meme_text = "My code compiling without errors"
        response = requests.get(f"{BASE_URL}/remix", params={"meme": meme_text})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoints()
