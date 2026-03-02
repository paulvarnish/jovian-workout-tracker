class Success:
    # the operation was carried out successfully.
    def __init__(self, msg, data=None):
        self.msg = msg
        self.form = 0
        self.data = data
        
class Warning:
    # the operation was carried out, but there may be an issue.
    def __init__(self, msg, data=None):
        self.msg = msg
        self.form = -1
        self.data = data

class Error:
    # something went wrong.
    def __init__(self, typ, msg):
        self.typ = typ
        self.msg = msg
        self.form = 1

class Item:
    # helper to return data
    def __init__(self, data):
        self.data = data
        self.form = 10