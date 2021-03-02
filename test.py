#!/usr/bin/python3

import time
from jarvis import Database


def test_jarvis_systempackage():
    import jarvis

    assert 1 == 1


def test_db_connection():
    Database(name="test").drop()
    db = Database(name="test")

    table = db.table(str(int(time.time())))
    table.insert({
        "hello": "world",
        "current_time": time.time()
    })
    table.filter({"hello": "world"}).update({
        "hello": "world2"
    })
    db.drop()

    assert 1 == 1


def test_api_functions():
    from core import API
    x, token = API.generate_token({"permission-level": 4})
    print("generate_token", (x, token))
    print("register_device", API.register_device(
        {"name": "jarvis test script", "token": token, "type": "tester"}))
    print("unregister_device", API.unregister_device({"target-token": token}))

    x, token = API.generate_token({"permission-level": 4})
    API.register_device({"name": "jarvis test script",
                         "token": token, "type": "tester"})

    print("get_devices::no-filter", API.get_devices({"token": token}))
    print("get_devices::token-filter",
          API.get_devices({"token": token, "target-token": token}))
    print("get_devices::failed-filter",
          API.get_devices({"token": token, "target-token": "ffffff"}))

    print("set_property", API.set_property(
        {"token": token, "property": "hello", "value": "property!"}))
    x, result = API.get_property({"token": token, "property": "hello"})
    print("get_property", list(result))

    print("hello::before", Database().table(
        "devices").filter({"token": token})[0]["last-seen"])
    print("hello", API.hello({"token": token}))
    print("hello::after", Database().table(
        "devices").filter({"token": token})[0]["last-seen"])

    print("am_i_registered", API.am_i_registered({"token": token}))

    x, id = API.decision__ask({"token": token, "type": "call", "title": "Mom is calling...", "infos": "Accept or decline call!", "options": [
        {"text": "accept",
         "color": "green",
         "icon": "accept"}, {"text": "reject",
                             "color": "red",
                             "icon": "reject"}
    ]})
    print("decision__ask", (x, id))
    print("decision__answer", API.decision__answer(
        {"token": token, "id": id, "option": 1, "description": "we're rejecting the call"}))
    print("decision__answer", API.decision__answer(
        {"token": token, "id": id, "option": 0, "description": "we're accepting the call"}))
    print("decision__scan::no-filter", API.decision__scan({"token": token}))
    print("decision__scan::token-filter",
          API.decision__scan({"token": token, "target-token": token}))
    print("decision__scan::type-filter",
          API.decision__scan({"token": token, "type": "call"}))
    print("decision__scan::both-filter",
          API.decision__scan({"token": token, "target-token": token, "type": "call"}))
    print("decision__scan::failed-filter",
          API.decision__scan({"token": token, "target-token": "ffffff"}))
    print("decision__scan::failed-filter",
          API.decision__scan({"token": token, "target-token": "ffffff", "type": "call"}))
    print("decision__scan::failed-filter",
          API.decision__scan({"token": token, "type": "test"}))

    print("decision__delete", API.decision__delete({"token": token, "id": id}))
    API.unregister_device({"target-token": token})

    assert 1 == 1


def test_jarvis_application_backend():
    from jarvis import Jarvis
    j = Jarvis(client_id="tester-script")
    j.register("tester-script-name")
    print("get_devices", j.get_devices())
    print("set_property", j.set_property("test", "123"))
    print("get_property::property_only", j.get_property("test"))
    print("get_property::property_and_token", j.get_property("test", j.token))
    print("get_property::fail_property_only", j.get_property("test2"))
    print("get_property::fail_property_and_token",
          j.get_property("test2", j.token))
    x, id = j.decision_ask("call", "Mom is calling...",
                           "Mom (+4367761244487) is calling", [{"text": "accept"}, {"text": "reject"}])
    print("decision_ask", (x, id))
    print("decision_answer", j.decision_answer(id, 1))
    print("decision_scan::empty", j.decision_scan())
    print("decision_scan::token", j.decision_scan(j.token))
    print("decision_scan::type", j.decision_scan(typ="call"))
    print("decision_scan::token_and_type", j.decision_scan(j.token, "call"))
    print("decision_scan::fail_token", j.decision_scan("abc"))
    print("decision_scan::fail_type", j.decision_scan(typ="abc"))
    print("decision_scan::fail_token_and_type", j.decision_scan("abc", "abc"))
    print("decision_delete::fail", j.decision_delete("abc"))
    print("decision_delete", j.decision_delete(id))


def test_performance():
    from jarvis import Jarvis
    import time
    j = Jarvis(client_id="tester-script")
    j.register("tester-script-name")
    count = 100
    start = time.time()
    for i in range(count):
        j.set_property("test", f"abc{i}")
    end = time.time()
    took = end - start
    print(
        f"jarvis secure: took {took}s to make {count} modifies ({count/took} mods/sec)")

    j.faster = True
    start = time.time()
    for i in range(count):
        j.set_property("test", f"abc{i}")
    end = time.time()
    took = end - start
    print(
        f"jarvis insecure: took {took}s to make {count} modifies ({count/took} mods/sec)")

    from jarvis import Database
    db = Database(name="test")
    table = db.table("test", True)
    start = time.time()
    for i in range(count):
        table.insert({f"test{i}": "abc"})
    end = time.time()
    took = end - start
    print(
        f"jarvis db: took {took}s to make {count} inserts ({count/took} insr/sec)")

    import couchdb2
    server = couchdb2.Server(
        f"http://127.0.0.1:5984/", username="jarvis", password="jarvis")
    table = server.get("test2") if "test2" in server else server.create("test2")
    start = time.time()
    for i in range(count):
        table.put({f"test{i}": "abc"})
    end = time.time()
    took = end - start
    print(
        f"couchdb: took {took}s to make {count} inserts ({count/took} insr/sec)")
    
