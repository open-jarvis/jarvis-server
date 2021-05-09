"""
This module provides classes to handle crucial Jarvis functionalities

Subclasses include:
* [`API.py`](core/API.html)  
Handles Database connection for API requests

* [`HTTPServer.py`](core/HTTPServer.html)  
Serves the API to the outside world (devices, etc...) via HTTP

* [`MQTTServer.py`](core/MQTTServer.html)  
Serves the API to the inside world (applications) via MQTT

* [`Permissions.py`](core/Permissions.html)  
Permission handling for API calls

* [`Trace.py`](core/Trace.html)  
A tracing module to keep track of executing functions and exception tracebacks
"""