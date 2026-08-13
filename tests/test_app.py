"""
Comprehensive tests for the FastAPI activities management application.
Uses the Arrange-Act-Assert (AAA) pattern for test organization:
- Arrange: Set up test data and preconditions
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest


class TestRootEndpoint:
    """Tests for the GET / endpoint."""
    
    def test_root_returns_redirect_to_static_index(self, client):
        """
        Arrange: N/A (simple GET request, no data setup needed)
        Act: Make a GET request to the root endpoint
        Assert: Verify redirect status and location
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code in [307, 308]  # Temporary or permanent redirect
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: N/A (activities are predefined in app)
        Act: Make a GET request to /activities
        Assert: Verify response contains all activities
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a dict with activities
        assert isinstance(data, dict)
        assert len(data) > 0
        # Verify some known activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_has_correct_structure(self, client):
        """
        Arrange: N/A
        Act: Make a GET request to /activities
        Assert: Verify each activity has required fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_details, dict)
            
            # Verify required fields exist
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            
            # Verify field types
            assert isinstance(activity_details["description"], str)
            assert isinstance(activity_details["schedule"], str)
            assert isinstance(activity_details["max_participants"], int)
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_participant_counts_are_correct(self, client):
        """
        Arrange: N/A
        Act: Make a GET request to /activities
        Assert: Verify participant counts match list lengths
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            participants = activity_details["participants"]
            max_participants = activity_details["max_participants"]
            
            # Participants should not exceed max
            assert len(participants) <= max_participants
            # All participants should be strings (emails)
            assert all(isinstance(p, str) for p in participants)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success_adds_participant(self, client):
        """
        Arrange: Prepare a new email and existing activity
        Act: POST signup request with valid data
        Assert: Verify participant is added and response is correct
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]
        
        # Verify participant was actually added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert new_email in activities_data[activity_name]["participants"]
    
    def test_signup_fails_with_nonexistent_activity(self, client):
        """
        Arrange: Prepare email and non-existent activity name
        Act: POST signup request with invalid activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_fails_with_duplicate_email(self, client):
        """
        Arrange: Use an email already signed up for an activity
        Act: POST signup request with duplicate email
        Assert: Verify 400 error is returned (validates duplicate prevention bug fix)
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_fails_with_missing_email_parameter(self, client):
        """
        Arrange: Prepare activity name but no email
        Act: POST signup request without email parameter
        Assert: Verify validation error is returned
        """
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup")
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity (validation error)
    
    def test_signup_allows_different_students_in_same_activity(self, client):
        """
        Arrange: Add multiple different students to same activity
        Act: POST signup for two different emails
        Assert: Both signups succeed
        """
        # Arrange
        activity_name = "Tennis Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success_removes_participant(self, client):
        """
        Arrange: Use an existing participant email
        Act: DELETE unregister request with valid data
        Assert: Verify participant is removed and response is correct
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"  # Already in Chess Club
        
        # Verify participant exists before unregister
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email_to_remove in activities_data[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email_to_remove in data["message"]
        
        # Verify participant was actually removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email_to_remove not in activities_data[activity_name]["participants"]
    
    def test_unregister_fails_with_nonexistent_activity(self, client):
        """
        Arrange: Prepare email and non-existent activity name
        Act: DELETE unregister request with invalid activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_fails_with_email_not_in_activity(self, client):
        """
        Arrange: Use an email not signed up for the activity
        Act: DELETE unregister request with non-participant email
        Assert: Verify 400 error is returned
        """
        # Arrange
        activity_name = "Chess Club"
        email_not_in_activity = "notinactivity@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_not_in_activity}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_fails_with_missing_email_parameter(self, client):
        """
        Arrange: Prepare activity name but no email
        Act: DELETE unregister request without email parameter
        Assert: Verify validation error is returned
        """
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister")
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity (validation error)
    
    def test_unregister_success_multiple_participants(self, client):
        """
        Arrange: Activity with multiple participants, remove one
        Act: DELETE unregister request for one participant
        Assert: Other participants remain, only target is removed
        """
        # Arrange
        activity_name = "Programming Class"
        email_to_remove = "emma@mergington.edu"
        other_email = "sophia@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify correct participant removed, other remains
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data[activity_name]["participants"]
        assert email_to_remove not in participants
        assert other_email in participants
    
    def test_unregister_then_signup_again_succeeds(self, client):
        """
        Arrange: Unregister a participant, then try to sign up again
        Act: DELETE unregister, then POST signup with same email
        Assert: Both operations succeed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Act - Signup again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        
        # Verify participant is in the list again
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
