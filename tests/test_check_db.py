from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sq

from CheckDb.Classes.CheckDb import CheckDb
from CheckDb.structure import Base


class TestCheckDb:
    @pytest.fixture
    def check_db(self):
        return CheckDb()

    @patch('CheckDb.Classes.CheckDb.create_engine')
    @patch('CheckDb.Classes.CheckDb.database_exists')
    def test_exists_db_true(self, mock_database_exists, mock_create_engine, check_db):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_database_exists.return_value = True

        result = check_db.exists_db()

        assert result is True
        mock_database_exists.assert_called_once_with(mock_engine.url)

    @patch('CheckDb.Classes.CheckDb.create_engine')
    @patch('CheckDb.Classes.CheckDb.database_exists')
    def test_exists_db_false(self, mock_database_exists, mock_create_engine, check_db):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_database_exists.return_value = False

        result = check_db.exists_db()

        assert result is False

    @patch('CheckDb.Classes.CheckDb.create_engine')
    @patch('CheckDb.Classes.CheckDb.database_exists')
    @patch('CheckDb.Classes.CheckDb.create_database')
    def test_create_db_when_not_exists(self, mock_create_database, mock_database_exists, mock_create_engine, check_db):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_database_exists.return_value = False

        check_db.create_db()

        mock_create_database.assert_called_once_with(mock_engine.url)
        assert check_db.error is None

    @patch('CheckDb.Classes.CheckDb.create_engine')
    @patch('CheckDb.Classes.CheckDb.database_exists')
    @patch('CheckDb.Classes.CheckDb.create_database')
    def test_create_db_when_exists(self, mock_create_database, mock_database_exists, mock_create_engine, check_db):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_database_exists.return_value = True

        check_db.create_db()

        mock_create_database.assert_not_called()
        assert check_db.error is None

    @patch('CheckDb.Classes.CheckDb.sq.inspect')
    @patch('CheckDb.Classes.CheckDb.create_engine')
    def test_exists_tables(self, mock_create_engine, mock_inspect):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector

        check_db = CheckDb()
        result = check_db.exists_tables('test_table')

        assert result is True
        mock_inspect.assert_called_once_with(mock_engine)
        mock_inspector.has_table.assert_called_once_with('test_table')
