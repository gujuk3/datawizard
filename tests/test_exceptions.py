import pytest
from datawizard_core.exceptions import (
    DataWizardError,
    InvalidFileError,
    ValidationError,
    PreprocessingError,
    TrainingError,
    LLMError,
)


class TestDataWizardError:
    def test_message_stored(self):
        e = DataWizardError("something went wrong")
        assert e.message == "something went wrong"

    def test_default_details_empty_dict(self):
        e = DataWizardError("msg")
        assert e.details == {}

    def test_custom_details_stored(self):
        e = DataWizardError("msg", details={"key": "value"})
        assert e.details == {"key": "value"}

    def test_str_representation(self):
        e = DataWizardError("my error")
        assert str(e) == "my error"

    def test_to_dict_contains_required_keys(self):
        e = DataWizardError("msg", details={"k": 1})
        d = e.to_dict()
        assert d["error_type"] == "DataWizardError"
        assert d["message"] == "msg"
        assert d["details"] == {"k": 1}

    def test_is_exception(self):
        e = DataWizardError("x")
        assert isinstance(e, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(DataWizardError) as exc_info:
            raise DataWizardError("raised error", details={"a": 1})
        assert exc_info.value.message == "raised error"


class TestValidationError:
    def test_is_subclass(self):
        e = ValidationError("invalid")
        assert isinstance(e, DataWizardError)

    def test_to_dict_error_type(self):
        e = ValidationError("bad input")
        assert e.to_dict()["error_type"] == "ValidationError"

    def test_message_and_details(self):
        e = ValidationError("bad col", details={"column": "age"})
        assert e.message == "bad col"
        assert e.details["column"] == "age"

    def test_caught_as_data_wizard_error(self):
        with pytest.raises(DataWizardError):
            raise ValidationError("v error")


class TestPreprocessingError:
    def test_is_subclass(self):
        e = PreprocessingError("failed")
        assert isinstance(e, DataWizardError)

    def test_to_dict_error_type(self):
        e = PreprocessingError("preprocess failed")
        assert e.to_dict()["error_type"] == "PreprocessingError"

    def test_caught_as_data_wizard_error(self):
        with pytest.raises(DataWizardError):
            raise PreprocessingError("p error")


class TestTrainingError:
    def test_is_subclass(self):
        e = TrainingError("training failed")
        assert isinstance(e, DataWizardError)

    def test_to_dict_error_type(self):
        e = TrainingError("convergence failed")
        assert e.to_dict()["error_type"] == "TrainingError"

    def test_with_algorithm_details(self):
        e = TrainingError("fit failed", details={"algorithm": "knn", "reason": "NaN in input"})
        d = e.to_dict()
        assert d["details"]["algorithm"] == "knn"

    def test_caught_as_data_wizard_error(self):
        with pytest.raises(DataWizardError):
            raise TrainingError("t error")


class TestLLMError:
    def test_is_subclass(self):
        e = LLMError("llm unavailable")
        assert isinstance(e, DataWizardError)

    def test_to_dict_error_type(self):
        e = LLMError("timeout")
        assert e.to_dict()["error_type"] == "LLMError"

    def test_with_provider_details(self):
        e = LLMError("key missing", details={"provider": "groq", "env_key": "GROQ_API_KEY"})
        assert e.details["provider"] == "groq"

    def test_caught_as_data_wizard_error(self):
        with pytest.raises(DataWizardError):
            raise LLMError("l error")


class TestInvalidFileError:
    def test_is_subclass(self):
        e = InvalidFileError("bad file")
        assert isinstance(e, DataWizardError)

    def test_to_dict_error_type(self):
        e = InvalidFileError("not a csv")
        assert e.to_dict()["error_type"] == "InvalidFileError"

    def test_caught_as_data_wizard_error(self):
        with pytest.raises(DataWizardError):
            raise InvalidFileError("f error")


class TestErrorHierarchy:
    def test_each_subclass_is_not_sibling(self):
        assert not isinstance(ValidationError("x"), TrainingError)
        assert not isinstance(TrainingError("x"), LLMError)
        assert not isinstance(LLMError("x"), PreprocessingError)

    def test_all_are_data_wizard_errors(self):
        errors = [
            InvalidFileError("a"),
            ValidationError("b"),
            PreprocessingError("c"),
            TrainingError("d"),
            LLMError("e"),
        ]
        for e in errors:
            assert isinstance(e, DataWizardError)
