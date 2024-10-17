import requests
import urllib3

urllib3.disable_warnings

def test_proxy(proxy):
    try:
        response = requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.ok:
            print(f"Proxy {proxy} is working. Your IP: {response.json()['origin']}")
        else:
            print(f"Proxy {proxy} returned status code {response.status_code}")
    except Exception as e:
        print(f"Error occurred while testing proxy {proxy}: {e}")

def main():
    proxies = [
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d62:glby77lonnnr@proxy.oculus-proxy.com:31112",
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d63:glby77lonnnr@proxy.oculus-proxy.com:31112",
        # Add more proxies to test here
    ]

    for proxy in proxies:
        test_proxy(proxy)

if __name__ == "__main__":
    main()