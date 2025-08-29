from unittest.mock import MagicMock, patch

import pytest
import requests

from VK.Classes.Criteria import Criteria
from VK.Classes.Result import Result
from VK.Classes.VKService import VKService


class TestVKService:
    @pytest.fixture
    def vk_service(self):
        return VKService()

    @pytest.fixture
    def test_criteria(self):
        criteria = Criteria()
        criteria.gender_id = 1
        criteria.status = 1
        criteria.age_from = 20
        criteria.age_to = 30
        criteria.city = {'id': 1, 'name': 'Moscow'}
        criteria.has_photo = 1
        return criteria

    @patch('VK.Classes.VKService.requests.get')
    def test_get_users_info_success(self, mock_get, vk_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': [{
                'first_name': 'Test',
                'last_name': 'User',
                'sex': 1,
                'city': {'id': 1, 'title': 'Moscow'},
                'bdate': '01.01.1990'
            }]
        }
        mock_get.return_value = mock_response

        result = vk_service.get_users_info('test_token', 123)

        assert result is not None
        assert result['first_name'] == 'Test'

    @patch('VK.Classes.VKService.requests.get')
    def test_get_users_info_failure(self, mock_get, vk_service):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = vk_service.get_users_info('test_token', 123)

        assert result is None

    @patch('VK.Classes.VKService.requests.get')
    def test_users_search_success(self, mock_get, vk_service, test_criteria):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {
                'items': [{
                    'id': 123,
                    'first_name': 'Test',
                    'last_name': 'User',
                    'sex': 1,
                    'city': {'id': 1, 'title': 'Moscow'},
                    'bdate': '01.01.1995'
                }]
            }
        }
        mock_get.return_value = mock_response

        with patch.object(vk_service, 'add_photos') as mock_add_photos:
            mock_add_photos.return_value = MagicMock()

            result = vk_service.users_search(test_criteria, 'test_token')

            assert result is not None
            assert len(result) > 0

    def test_determine_age_valid_date(self, vk_service):
        test_date = "01.01.1990"

        age = vk_service.determine_age(test_date)

        assert isinstance(age, int)
        assert age > 0

    def test_determine_age_invalid_date(self, vk_service):
        test_date = "invalid-date"

        with pytest.raises(ValueError):
            vk_service.determine_age(test_date)
