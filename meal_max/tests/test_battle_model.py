import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

### Fixtures ###

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
    return mocker.patch("meal_max.utils.random_utils.get_random", return_value=0.5)

@pytest.fixture
def mock_db_connection(mocker):
    """Mock the database connection to avoid real database interactions."""
    mock_conn = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default behavior for SELECT queries
    mocker.patch("meal_max.utils.sql_utils.get_db_connection", return_value=mock_conn)
    return mock_cursor


####################
# Clear Combatants
###################

def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
     """Test clearing the combatants list."""
     battle_model.prep_combatant(sample_meal1)
     battle_model.prep_combatant(sample_meal2)
     assert len(battle_model.get_combatants()) == 2, "Two combatants should be present before clearing."
     battle_model.clear_combatants()
     assert len(battle_model.get_combatants()) == 0, "Combatants list should be empty after clearing."

def test_clear_combatants_one(battle_model, sample_meal1):
    """Test clearing the combatants list with only one combatant."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1, "One combatant should be present before clearing."
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0, "Combatants list should be empty after clearing."

def test_get_battle_score(battle_model, sample_meal1):
    """Test battle score calculation for a combatant."""
    score = battle_model.get_battle_score(sample_meal1)
    difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}
    assert score == (sample_meal1.price * len(sample_meal1.cuisine)) - difficulty_modifier[sample_meal1.difficulty], "Battle score should be calculated correctly."

def test_get_battle_score2(battle_model, sample_meal2):
    """Test battle score calculation for a second combatant."""
    score = battle_model.get_battle_score(sample_meal2)
    difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}
    assert score == (sample_meal2.price * len(sample_meal2.cuisine)) - difficulty_modifier[sample_meal2.difficulty], "Battle score should be calculated correctly."

def test_get_combatants_non_empty(battle_model, sample_meal1, sample_meal2):
    """Test that get_combatants returns the correct list of combatants when added."""
    # Add sample meals to the combatants list
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Retrieve combatants and verify they match the added meals
    combatants = battle_model.get_combatants()
    assert combatants == [sample_meal1, sample_meal2], "Combatants list should match the added meals."
    assert len(combatants) == 2, "Combatants list should contain two meals after adding them."

def test_get_combatants_empty(battle_model):
    """Test that get_combatants returns an empty list when no combatants are added."""
    combatants = battle_model.get_combatants()
    assert combatants == [], "Combatants list should be empty initially."

def test_prep_combatant_no_combatants(battle_model):
    """Test that ValueError is raised when no combatants are added."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_prep_combatant_one_combatant(battle_model, sample_meal1):
    """Test adding a combatant to an initially empty list."""
    battle_model.prep_combatant(sample_meal1)
    assert battle_model.get_combatants() == [sample_meal1], "Expected combatants list to contain the first added meal."

def test_prep_combatant_two_combatants(battle_model, sample_meal1, sample_meal2):
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

####################
# Battle
###################

def test_battle_no_combatants(battle_model):
    """Test that ValueError is raised when there are no combatants."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()


def test_battle_one_combatant(battle_model, sample_meal1):
    """Test that ValueError is raised when there is only one combatant."""
    battle_model.prep_combatant(sample_meal1)

    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_two_combatants(battle_model, sample_meal1, sample_meal2, mocker):
    """Test that battle returns the correct winner and updates stats."""

    # Mock `get_random` to return a consistent value
    mock_random = mocker.patch("music_collection.models.song_model.get_random", return_value=0.5)

    # Mock `update_meal_stats` to track calls
    mock_update_meal_stats = mocker.patch("meal_max.models.kitchen_model.update_meal_stats")

    # Prepare combatants
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Conduct the battle
    winner = battle_model.battle()

    # Assertions
    assert winner == sample_meal2.meal, "Expected second combatant to win based on mocked random value."

    # Ensure `update_meal_stats` was called for both combatants with correct statuses
    mock_update_meal_stats.assert_any_call(sample_meal1.id, "loss")
    mock_update_meal_stats.assert_any_call(sample_meal2.id, "win")
    assert mock_update_meal_stats.call_count == 2, "Expected two calls to update_meal_stats."

    # Validate that the correct combatant remains in the list
    assert sample_meal1 not in battle_model.get_combatants(), "Losing combatant should be removed."
    assert sample_meal2 in battle_model.get_combatants(), "Winning combatant should remain."
