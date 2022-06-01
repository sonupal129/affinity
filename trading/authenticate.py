import fxcmpy


# CODE BELOW

class CreateConnection:

    def __init__(self, api_key, server="demo"):
        self.api = api_key
        self.server = server

    def connect(self):
        return fxcmpy.fxcmpy(access_token=self.api, log_level="error", server=self.server)

