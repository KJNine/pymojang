import requests
from .api.auth import yggdrasil
from .api import security
from .api import user
from .api import base

from .globals import current_ctx
from .context import Context
from .profile import UserProfile

class UserSession:

    def __init__(self, session: requests.Session):
        self.__context = Context()
        self.__context.session = session
        
        self.__session = session
        self.__access_token = None
        self.__client_token = None
        self.__profile = None

    def connect(self, username: str, password: str):
        with self.__context(username=username, password=password):
            auth_data = yggdrasil.authenticate()
            self.__access_token = auth_data.pop('access_token')
            self.__client_token = auth_data.pop('client_token')

            names = base.names(auth_data['uuid'])
            name_change_data = user.check_name_change()
            profile_data = user.get_profile()

            data = {'names': names, **auth_data, **name_change_data, ** profile_data}
            self.__profile = UserProfile(**data)

    def close(self):
        with self.__context(access_token=self.__access_token, client_token=self.__client_token):
            return yggdrasil.invalidate()

    @property
    def profile(self):
        return self.__profile

    # Security
    @property
    def secure(self):
        with self.__context():
            return security.is_secure()

    @property
    def challenges(self):
        with self.__context():
            return security.get_challenges()

    def verify(self, answers: list):
        with self.__context():
            return security.verify_ip(answers)
    
    # Name
    def change_name(self, name: str):
        with self.__context():
            user.change_name(name)
            names = base.names(self.__profile.uuid)
            name_change_data = user.check_name_change()
            self.__profile.update(name=name, names=names, **name_change_data)

    # Skin
    def change_skin(self, path: str, variant='classic'):
        with self.__context():
            user.upload_skin(path, variant)
            profile_data = user.get_profile(self.__session)
            self.__profile.update(**profile_data)

    def reset_skin(self):
        with self.__context():
            user.reset_skin(self.__profile.uuid)
            profile_data = user.get_profile()
            self.__profile.update(**profile_data)
