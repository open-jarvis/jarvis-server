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
    from classes import API
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

    x, id = API.id__ask({"token": token, "type": "call", "name": "Mom is calling...", "infos": "Accept or decline call!", "options": [
        {"text": "accept",
         "color": "green",
         "icon": "accept"}, {"text": "reject",
                             "color": "red",
                             "icon": "reject"}
    ]})
    print("id__ask", (x, id))
    print("id__answer", API.id__answer({"token": token, "id": id, "option": 1, "description": "we're rejecting the call"}))
    print("id__answer", API.id__answer({"token": token, "id": id, "option": 0, "description": "we're accepting the call"}))
    print("id__scan::no-filter", API.id__scan({"token": token}))
    print("id__scan::token-filter", API.id__scan({"token": token, "target-token": token}))
    print("id__scan::type-filter", API.id__scan({"token": token, "type": "call"}))
    print("id__scan::both-filter", API.id__scan({"token": token, "target-token": token, "type": "call"}))
    print("id__scan::failed-filter", API.id__scan({"token": token, "target-token": "ffffff"}))
    print("id__scan::failed-filter", API.id__scan({"token": token, "target-token": "ffffff", "type": "call"}))
    print("id__scan::failed-filter", API.id__scan({"token": token, "type": "test"}))

    print("id__delete", API.id__delete({"token": token, "id": id}))
    API.unregister_device({"target-token": token})

    assert 1 == 1