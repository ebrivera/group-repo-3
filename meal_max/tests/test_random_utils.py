import pytest

from meal_max.models.kitchen_model import KitchenModel
from meal_max.models.battle_model import BattleModel

@pytest.fixture
def mock_random():
    return 0.5