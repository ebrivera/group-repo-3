from contextlib import contextmanager
import re
import sqlite3
import pytest


from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

###############
# Fixtures
###############

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()


# mock db connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    @contextmanager
    def mock_get_db_connection():
        yield mock_conn 

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor

###############
# Add and delete
###############

# Test create_meal

def test_create_meal(mock_cursor):
    """ Testing the creation of a meal in the table"""

    # call function
    create_meal(meal="Pizza", cuisine="Italian", price=10.0, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Pizza", "Italian", 10.0, "MED")

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate name (should raise an error)."""
    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Pizza' already exists"):
        create_meal(meal="Pizza", cuisine="Italian", price=10.0, difficulty="MED")

def test_create_meal_invalid_price():
    """Test creating a meal with an invalid price (should raise an error)."""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -10.0. Price must be a positive number."):
        create_meal(meal="Pizza", cuisine="Italian", price=-10.0, difficulty="MED")
    
    # Attempt to create a meal with a price of 0
    with pytest.raises(ValueError, match="Invalid price: 0. Price must be a positive number."):
        create_meal(meal="Pizza", cuisine="Italian", price=0, difficulty="MED")
    
    # Attempt to create a meal with a non-numeric price
    with pytest.raises(ValueError, match="Invalid price: invalid. Price must be a positive number."):
        create_meal(meal="Pizza", cuisine="Italian", price="invalid", difficulty="MED")
    
    # Attempt to create a meal with a price of None
    with pytest.raises(ValueError, match="Invalid price: None. Price must be a positive number."):
        create_meal(meal="Pizza", cuisine="Italian", price=None, difficulty="MED")

def test_create_meal_invalid_difficulty():
    """Test creating a meal with an invalid difficulty (should raise an error)."""

    # Attempt to create a meal with a difficulty that is not in the allowed list
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pizza", cuisine="Italian", price=10.0, difficulty="EASY")

    # Attempt to create a meal with an empty string for difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: . Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pizza", cuisine="Italian", price=10.0, difficulty="")

    # Attempt to create a meal with a difficulty as None
    with pytest.raises(ValueError, match="Invalid difficulty level: None. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pizza", cuisine="Italian", price=10.0, difficulty=None)

    # Attempt to create a meal with a numerical difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: 5. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pizza", cuisine="Italian", price=10.0, difficulty=5)

def test_clear_meals(mock_cursor, mocker):
    """Testing the clearing of all meals from the table"""
    
    # mocking the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_meals function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


def test_delete_meal(mock_cursor): 
    """Test soft deleting a meal from the database by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."


def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)


def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

###############
# Get by id and name
###############


def test_get_meal_by_id(mock_cursor):
    """Test getting a meal by ID from the database."""
    # Simulate that the meal exists in the database
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "MED", False)

    # Call the get_meal_by_id function
    result = get_meal_by_id(1)

    # Expected result
    expected_result = Meal(id=1, meal="Pizza", cuisine="Italian", price=10.0, difficulty="MED")
    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"


    # Ensure the correct SQL query was executed
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."
    

def test_get_meal_by_id_not_found(mock_cursor):
    """Test ValueError when trying to get a meal by ID that doesn't exist."""
    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to get a non-existent meal by ID
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted(mock_cursor):
    """Test ValueError when trying to get a meal by ID that's marked as deleted."""
    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "MED", True)

    # Expect a ValueError when attempting to get a meal that's marked as deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)


def test_get_meal_by_name(mock_cursor):
    """Test getting a meal by name from the database."""
    # Simulate that the meal exists in the database
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "MED", False)

    # Call the get_meal_by_name function
    result = get_meal_by_name("Pizza")

    # Expected result
    expected_result = Meal(id=1, meal="Pizza", cuisine="Italian", price=10.0, difficulty="MED")
    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"


    # Ensure the correct SQL query was executed
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Pizza",)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_name_not_found(mock_cursor):
    """Test ValueError when trying to get a meal by name that doesn't exist."""
    # Simulate that no meal exists with the given name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to get a non-existent meal by name
    with pytest.raises(ValueError, match="Meal with name Pizza not found"):
        get_meal_by_name("Pizza")

