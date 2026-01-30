"""
Tests for the High School Management System API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Save original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student(self, client):
        """Test signing up a new student for an activity"""
        activity_name = "Basketball Team"
        email = "test_student@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_duplicate_student(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        activity_name = "Tennis Club"
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signing up with special characters in email"""
        from urllib.parse import quote
        
        activity_name = "Digital Art"
        email = "student+test@mergington.edu"
        
        response = client.post(
            f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_student(self, client):
        """Test unregistering an existing student from an activity"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Pre-existing participant
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_unregister_nonexistent_student(self, client):
        """Test unregistering a student who is not signed up"""
        activity_name = "Science Club"
        email = "notregistered@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow of signing up and then unregistering"""
        activity_name = "Theater Club"
        email = "workflow_test@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response2 = client.get("/activities")
        activities_data2 = activities_response2.json()
        assert email not in activities_data2[activity_name]["participants"]


class TestActivityConstraints:
    """Tests for activity constraints and edge cases"""
    
    def test_multiple_students_can_signup(self, client):
        """Test that multiple students can sign up for the same activity"""
        activity_name = "Debate Team"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for email in emails:
            assert email in activities_data[activity_name]["participants"]
    
    def test_student_can_signup_for_multiple_activities(self, client):
        """Test that a student can sign up for different activities"""
        email = "multi_activity@mergington.edu"
        activities_list = ["Science Club", "Digital Art", "Chess Club"]
        
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for activity_name in activities_list:
            assert email in activities_data[activity_name]["participants"]
