import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal
from meal_max.utils.random_utils import get_random


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
    return Meal(id=1, meal="Pizza", cuisine="Italian", price=10.0, difficulty="MED")

@pytest.fixture
def sample_meal2():
    """Fixture to provide a second sample meal object."""
    return Meal(id=2, meal="Burger", cuisine="American", price=8.0, difficulty="LOW")

@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    """Fixture to provide a sample battle setup."""
    return [sample_meal1, sample_meal2]

@pytest.fixture
def mock_random(mocker):
    """Fixture to mock get_random with a consistent value."""
    return mocker.patch("meal_max.models.battle_model.get_random")


def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
     """Test clearing the combatants list."""
     battle_model.prep_combatant(sample_meal1)
     battle_model.prep_combatant(sample_meal2)
     assert len(battle_model.get_combatants()) == 2, "Two combatants should be present before clearing."
     battle_model.clear_combatants()
     assert len(battle_model.get_combatants()) == 0, "Combatants list should be empty after clearing."



#Unit tests for battle
def test_battle(battle_model, sample_battle, mocker):
    """Test the battle method for correct winner determination."""
    # Mock the update_meal_stats function
    mock_update_meal_stats = mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

    # Set up combatants
    battle_model.combatants.extend(sample_battle["meals"])

    # Run the battle and get the winner
    winner_meal = battle_model.battle()

    # Check if the correct winner was returned
    assert winner_meal == sample_battle["winner"].meal, "Winner should be determined correctly."

    # Verify that update_meal_stats was called with the winner and loser
    mock_update_meal_stats.assert_any_call(sample_battle["winner"].id, 'win')
    mock_update_meal_stats.assert_any_call(sample_battle["loser"].id, 'loss')

    # Check if the loser was removed from combatants
    assert len(battle_model.get_combatants()) == 1, "Loser should have been removed from combatants list."



def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
    """Test clearing the combatants list."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    assert len(battle_model.get_combatants()) == 2, "Two combatants should be present before clearing."
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0, "Combatants list should be empty after clearing."

def test_battle_zero_combatants(battle_model):
    """Test that ValueError is raised when not enough combatants are available."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()


def test_battle_with_one_combatant(battle_model, sample_meal1):
    """Test that battle raises a ValueError when there is only one combatant."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()


def test_get_battle_score(battle_model,sample_meal1, mocker):
    """Test that get_battle_score returns a consistent score."""
    # Mock the random utility function to return a fixed value
    mocker.patch("meal_max.utils.random_utils.get_random", return_value=10)

    # Call the function and verify the result
    score = battle_model.get_battle_score(sample_meal1)
    assert score == 50.0, "Expected battle score to be 50.0 for the sample meal."



# unit test for prep_combatants
def test_prep_combatant_empty_list(battle_model):
    """Test that ValueError is raised when no combatants are added."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle() 

def test_prep_combatant_zero_list(battle_model, sample_meal1):
    """Test adding a combatant to an initially empty list."""
    battle_model.prep_combatant(sample_meal1)
    assert battle_model.get_combatants() == [sample_meal1], "Expected combatants list to contain the first added meal."


def test_prep_combatant_second_combatant(battle_model, sample_meal1, sample_meal2):
    """Test adding a second combatant to the list."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    assert battle_model.get_combatants() == [sample_meal1, sample_meal2], "Expected combatants list to contain both meals."

def test_prep_combatant_full_list(battle_model, sample_meal1, sample_meal2):
    """Test that adding a third combatant raises a ValueError."""
    # Prepare two combatants
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    
    # Attempt to add a third combatant, which should raise a ValueError
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal2)

# unit test for get_combatants

def test_get_combatants_empty(battle_model):
    """Test that get_combatants returns an empty list when no combatants are added."""
    # Check that combatants list is initially empty
    combatants = battle_model.get_combatants()
    assert combatants == [], "Combatants list should be empty initially."


def test_get_combatants_non_empty(battle_model, sample_meal1, sample_meal2):
    """Test that get_combatants returns the correct list of combatants when added."""
    # Add sample meals to the combatants list
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Retrieve combatants and verify they match the added meals
    combatants = battle_model.get_combatants()
    assert combatants == [sample_meal1, sample_meal2], "Combatants list should match the added meals."
    assert len(combatants) == 2, "Combatants list should contain two meals after adding them."


