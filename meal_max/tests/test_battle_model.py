import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats function for testing purposes."""
    return mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

@pytest.fixture
def sample_meal1():
    """Fixture to provide a sample meal object."""
    return Meal(id=1, meal="Pizza", cuisine="Italian", price=10.0, difficulty="MED", battles=5, wins=3)

@pytest.fixture
def sample_meal2():
    """Fixture to provide a second sample meal object."""
    return Meal(id=2, meal="Burger", cuisine="American", price=8.0, difficulty="LOW", battles=4, wins=2)

@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    """Fixture to provide a sample battle setup."""
    return {"meals": [sample_meal1, sample_meal2], "winner": sample_meal1, "loser": sample_meal2}
