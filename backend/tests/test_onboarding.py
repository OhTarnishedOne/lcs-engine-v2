"""
Tests for Onboarding endpoints and service.
"""


def test_get_all_questions(client):
    """Test getting all onboarding questions."""
    # Register and get token
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Get questions
    response = client.get(
        "/api/onboarding/questions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert len(data["sections"]) == 5
    assert data["total_questions"] > 0

    # Check first section structure
    section1 = data["sections"][0]
    assert section1["section"] == 1
    assert section1["title"] == "Where You Are"
    assert len(section1["questions"]) == 4


def test_get_single_section(client):
    """Test getting a single section's questions."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    response = client.get(
        "/api/onboarding/questions/2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["section"]["section"] == 2
    assert data["section"]["title"] == "What's Holding You Back"
    assert data["total_sections"] == 5
    assert data["is_last_section"] is False


def test_save_section_responses(client):
    """Test saving responses for a section."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Save section 1 responses
    response = client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "section": 1,
            "responses": {
                "experience_level": "never",
                "current_situation": "early_career",
                "has_investment_account": False,
                "has_retirement_account": False
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["section"] == 1
    assert data["saved_count"] == 4
    assert data["next_section"] == 2
    assert data["is_complete"] is False


def test_save_single_response(client):
    """Test saving a single response."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    response = client.post(
        "/api/onboarding/response",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "experience_level",
            "answer_value": "curious"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question_key"] == "experience_level"
    assert data["saved"] is True


def test_get_progress(client):
    """Test getting onboarding progress."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Initial progress (no responses)
    response = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sections_completed"] == []
    assert data["current_section"] == 1
    assert data["is_complete"] is False

    # Save section 1
    client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "section": 1,
            "responses": {
                "experience_level": "never",
                "current_situation": "early_career",
                "has_investment_account": False,
                "has_retirement_account": False
            }
        }
    )

    # Check updated progress
    response = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert 1 in data["sections_completed"]
    assert data["current_section"] == 2


