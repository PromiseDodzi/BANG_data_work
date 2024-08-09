
class CdstarError(Exception):
    def __init__(self, message, error, status_code):
        super(CdstarError, self).__init__(message)
        self.error = error.get('error') if isinstance(error, dict) else error
        self.status_code = status_code
