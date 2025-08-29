from unittest.mock import MagicMock, patch

import pytest

from CheckDb.structure import Cities
from CheckDb.structure import Criteria as DbCriteria
from CheckDb.structure import Users
from Repository.repository import Repository
from VK.Classes.Criteria import Criteria
from VK.Classes.User import User


class TestRepository:
    @pytest.fixture
    def repository(self):
        return Repository()

    @pytest.fixture
    def test_user(self):
        user = User(123)
        user.set_first_name("Test")
        user.set_last_name("User")
        user.set_age(25)
        user.set_gender(1)
        user.set_city({'id': 1, 'name': 'Moscow'})
        user.set_about_me("Test about me")
        return user

    @patch('Repository.repository.sessionmaker')
    @patch('Repository.repository.create_engine')
    def test_add_user_new_user_new_city(self, mock_create_engine, mock_sessionmaker, repository, test_user):
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        user_query_mock = MagicMock()
        city_query_mock = MagicMock()
        criteria_query_mock = MagicMock()
        
        user_query_mock.filter.return_value.first.return_value = None
        city_query_mock.filter.return_value.first.return_value = None
        criteria_query_mock.filter.return_value.all.return_value = []
        
        mock_session.query.side_effect = [
            user_query_mock,
            city_query_mock,
            criteria_query_mock
        ]

        repository.add_user(test_user)
        
        assert mock_session.add.call_count == 3
        mock_session.commit.assert_called()

    @patch('Repository.repository.sessionmaker')
    @patch('Repository.repository.create_engine')
    def test_add_user_existing_user(self, mock_create_engine, mock_sessionmaker, repository, test_user):
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        existing_user = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_user

        repository.add_user(test_user)

        mock_session.add.assert_not_called()
        mock_session.commit.assert_called()

    @patch('Repository.repository.sessionmaker')
    @patch('Repository.repository.create_engine')
    def test_get_user_exists(self, mock_create_engine, mock_sessionmaker, repository):
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        
        mock_user = MagicMock()
        mock_city = MagicMock()
        mock_user.id = 123
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.age = 25
        mock_user.gender_id = 1
        mock_user.about_me = "Test about me"
        mock_city.id = 1
        mock_city.name = "Moscow"
        
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (mock_user, mock_city)
        ]

        with patch.object(repository, 'open_criteria') as mock_open_criteria:
            mock_criteria = Criteria()
            mock_open_criteria.return_value = mock_criteria

            result = repository.get_user(123)

            assert result is not None
            assert result.get_user_id() == 123
            assert result.get_first_name() == "Test"

    @patch('Repository.repository.sessionmaker')
    @patch('Repository.repository.create_engine')
    def test_get_user_not_exists(self, mock_create_engine, mock_sessionmaker, repository):
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session
        mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = repository.get_user(999)

        assert result is None
