from django.core.exceptions import NON_FIELD_ERRORS


class BaseCustomException(Exception):
    status_code = None
    error_dict = {}

    def __init__(self, error):
        Exception.__init__(self)
        self.error_dict = {}
        if isinstance(error, dict):
            for field, messages in error.items():
                self.error_dict[field] = []
                if isinstance(messages, list):
                    for message in messages:
                        self.error_dict[field].append(message)
                else:
                    self.error_dict[field] = [messages]
        elif isinstance(error, list):
            self.error_dict[NON_FIELD_ERRORS] = []
            for error in error:
                self.error_dict[NON_FIELD_ERRORS].append(error)
        else:
            self.error_dict[NON_FIELD_ERRORS] = [error]

    def to_dict(self):
        return self.error_dict


class InvalidRequest(BaseCustomException):
    status_code = 400


class MethodNotAllowed(BaseCustomException):
    status_code = 405


class StateDoesNotExist(BaseCustomException):
    status_code = 412


class TransitionDoesNotExist(BaseCustomException):
    status_code = 412


class TransitionNotAvailable(BaseCustomException):
    status_code = 412


class TransitionFailed(BaseCustomException):
    status_code = 412


class Forbidden(BaseCustomException):
    status_code = 403


class AlreadySubmitted(BaseCustomException):
    status_code = 422
