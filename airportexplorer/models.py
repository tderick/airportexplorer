from flask_login import UserMixin

from airportexplorer.database import get_database


class User(UserMixin):

    def __init__(self, username, email, _id=None, nickname=None):
        self.username = email
        self.email = email
        self._id = _id
        self.nickname = nickname

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id

    @classmethod
    def get_by_username(cls, username):
        result = get_database().users.find_one({"email": username})
        if result is not None:
            return cls(
                username=result["email"],
                email=result["email"],
                _id=result["email"],
                nickname=result["nickname"],
            )
        else:
            return None

    @classmethod
    def get_by_email(cls, email):
        result = get_database().users.find_one({"email": email})
        if result is not None:
            return cls(
                username=result["email"],
                email=result["email"],
                _id=result["email"],
                nickname=result["nickname"],
            )
        else:
            return None

    @classmethod
    def get_by_id(cls, _id):
        result = get_database().users.find_one({"sub": _id})
        if result is not None:
            return cls(
                username=result["email"],
                email=result["email"],
                _id=result["sub"],
                nickname=result["nickname"],
            )
        else:
            return None

    @staticmethod
    def login_valid(email, password):
        return False

    @classmethod
    def register(cls, email, sub, nickname, email_verified=None):
        user = cls.get_by_email(email)
        if user is None:
            document = {
                "email": email,
                "sub": sub,
                "nickname": nickname,
                "email_verified": email_verified,
                "onboaring_complete": False,
            }
            get_database().users.insert_one(document)
            return True
        else:
            return False

    def json(self):
        return {
            "username": self.username,
            "email": self.email,
            "_id": self._id,
            "password": self.password,
        }
