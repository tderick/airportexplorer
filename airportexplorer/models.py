from flask_login import UserMixin

from airportexplorer.database import get_database


class User(UserMixin):

    def __init__(self, username=None, email=None, _id=None, nickname=None, is_onboarding_complete=False, first_name=None, last_name=None, object_id=None):
        self.username = email
        self.email = email
        self._id = _id
        self.nickname = nickname
        self.is_onboarding_complete = is_onboarding_complete
        self.first_name = first_name
        self.last_name = last_name
        self.object_id = object_id
        
        

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
                is_onboarding_complete=result["is_onboarding_complete"],
                first_name=result["first_name"],
                last_name=result["last_name"],
                object_id=result["_id"],
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
                is_onboarding_complete=result["is_onboarding_complete"],
                first_name=result["first_name"],
                last_name=result["last_name"],
                object_id=result["_id"],
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
                is_onboarding_complete=result["is_onboarding_complete"],
                first_name=result["first_name"],
                last_name=result["last_name"],
                object_id=result["_id"],
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
                "is_onboarding_complete": False,
                "first_name": "",
                "last_name": "",
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

    def save(self):
        get_database().users.update_one(
            {"_id": self.object_id},
            {
                "$set": {
                    "email": self.email,
                    "sub": self._id,
                    "nickname": self.nickname,
                    "is_onboarding_complete": self.is_onboarding_complete,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                }
            },
        )   