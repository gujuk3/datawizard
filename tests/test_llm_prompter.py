import os
import pytest
from unittest.mock import patch, MagicMock
import requests

from datawizard_core.llm_prompter import (
    build_upload_insights_prompt,
    build_statistics_prompt,
    build_model_results_prompt,
    parse_llm_response,
    call_llm_api,
    call_groq,
    call_local_llm,
    call_llm,
    _parse_api_response,
)
from datawizard_core.exceptions import LLMError


# ── Prompt builders ────────────────────────────────────────────────────────────

class TestBuildUploadInsightsPrompt:
    def test_returns_string(self):
        summary = {"file_name": "data.csv", "row_count": 100, "column_count": 5,
                   "missing_pct": 2.5, "duplicate_row_count": 0}
        result = build_upload_insights_prompt(summary, ["age", "salary"], ["city"])
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_column_names(self):
        summary = {"file_name": "test.csv", "row_count": 10, "column_count": 2,
                   "missing_pct": 0, "duplicate_row_count": 0}
        result = build_upload_insights_prompt(summary, ["price"], ["category"])
        assert "price" in result
        assert "category" in result

    def test_handles_empty_column_lists(self):
        summary = {"file_name": "x.csv", "row_count": 5, "column_count": 1,
                   "missing_pct": 0, "duplicate_row_count": 0}
        result = build_upload_insights_prompt(summary, [], [])
        assert isinstance(result, str)


class TestBuildStatisticsPrompt:
    def _stats(self):
        return {
            "numeric": {
                "age": {"mean": 29.5, "median": 29.0, "std": 4.1, "min": 25, "max": 35,
                        "q1": 27.0, "q3": 32.0, "skewness": 0.1, "non_null_count": 4},
            },
            "categorical": {
                "city": {"mode": "Istanbul", "unique_count": 3,
                         "top_values": [{"value": "Istanbul", "count": 2}], "non_null_count": 4},
            },
        }

    def _summary(self):
        return {"row_count": 4, "column_count": 3, "numeric_column_count": 2,
                "categorical_column_count": 1, "missing_pct": 0, "duplicate_row_count": 0}

    def test_returns_string(self):
        result = build_statistics_prompt(self._summary(), self._stats())
        assert isinstance(result, str)

    def test_contains_column_names(self):
        result = build_statistics_prompt(self._summary(), self._stats())
        assert "age" in result
        assert "city" in result

    def test_with_correlation_data(self):
        corr = {"columns": ["age", "salary"], "matrix": [[1.0, 0.9], [0.9, 1.0]], "method": "pearson"}
        result = build_statistics_prompt(self._summary(), self._stats(), corr_data=corr)
        assert "age" in result
        assert "salary" in result

    def test_with_single_numeric_no_corr(self):
        # corr_data has only 1 column — corr section skipped
        corr = {"columns": ["age"], "matrix": [[1.0]], "method": "pearson"}
        result = build_statistics_prompt(self._summary(), self._stats(), corr_data=corr)
        assert isinstance(result, str)

    def test_no_numeric_columns(self):
        stats = {"numeric": {}, "categorical": {}}
        result = build_statistics_prompt(self._summary(), stats)
        assert "Sayısal sütun yok" in result


