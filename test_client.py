# File: test/test_client.py
# honeyserver.py の簡単な動作確認用クライアント

import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:18080"


def test_get():
    with urllib.request.urlopen(BASE_URL + "/", timeout=3) as response:
        body = response.read().decode("utf-8")
        print("GET status:", response.status)
        print("login form:", "username" in body and "password" in body)


def test_post():
    form = {
        "username": "test_student",
        "password": "qwerty1234"
    }
    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + "/login",
        data=data,
        method="POST"
    )

    try:
        urllib.request.urlopen(request, timeout=3)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        print("POST status:", error.code)
        print("failed page:", "Login Failed" in body)


if __name__ == "__main__":
    test_get()
    test_post()