def test_get_meal_by_name_deleted(mock_cursor):
    """Test ValueError when trying to get a meal by name that's marked as deleted."""
    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "MED", True)

    # Expect a ValueError when attempting to get a meal that's marked as deleted
    with pytest.raises(ValueError, match="Meal with name Pizza has been deleted"):
        get_meal_by_name("Pizza")

def test_get_leaderboard(mock_cursor):
    """Test getting the leaderboard from the database."""
    
    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Pizza", "Italian", 10.0, "MED", 5, 3, 0.6),
        (2, "Burger", "American", 8.0, "LOW", 4, 2, 0.5),
        (3, "Sushi", "Japanese", 15.0, "HIGH", 6, 4, 0.6667)
    ]

    # Call the get_leaderboard function
    result = get_leaderboard()

    # Expected result
    expected_result = [
        {"id": 1, "meal": "Pizza", "cuisine": "Italian", "price": 10.0, "difficulty": "MED", "battles": 5, "wins": 3, "win_pct": 60.0},
        {"id": 2, "meal": "Burger", "cuisine": "American", "price": 8.0, "difficulty": "LOW", "battles": 4, "wins": 2, "win_pct": 50.0},
        {"id": 3, "meal": "Sushi", "cuisine": "Japanese", "price": 15.0, "difficulty": "HIGH", "battles": 6, "wins": 4, "win_pct": 66.7},
    ]

    assert result == expected_result, f"Expected {expected_result}, but got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_no_meals(mock_cursor):
    """Test getting the leaderboard when there are no meals in the database."""
    # Simulate that there are no meals in the database
    mock_cursor.fetchall.return_value = []

    # Call the get_leaderboard function
    result = get_leaderboard()

    # Expected result should be an empty list
    expected_result = []
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."


def test_get_leaderboard_sort_by_win_pct(mock_cursor):
    """Test getting the leaderboard sorted by win percentage."""
    # Simulate meals in the database sorted by win percentage (DESC)
    mock_cursor.fetchall.return_value = [
        (3, "Sushi", "Japanese", 15.0, "HIGH", 6, 5, 0.8333),  # Highest win percentage
        (1, "Pizza", "Italian", 10.0, "MED", 5, 3, 0.6),       # Middle win percentage
        (2, "Burger", "American", 8.0, "LOW", 4, 2, 0.5)       # Lowest win percentage
    ]

    # Call the get_leaderboard function with sort_by="win_pct"
    result = get_leaderboard(sort_by="win_pct")

    # Expected result
    expected_result = [
        {"id": 3, "meal": "Sushi", "cuisine": "Japanese", "price": 15.0, "difficulty": "HIGH", "battles": 6, "wins": 5, "win_pct": 83.3},
        {"id": 1, "meal": "Pizza", "cuisine": "Italian", "price": 10.0, "difficulty": "MED", "battles": 5, "wins": 3, "win_pct": 60.0},
        {"id": 2, "meal": "Burger", "cuisine": "American", "price": 8.0, "difficulty": "LOW", "battles": 4, "wins": 2, "win_pct": 50.0}
    ]

    # Assert the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, but got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."


def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test handling of an invalid sort_by parameter."""
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
        get_leaderboard(sort_by="invalid_sort")


###############
# Update stats
###############

def test_update_meal_stats_win(mock_cursor):
    """Test updating the stats of a meal in the database."""
    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal function with a sample song ID
    meal_id = 1
    update_meal_stats(meal_id, "win")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")
    
    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    # Assert that the SQL query was executed with the correct arguments (song ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_update_meal_stats_no_win(mock_cursor):
    """Test updating the stats of a meal in the database."""
    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal function with a sample song ID
    meal_id = 1
    update_meal_stats(meal_id, "loss")

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1 WHERE id = ?")
    
    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    # Assert that the SQL query was executed with the correct arguments (song ID)
    expected_arguments = (meal_id,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_invalid_id(mock_cursor):
    """Test ValueError when trying to update stats for a meal that doesn't exist."""
    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to update stats for a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")

def test_update_meal_stats_deleted(mock_cursor):
    """Test ValueError when trying to update stats for a meal that's marked as deleted."""
    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to update a deleted song
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")