class TestBuildModelResultsPrompt:
    def _clf_metrics(self):
        return {
            "accuracy": 0.92, "precision": 0.91, "recall": 0.90, "f1_score": 0.905,
            "confusion_matrix": [[10, 1], [1, 8]], "class_labels": ["0", "1"],
            "classification_report": {},
        }

    def _reg_metrics(self):
        return {"mse": 0.25, "rmse": 0.5, "r2_score": 0.88,
                "predictions": [1.0, 2.0], "actuals": [1.1, 1.9]}

    def test_classification_returns_string(self):
        result = build_model_results_prompt(self._clf_metrics(), [], "classification", "logistic_regression")
        assert isinstance(result, str)

    def test_regression_returns_string(self):
        result = build_model_results_prompt(self._reg_metrics(), [], "regression", "linear_regression")
        assert isinstance(result, str)
        assert "R²" in result

    def test_with_feature_importance(self):
        fi = [{"feature": "age", "importance": 0.7, "importance_pct": "70.0"},
              {"feature": "salary", "importance": 0.3, "importance_pct": "30.0"}]
        result = build_model_results_prompt(self._clf_metrics(), fi, "classification", "decision_tree")
        assert "age" in result

    def test_with_shap_values(self):
        shap = [{"feature": "age", "shap_value": 0.5, "shap_pct": "60.0"}]
        result = build_model_results_prompt(
            self._clf_metrics(), [], "classification", "logistic_regression", shap_values=shap
        )
        assert "age" in result

    def test_confusion_matrix_without_labels(self):
        metrics = self._clf_metrics()
        metrics["class_labels"] = []
        result = build_model_results_prompt(metrics, [], "classification", "knn")
        assert isinstance(result, str)

    def test_unknown_algorithm_uses_raw_name(self):
        result = build_model_results_prompt(self._clf_metrics(), [], "classification", "custom_algo")
        assert "custom_algo" in result


# ── parse_llm_response ─────────────────────────────────────────────────────────

class TestParseLlmResponse:
    def test_empty_string_returns_empty_result(self):
        result = parse_llm_response("")
        assert result["summary"] == ""
        assert result["sections"] == []
        assert result["bullet_points"] == []

    def test_none_like_empty_returns_empty(self):
        result = parse_llm_response("   ")
        assert result["summary"] == ""

    def test_plain_text_becomes_summary(self):
        result = parse_llm_response("This is a plain text response.")
        assert "plain text" in result["summary"]

    def test_hash_sections_parsed(self):
        text = "### Introduction\nSome intro text.\n### Conclusion\nEnding."
        result = parse_llm_response(text)
        assert len(result["sections"]) == 2
        assert result["sections"][0]["title"] == "Introduction"
        assert result["sections"][1]["title"] == "Conclusion"

    def test_bold_headers_parsed(self):
        text = "**Summary**\nContent here.\n**Details**\nMore content."
        result = parse_llm_response(text)
        titles = [s["title"] for s in result["sections"]]
        assert "Summary" in titles

    def test_bullet_points_extracted(self):
        text = "### Section\n- First point\n- Second point\n• Third point"
        result = parse_llm_response(text)
        assert len(result["bullet_points"]) >= 3

    def test_numbered_items_extracted(self):
        text = "1. First item\n2. Second item"
        result = parse_llm_response(text)
        assert len(result["bullet_points"]) >= 2

    def test_raw_text_preserved(self):
        text = "### Header\nContent"
        result = parse_llm_response(text)
        assert result["raw_text"] == text

    def test_pre_section_text_is_summary(self):
        text = "Introduction paragraph.\n### Section\nContent."
        result = parse_llm_response(text)
        assert "Introduction" in result["summary"]


# ── call_llm_api ───────────────────────────────────────────────────────────────

