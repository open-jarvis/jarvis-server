import time
import random
from jarvis import Config, Database

ITERATIONS = 10

print(f"{ITERATIONS} iterations")

cnf = Config()
start = time.time()
for i in range(ITERATIONS):
        cnf.set("TEST-key", ''.join(random.choice("abcdef1234567890") for i in range(16)))
print(f"Setting keys: {(time.time() - start)/ITERATIONS :.2f}s")

start = time.time()
for i in range(ITERATIONS):
        cnf.get("TEST-key", None)
print(f"Getting keys: {(time.time() - start)/ITERATIONS :.2f}s")

start = time.time()
for i in range(ITERATIONS):
        Database().table("devices").find({ "_id": { "$eq": "server" } })
print(f"Find operation: {(time.time() - start)/ITERATIONS :.2f}s")


"""
Result:

10 iterations
Setting keys: 0.17s
Getting keys: 0.07s
Find operation: 0.10s
"""