def test_complete_onboarding_creates_profile(client):
    """Test that completing onboarding creates a profile with persona."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Complete onboarding with all responses
    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                # Section 1
                "experience_level": "never",
                "current_situation": "early_career",
                "has_investment_account": False,
                "has_retirement_account": False,
                # Section 2
                "barriers": ["dont_know_where_to_start", "fear_of_losing_money"],
                "biggest_barrier": "dont_know_where_to_start",
                # Section 3
                "primary_goal": "learn_basics",
                "time_horizon": "3_to_5_years",
                # Section 4
                "risk_tolerance": "conservative",
                "loss_reaction": "wait_and_see",
                "monthly_investable": "under_100",
                # Section 5
                "learning_preference": "do",
                "time_commitment": "15_min_daily",
                "interests": ["stocks", "etfs"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["experience_level"] == "never"
    assert data["risk_tolerance"] == "conservative"
    assert data["onboarding_completed"] is True
    assert data["persona"] is not None
    assert data["persona_description"] is not None


def test_get_profile_after_onboarding(client):
    """Test getting profile after completing onboarding."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Complete onboarding
    client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "beginner",
                "current_situation": "student",
                "has_investment_account": True,
                "has_retirement_account": False,
                "barriers": ["not_enough_money"],
                "primary_goal": "start_investing",
                "time_horizon": "5_to_10_years",
                "risk_tolerance": "moderate",
                "loss_reaction": "wait_and_see",
                "monthly_investable": "100_to_500",
                "learning_preference": "read",
                "time_commitment": "30_min_weekly",
                "interests": ["all"]
            }
        }
    )

    # Get profile
    response = client.get(
        "/api/onboarding/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["raw"]["experience_level"] == "beginner"
    assert data["raw"]["current_situation"] == "student"
    assert data["derived"]["persona"] is not None
    assert data["derived"]["experience_summary"] is not None


def test_personalized_welcome(client):
    """Test welcome message addresses user's barriers."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Complete onboarding with specific barrier
    client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "never",
                "current_situation": "early_career",
                "has_investment_account": False,
                "has_retirement_account": False,
                "barriers": ["fear_of_losing_money"],
                "biggest_barrier": "fear_of_losing_money",
                "primary_goal": "learn_basics",
                "time_horizon": "5_to_10_years",
                "risk_tolerance": "very_conservative",
                "loss_reaction": "sell_immediately",
                "monthly_investable": "nothing_yet",
                "learning_preference": "watch",
                "time_commitment": "5_min_daily",
                "interests": ["retirement"]
            }
        }
    )

    # Get welcome message
    response = client.get(
        "/api/onboarding/welcome",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "greeting" in data
    assert "acknowledgment" in data
    assert "losing money" in data["acknowledgment"]  # Should address their fear
    assert "recommended_action" in data
    assert "personalized_tips" in data


def test_persona_generation_cautious_beginner(client):
    """Test persona generation for beginner with fear barrier."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "never",
                "current_situation": "student",
                "has_investment_account": False,
                "has_retirement_account": False,
                "barriers": ["fear_of_losing_money"],
                "biggest_barrier": "fear_of_losing_money",
                "primary_goal": "learn_basics",
                "time_horizon": "3_to_5_years",
                "risk_tolerance": "very_conservative",
                "loss_reaction": "sell_immediately",
                "monthly_investable": "nothing_yet",
                "learning_preference": "read",
                "time_commitment": "flexible",
                "interests": ["stocks"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["persona"] == "cautious_beginner"
    assert data["recommended_path"] == "start_with_basics"


def test_persona_generation_eager_learner(client):
    """Test persona generation for curious learner with moderate risk."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "beginner",
                "current_situation": "early_career",
                "has_investment_account": True,
                "has_retirement_account": True,
                "barriers": ["none"],
                "primary_goal": "learn_basics",
                "time_horizon": "3_to_5_years",
                "risk_tolerance": "moderate",
                "loss_reaction": "wait_and_see",
                "monthly_investable": "100_to_500",
                "learning_preference": "do",
                "time_commitment": "1_hour_weekly",
                "interests": ["all"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["persona"] == "eager_learner"
    assert data["recommended_path"] == "accelerated_learning"


def test_persona_generation_wealth_builder(client):
    """Test persona generation for growth-oriented aggressive investor."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "beginner",
                "current_situation": "early_career",
                "has_investment_account": True,
                "has_retirement_account": True,
                "barriers": ["none"],
                "primary_goal": "grow_wealth",
                "time_horizon": "10_plus_years",
                "risk_tolerance": "aggressive",
                "loss_reaction": "buy_more",
                "monthly_investable": "500_to_1000",
                "learning_preference": "do",
                "time_commitment": "1_hour_weekly",
                "interests": ["all"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["persona"] == "wealth_builder"
    assert data["recommended_path"] == "investment_strategies"


def test_persona_generation_income_seeker(client):
    """Test persona generation for conservative retirement-focused user."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "intermediate",
                "current_situation": "mid_career",
                "has_investment_account": True,
                "has_retirement_account": True,
                "barriers": ["none"],
                "primary_goal": "retirement",
                "time_horizon": "10_plus_years",
                "risk_tolerance": "moderate",
                "loss_reaction": "wait_and_see",
                "monthly_investable": "500_to_1000",
                "learning_preference": "read",
                "time_commitment": "30_min_weekly",
                "interests": ["retirement", "bonds"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["persona"] == "income_seeker"
    assert data["recommended_path"] == "retirement_planning"


def test_onboarding_progress_after_complete(client):
    """Test progress shows 100% after completing."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Complete onboarding
    client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "never",
                "current_situation": "student",
                "has_investment_account": False,
                "has_retirement_account": False,
                "barriers": ["dont_know_where_to_start"],
                "primary_goal": "learn_basics",
                "time_horizon": "not_sure",
                "risk_tolerance": "moderate",
                "loss_reaction": "not_sure",
                "monthly_investable": "not_sure",
                "learning_preference": "discuss",
                "time_commitment": "flexible",
                "interests": ["stocks"]
            }
        }
    )

    # Check progress
    response = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["percent_complete"] == 100
    assert data["is_complete"] is True
    assert data["current_section"] is None


def test_conditional_questions(client):
    """Test that conditional questions work correctly."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # With barriers selected (not "none"), biggest_barrier should be saved
    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "experience_level": "curious",
                "current_situation": "mid_career",
                "has_investment_account": False,
                "has_retirement_account": True,
                "barriers": ["too_complicated", "no_time"],
                "biggest_barrier": "too_complicated",
                "primary_goal": "retirement",
                "time_horizon": "10_plus_years",
                "risk_tolerance": "moderate",
                "loss_reaction": "wait_and_see",
                "monthly_investable": "100_to_500",
                "learning_preference": "watch",
                "time_commitment": "30_min_weekly",
                "interests": ["retirement", "bonds"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["barriers"] == ["too_complicated", "no_time"]
    assert data["biggest_barrier"] == "too_complicated"


def test_update_response_overwrites(client):
    """Test that saving the same question overwrites previous response."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Save initial response
    client.post(
        "/api/onboarding/response",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "experience_level",
            "answer_value": "never"
        }
    )

    # Update response
    client.post(
        "/api/onboarding/response",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "experience_level",
            "answer_value": "beginner"
        }
    )

    # Complete with rest of responses
    response = client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "responses": {
                "current_situation": "early_career",
                "has_investment_account": True,
                "has_retirement_account": False,
                "barriers": ["none"],
                "primary_goal": "grow_wealth",
                "time_horizon": "5_to_10_years",
                "risk_tolerance": "moderate",
                "loss_reaction": "wait_and_see",
                "monthly_investable": "100_to_500",
                "learning_preference": "do",
                "time_commitment": "15_min_daily",
                "interests": ["stocks", "etfs"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should have the updated value
    assert data["experience_level"] == "beginner"