class TestCallLlmApi:
    def test_invalid_provider_raises(self):
        with pytest.raises(LLMError, match="Invalid provider"):
            call_llm_api("prompt", provider="badprovider")

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMError, match="API key not found"):
                call_llm_api("prompt", provider="openai")

    def test_openai_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), \
             patch("datawizard_core.llm_prompter.requests.post", return_value=mock_response):
            result = call_llm_api("test prompt", provider="openai")
        assert result["text"] == "Hello!"
        assert result["provider"] == "openai"

    def test_anthropic_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Anthropic response"}],
            "usage": {"input_tokens": 5, "output_tokens": 8},
        }
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}), \
             patch("datawizard_core.llm_prompter.requests.post", return_value=mock_response):
            result = call_llm_api("test prompt", provider="anthropic")
        assert result["text"] == "Anthropic response"

    def test_client_error_raises(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "bad-key"}), \
             patch("datawizard_core.llm_prompter.requests.post", return_value=mock_response):
            with pytest.raises(LLMError):
                call_llm_api("prompt", provider="openai")

    def test_connection_error_raises_after_retries(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}), \
             patch("datawizard_core.llm_prompter.requests.post",
                   side_effect=requests.exceptions.ConnectionError("unreachable")), \
             patch("datawizard_core.llm_prompter.time.sleep"):
            with pytest.raises(LLMError):
                call_llm_api("prompt", provider="openai")

    def test_timeout_raises_after_retries(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}), \
             patch("datawizard_core.llm_prompter.requests.post",
                   side_effect=requests.exceptions.Timeout()), \
             patch("datawizard_core.llm_prompter.time.sleep"):
            with pytest.raises(LLMError):
                call_llm_api("prompt", provider="openai")


# ── _parse_api_response ────────────────────────────────────────────────────────

class TestParseApiResponse:
    def test_openai_format(self):
        response = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        }
        result = _parse_api_response(response, "openai", "gpt-4o-mini")
        assert result["text"] == "Hello"
        assert result["usage"]["prompt_tokens"] == 5

    def test_anthropic_format(self):
        response = {
            "content": [{"type": "text", "text": "Hi there"}],
            "usage": {"input_tokens": 4, "output_tokens": 2},
        }
        result = _parse_api_response(response, "anthropic", "claude-3")
        assert result["text"] == "Hi there"

    def test_malformed_response_raises(self):
        with pytest.raises(LLMError):
            _parse_api_response({"no_choices": []}, "openai", "gpt-4o-mini")

    def test_unknown_provider_fallback(self):
        result = _parse_api_response({"some": "data"}, "other", "model-x")
        assert "text" in result


# ── call_groq ──────────────────────────────────────────────────────────────────

class TestCallGroq:
    def test_missing_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMError, match="GROQ_API_KEY"):
                call_groq("prompt")

    def test_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Groq reply"}}]
        }
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}), \
             patch("datawizard_core.llm_prompter.requests.post", return_value=mock_response):
            result = call_groq("hello")
        assert result == "Groq reply"

    def test_http_error_propagates(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        with patch.dict(os.environ, {"GROQ_API_KEY": "key"}), \
             patch("datawizard_core.llm_prompter.requests.post", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                call_groq("prompt")


# ── call_local_llm ─────────────────────────────────────────────────────────────

class TestCallLocalLlm:
    def test_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Local reply"}}]
        }
        with patch("datawizard_core.llm_prompter.requests.post", return_value=mock_response):
            result = call_local_llm("hello")
        assert result == "Local reply"

    def test_connection_error_raises_llm_error(self):
        with patch("datawizard_core.llm_prompter.requests.post",
                   side_effect=requests.exceptions.ConnectionError()):
            with pytest.raises(LLMError, match="not reachable"):
                call_local_llm("prompt")

    def test_generic_exception_raises_llm_error(self):
        with patch("datawizard_core.llm_prompter.requests.post",
                   side_effect=ValueError("bad json")):
            with pytest.raises(LLMError):
                call_local_llm("prompt")


# ── call_llm routing ───────────────────────────────────────────────────────────

class TestCallLlmRouting:
    def test_routes_to_groq_by_default(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "groq"}), \
             patch("datawizard_core.llm_prompter.call_groq", return_value="groq") as mock_groq:
            result = call_llm("p")
        mock_groq.assert_called_once_with("p")
        assert result == "groq"

    def test_routes_to_local_when_set(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "local"}), \
             patch("datawizard_core.llm_prompter.call_local_llm", return_value="local") as mock_local:
            result = call_llm("p")
        mock_local.assert_called_once_with("p")
        assert result == "local"
