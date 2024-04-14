from protocol import *
from hashing import *
from sqlalchemy import create_engine, MetaData, Table, Column, String, Boolean
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session


class User:

    def __init__(self, username: str, password: str, email: str, phone_number: str):
        self.username = username
        self.base64_password = ScryptHash(password).create_b64_hash()
        self.email = email
        self.phone_number = phone_number
        self.signed_in = False


class Database:

    db_file = 'database.db'

    @classmethod
    def init(cls):
        cls.engine = create_engine(f'sqlite:///{cls.db_file}')

        metadata = MetaData()

        users_table = Table('users', metadata,
            Column('username', String, primary_key=True),
            Column('base64_password', String),
            Column('email', String),
            Column('phone_number', String),
            Column('signed_in', Boolean, default=False)
        )

        mapper(User, users_table)

        metadata.create_all(cls.engine)
    

    @classmethod
    def _find_user(cls, primary_key: str) -> Tuple[User, Session]:
        session = sessionmaker(bind=cls.engine)()
        wanted_user = session.query(User).get(primary_key)
        return wanted_user, session


    @classmethod
    def add_user(cls, user_details: Tuple[str, str, str, str]) -> bool:
        session = sessionmaker(bind=cls.engine)()
        username, password, email, phone_number = user_details
        new_user = User(username, password, email, phone_number)
        session.add(new_user)
        try:
            session.commit()
        except IntegrityError:
            print_colored('error', UserMessages.USER_EXISTS)
            session.close()
            return False
        print_colored('database', UserMessages.added(username))
        session.close()
        return True
    
    @classmethod
    def sign_in_check(cls, user_details: Tuple[str, str]) -> Tuple[bool, str]:
        username, password = user_details
        wanted_user, session = cls._find_user(username)

        if wanted_user is None:
            session.close()
            return False, UserMessages.NO_EXISTING_USER
        if wanted_user.signed_in:
            session.close()
            return False, UserMessages.ALREADY_SIGNED_IN
        if ScryptHash.create_from_b64(wanted_user.base64_password).compare(password):
            wanted_user.signed_in = True
            session.commit()
            session.close()
            return True, ''
        else:
            session.close()
            return False, UserMessages.INCORRECT_PASS
    
    @classmethod
    def sign_out(cls, username: str) -> Tuple[bool, str]:
        wanted_user, session = cls._find_user(username)
        if wanted_user is None:
            return False, UserMessages.NO_EXISTING_USER
        if not wanted_user.signed_in:
            return False, UserMessages.NOT_SIGNED_IN
        wanted_user.signed_in = False
        session.commit()
        session.close()
        return True, ''


    '''@classmethod
    def remove_user(cls, username: str):
        session = sessionmaker(bind=cls.engine)()
        wanted_user = cls._find_user(username)
        if wanted_user:
            session.delete(wanted_user)
            session.commit()
            print_colored('database', UserMessages.removed(username))
        else:
            print_colored('error', 'User could not be removed')
        session.close()'''
