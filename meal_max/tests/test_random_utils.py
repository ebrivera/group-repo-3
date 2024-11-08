import pytest
import requests

from meal_max.utils.logger import configure_logger
from meal_max.utils.random_utils import get_random

RANDOM_NUMBER_DECIMAL = 0.42

@pytest.fixture
def mock_random_org_decimal(mocker):
    """Mock a successful request to random.org for a decimal number."""
    mock_response = mocker.Mock()
    mock_response.text = f"{RANDOM_NUMBER_DECIMAL}"
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_random_decimal(mock_random_org_decimal):
    """Test retrieving a random decimal number from random.org."""
    result = get_random()
    
    # Assert that the result matches the mocked decimal number
    assert result == RANDOM_NUMBER_DECIMAL, f"Expected random number {RANDOM_NUMBER_DECIMAL}, but got {result}"
    
    # Ensure that the correct URL was called
    requests.get.assert_called_once_with(
        "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new",
        timeout=5
    )

def test_get_random_request_failure(mocker):
    """Simulate a request failure for random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()

def test_get_random_timeout(mocker):
    """Simulate a timeout error when requesting random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()

def test_get_random_invalid_response(mock_random_org_decimal):
    """Simulate an invalid response (non-float) from random.org."""
    mock_random_org_decimal.text = "invalid_response"

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()
