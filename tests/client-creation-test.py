"""
Run using:
```bash
kill -9 `jobs -p` ; PYTHONPATH=. python3 tests/client-creation-test.py
```
"""

from jarvis import Client, Database, Crypto
from classes import Client as backendClient

Database().table("clients").drop()


# THIS HAPPENS ON THE SERVER
# here we initialize a new client
cl = backendClient.Client.new({
    "ip": "127.0.0.1",
    "secure": True
})
cl.save()

print(f"Created Client with id '{cl.id}'")


# THIS HAPPENS ON THE CLIENT
priv, pub = Crypto.keypair(1024)
# we need to store these keys on the client device
cclient = Client(cl.id, private_key=priv, public_key=pub, server_public_key=None) 
# if the server pub key is none, it tries to retrieve it


