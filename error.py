class APIError(Exception):
    def __init__(self, code, desc):
        self.code = code
        self.description = desc


class APIAuthError(APIError):
    def __init__(self, desc):
        self.code = 403
        self.description = desc

class APINotFoundError(APIError):
    def __init__(self, desc):
        self.code = 404
        self.description = desc

class APITypeError(APIError):
    def __init__(self, desc):
        self.code = 404
        self.description = desc

class APIMissingError(APIError):
    def __init__(self, desc):
        self.code = 404
        self.description = desc

class APIExternalError(APIError):
    def __init__(self, desc):
        self.code = 403
        self.description = desc

