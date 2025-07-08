"""Tests for the FastAPI endpoints."""

from unittest.mock import patch
import pytest

import api


def test_analyze_endpoint_authorized():
    with patch("api.analyze_full_site") as mock_analyze, patch("api.plot_results") as mock_plot:
        mock_analyze.return_value = (10, {"Email Capture": 50}, 1)
        result = api.analyze(url="https://example.com", key="secret")
        assert result["total_score"] == 10
        assert "result_file" in result
        mock_plot.assert_called_once()


def test_analyze_endpoint_unauthorized():
    with pytest.raises(Exception):
        api.verify_key()

