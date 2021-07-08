"""
Run using:
```bash
kill -9 `jobs -p` ; PYTHONPATH=. python3 tests/client-creation-test.py
```
"""

from jarvis import Colors, Client, Database, Crypto
from classes import Client as backendClient

Database().table("devices").drop()


# THIS HAPPENS ON THE SERVER
# here we initialize a new client
cl = backendClient.Client.new({
    "ip": "127.0.0.1",
    "secure": True
})
cl.save()
print(f"Created real client with id '{cl.id}'")

cl2 = backendClient.Client.new({
    "ip": "127.0.0.1",
    "secure": True
})
cl2.save()
print(f"Created rogue client with id '{cl2.id}'")


# THIS HAPPENS ON THE CLIENT
priv, pub = Crypto.keypair(1024)
rogue_priv, rogue_pub = Crypto.keypair(2048)
# we need to store these keys on the client device
cclient = Client(cl.id, private_key=priv, public_key=pub, server_public_key=None) 
# if the server pub key is none, it tries to retrieve it
rogue_client = Client(cl2.id, private_key=rogue_priv, public_key=rogue_pub, server_public_key=None)

print("@@@@@@@@@@@@@@@@@ KEYS @@@@@@@@@@@@@@@@@")
print("Real client:", pub)
print("Rogue client:", rogue_pub)
npriv, npub = Crypto.keypair(2048)
print("Real client NEW:", npub)
print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

success = cclient.update_keys(npriv, npub)
print(f"Update real client pub: {success}")

rogue_client.pub = pub
resp = rogue_client.request(f"jarvis/client/{cl.id}/set/public-key", {"public-key": rogue_pub}, wait_for_response=False)
rogue_client.pub = rogue_pub
print(f"Rogue client updating real client pub: {resp}")

print(cl.data)

cl.reload()
cl2.reload()

print(cl.data)
print(cl.get("public-key", None), pub)

assert cl.get("public-key", None) == npub, "The rogue client succeeded!"
assert cl2.get("public-key", None) == rogue_pub, "The rogue client made a mistake!"

print(f"{Colors.GREEN}All tests passed{Colors.END}")