import time
import random
from jarvis import Config, Database

ITERATIONS = 100
DOC_ID = "server"

print(f"{ITERATIONS} iterations")

start = time.time()
for i in range(ITERATIONS):
    Database().table("devices").find({ "_id": { "$eq": DOC_ID } })
print(f"Find operation: {(time.time() - start)/ITERATIONS :.2f}s")

start = time.time()
for i in range(ITERATIONS):
    Database().table("devices").get(DOC_ID)
print(f"Get operation: {(time.time() - start)/ITERATIONS :.2f}s")


"""
Result:

100 iterations
Find operation: 0.09s
Get operation: 0.07s
"""