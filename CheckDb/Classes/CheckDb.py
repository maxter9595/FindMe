import os

import sqlalchemy as sq
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from CheckDb.structure import Genders, Status, form_tables


class CheckDb():
    def __init__(self):
        self.error = None
        self.tables = ['genders', 'status', 'cities', 'users', 'criteria', 'favorites', 'exceptions']

    def get_engine(self) -> Engine:
        """
        Формирует движок Sqlalchemy

        Выводной параметр:
        - движок Sqlalchemy
        """
        load_dotenv()

        dbname = os.getenv(key='DB_NAME')
        user = os.getenv(key='USER_NAME_DB')
        password = os.getenv(key='USER_PASSWORD_DB')
        host = os.getenv(key='DB_HOST')
        port_str = os.getenv(key='DB_PORT')

        try:
            port = int(port_str) if port_str else 5432
        except ValueError:
            print(f"Warning: Invalid port value '{port_str}', using default 5432")
            port = 5432

        dns_link = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        return create_engine(dns_link)

    def start_session(self) -> Session:
        """
        Инициирует сессию

        Выводной параметр:
        - экземпляр класса Session
        """
        engine = self.get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        return session

    def exists_db(self) -> bool:
        """
        Проверяет наличие БД в Postgres

        Выводимый параметр:
        bool : True - есть база данных, False - нет базы данных
        """
        engine = self.get_engine()
        return database_exists(engine.url)

    def create_db(self) -> None:
        """
        Создает базу данных
        """
        try:
            engine = self.get_engine()
            if not self.exists_db():
                print("Creating database...")
                create_database(engine.url)
                print("Database created successfully")
                self.error = None
            else:
                print("Database already exists")
        except Exception as e:
            self.error = str(e)
            print(f"Error creating database: {e}")

    def exists_tables(self, table_name: str) -> bool:
        """
        Проверяет существование таблицы в БД

        Вводной параметр:
        - table_name: наименование таблицы

        Выводимый параметр:
        bool : True -таблица есть в БД,
               False - таблица отсутствует в БД
        """
        engine = self.get_engine()
        return sq.inspect(engine).has_table(table_name)

    def create_tables(self):
        """
        Создает таблицы в БД
        """
        try:
            engine = self.get_engine()
            print("Creating tables...")
            form_tables(engine)
            
            for name_table in self.tables:
                if not self.exists_tables(name_table):
                    self.error = f'Таблица {name_table} не создана'
                    print(f"Error: Table {name_table} not created")
                    break
            else:
                self.error = None
                print("All tables created successfully")
                
        except Exception as e:
            self.error = str(e)
            print(f"Error creating tables: {e}")

    def fill_tables(self):
        """
        Заполняет таблицу genders и statuses
        """
        try:
            print("Filling tables...")
            session = self.start_session()
            genders = session.query(Genders).all()
            statuses = session.query(Status).all()

            if not genders:
                female = Genders(id=1, gender='Женщина')
                male = Genders(id=2, gender='Мужчина')
                session.add_all([female, male])
                session.commit()
                self.error = None
                print("Genders table filled successfully")
            
            if not statuses:
                single = Status(id=1, status='Не женат (не замужем)')
                couple = Status(id=2, status='В поиске')
                session.add_all([single, couple])
                session.commit()
                self.error = None
                print("Statuses table filled successfully")

            session.close()
        except Exception as e:
            self.error = str(e)
            print(f"Error filling tables: {e}")

    def check_db(self) -> bool:
        """
        Проверка, есть база данных или нет
        Если нет - создадим
        """
        try:
            self.create_db()
            self.create_tables()
            self.fill_tables()
            return self.error is None
        except Exception as e:
            self.error = str(e)
            print(f"Error in check_db: {e}")
            return False
