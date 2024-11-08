import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import KitchenModel

@pytest.fixture
def battle_model():
    """Fixture to provide a new instance of Battle_Model for each test."""
    return BattleModel()

@pytest.fixture
def mock_update_meal_stats(mocker):
    """Fixture to mock the update_meal_stats function."""
    return mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

""" Fixtures providing sample meals for testing. """
@pytest.fixture
def sample_meal_1():
    return KitchenModel().add_meal("Spaghetti", 100, 20, 10)

@pytest.fixture
def sample_meal_2():
    return KitchenModel().add_meal("Pizza", 200, 30, 15)

@pytest.fixture
