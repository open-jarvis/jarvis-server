from jarvis import Client, Crypto

priv, pub = Crypto.keypair(1024)
c = Client("test-client", priv, pub)
print(c.rpub)
print(c.ready())
dec = c.request("jarvis/status", {})
print(dec)
