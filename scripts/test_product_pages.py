
import requests

def check_url(url):
    try:
        resp = requests.get(url)
        print(f"URL: {url} -> Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error Content: {resp.text[:500]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_url("http://127.0.0.1:8000/products/")
    check_url("http://127.0.0.1:8000/products/1/")
