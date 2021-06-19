"""
Copyright (c) 2021 Philipp Scheer
"""

class APIDOC:
    def jarvis_client_+_set_public-key():
        """
`jarvis/client/+/set/public-key`

No documentation available!"""

    def jarvis_nlu_parse():
        """
`jarvis/nlu/parse`

Parse a sentence  
The sentence will be parsed by the trained NLU.  
If the NLU is not trained yet, throw an exception"""

    def jarvis_nlu_status():
        """
`jarvis/nlu/status`

Starts a status server
Returns an object: {    trained: True|False, 
                        training: True|False,
                        avg-time: { 
                            training: int, 
                            parsing: int 
                        }, 
                        total-time: { 
                            training: int, 
                            parsing: int 
                        }, 
                        count: { 
                            training: int, 
                            parsing: int 
                        } 
                    }"""

    def jarvis_nlu_train():
        """
`jarvis/nlu/train`

Train NLU  
If it receives a valid message, train the NLU engine and save both the trained model and training data into the database"""

    def jarvis_restart():
        """
`jarvis/restart`

No documentation available!"""

    def jarvis_server_get_public-key():
        """
`jarvis/server/get/public-key`

No documentation available!"""

    def jarvis_status():
        """
`jarvis/status`

No documentation available!"""

    def jarvis_update_download():
        """
`jarvis/update/download`

Download an update  
Make sure to call `jarvis/update/poll` before downloading  
Returns:
```python
{
    "success": true|false,
    "error?": ...
}
```"""

    def jarvis_update_install():
        """
`jarvis/update/install`

Install an update  
Make sure to call `jarvis/update/poll` and `jarvis/update/download` before installing  
Returns:
```python
{
    "success": true|false,
    "error?": ...
}
```"""

    def jarvis_update_poll():
        """
`jarvis/update/poll`

Manually poll for new updates  
Checks the update server and compare the remote to the local version  
If an update is available, retrieve the update notes  
Returns update information:
```python
{
    "success": true|false,
    "update": {
            "remote": str, # version string (eg. 1.2, 2.15.3)
            "local": str, # version string (eg. 1.2, 2.15.3)
            "name": {
                "remote": str, # version name (eg. Beta)
                "local": str # version name (eg. Aplha)
            },
            "update-size": int, # size of update in bytes
            "server": "jarvisdata.philippscheer.com",
            "timestamp": {
                "local": int, # unix timestamp of last file change
                "remote": int # unix timestamp of last file change
            },
            "notes": {
                "remote": str, # markdown of remote update notes
                "local": str # markdown of local update notes
            }
        }|{}
}
```"""

    def jarvis_update_status():
        """
`jarvis/update/status`

Gets the current update status
Returns:
```python
{
    "success": true|false,
    "current-action": "idle|downloading|installing",
    "available": {
        "download": true|false,
        "install": true|false
    },
    "schedule-install": int|false, # timestamp of scheduled install
    "progress": {
        "download": float # float percentage of progress 0-1
    }
}
```"""

