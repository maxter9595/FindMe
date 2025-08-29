# tests/test_user.py
import pytest

from VK.Classes.Criteria import Criteria
from VK.Classes.User import User


class TestUser:
    @pytest.fixture
    def user(self):
        return User(123)

    def test_user_initialization(self, user):
        assert user.get_user_id() == 123
        assert user.get_first_name() == ""
        assert user.get_last_name() == ""
        assert user.get_age() == 0
        assert user.get_gender() == 0
        assert user.get_city() is None
        assert user.get_about_me() == ""

    def test_set_and_get_methods(self, user):
        user.set_first_name("John")
        user.set_last_name("Doe")
        user.set_age(25)
        user.set_gender(1)
        user.set_city({'id': 1, 'name': 'Moscow'})
        user.set_about_me("Test user")

        assert user.get_first_name() == "John"
        assert user.get_last_name() == "Doe"
        assert user.get_age() == 25
        assert user.get_gender() == 1
        assert user.get_city()['name'] == 'Moscow'
        assert user.get_about_me() == "Test user"

    def test_get_gender_str(self, user):
        user.set_gender(1)
        
        assert user.get_gender_str() == 'Женщина'
        
        user.set_gender(2)
        assert user.get_gender_str() == 'Мужчина'

    def test_criteria_management(self, user):
        criteria = Criteria()
        criteria.gender_id = 1
        
        user.set_criteria(criteria)
        
        assert user.get_criteria() is not None
        assert user.get_criteria().gender_id == 1

    def test_to_dict(self, user):
        # Arrange
        user.set_first_name("John")
        user.set_last_name("Doe")
        user.set_age(25)
        user.set_gender(1)
        user.set_city({'id': 1, 'title': 'Moscow'})
        user.set_about_me("Test")
        
        result = user.to_dict()
        
        assert result['first_name'] == "John"
        assert result['last_name'] == "Doe"
        assert result['age'] == 25
        assert result['gender'] == 1
