# ruff: noqa

import gzip
import json
import os

import httpx


auth_token = os.environ["authToken"]
auth_cookie = os.environ["authCookie"]


cozy_headers = {
    "Authorization": auth_token,
    "Cookie": auth_cookie,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

ralph_headers = {
    "X-Auth-Token": auth_token,
    "Cookie": auth_cookie,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Experience-API-Version": "1.0.3"
}

cozy_client = httpx.Client(base_url="http://cozy.localhost:8080/data/com.inokufu.statements/", headers=cozy_headers, timeout=None)
ralph_client = httpx.Client(base_url="http://localhost:8100/xAPI/statements/", headers=ralph_headers, timeout=None)

# delete database
response = cozy_client.delete(url="/")
print(response.json())
assert response.status_code in [200, 404]

# create indices
response = cozy_client.post("/_index", json={"index": {"fields": ["source.id"]}})
print(response.json())
assert response.status_code == 200

response = cozy_client.post("/_index", json={"index": {"fields": ["source.timestamp"]}})
print(response.json())
assert response.status_code == 200

# insert data
with gzip.open("data/statements.json.gz", "rb") as f:
    content = f.read().decode("utf-8")
    json_content = "[" + ",".join(content.split("\n"))[:-1] + "]"
    data = json.loads(json_content)

response = ralph_client.post("/", json=data[:200])
print(response.json())
assert response.status_code == 200

# get data
response = ralph_client.get("/")
print(json.dumps(response.json(), indent=2))
assert response.status_code == 200

cozy_client.close()
ralph_client.close()
