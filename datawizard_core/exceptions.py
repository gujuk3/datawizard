class DataWizardError(Exception):
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class InvalidFileError(DataWizardError):
    pass


class ValidationError(DataWizardError):
    pass

class PreprocessingError(DataWizardError):
    pass

class TrainingError(DataWizardError):
    pass

class LLMError(DataWizardError):
    pass