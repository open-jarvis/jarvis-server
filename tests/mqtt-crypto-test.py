from jarvis import MQTT, Crypto, Exiter

priv, pub = Crypto.keypair(1024)
rpriv, rpub = Crypto.keypair(1024)


# CRYPTO TEST
msg = b"hello world"
enc = Crypto.encrypt(msg, pub)
dec = Crypto.decrypt(enc, priv)
assert dec == msg, "Crypto class is not working"


m = MQTT("test-client", priv, pub, rpub)
m2 = MQTT("test-client-2", rpriv, rpub, pub)

def cb(t,m,cid):
    print("topic", t)
    print("message", m)
    print("client-id", cid)

m2.on_message(cb)
m2.subscribe("test/hi")

m.publish("test/hi", "hello braa")

# ALSO WORKS NOW!

Exiter.mainloop(0.1)