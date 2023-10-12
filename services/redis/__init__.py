from helpers.env import EnvVars
from .types import RedisKeyActions, RedisKeyTypes
import redis
from typing import Union


class RedisManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=EnvVars.REDIS_HOST,
            port=EnvVars.REDIS_PORT,
            password=EnvVars.REDIS_PASSWORD,
        )

        if not self.redis_client.ping():
            raise Exception("Redis is not available")

    @staticmethod
    def get_key(
        key_type: RedisKeyTypes,
        key_action: RedisKeyActions,
        identifier: str,
    ):
        return f"{key_type.value}:{identifier}:{key_action.value}"

    def set_user_login_token(self, user_id: str, token: str):
        """
        set the login token of a user in redis for fast access
        """
        key = self.get_key(RedisKeyTypes.USER, RedisKeyActions.ACCESS_TOKEN, user_id)

        self.redis_client.set(key, token)

    def get_user_login_token(self, user_id: str) -> Union[str, None]:
        """
        get the login token of a user from redis
        """

        key = self.get_key(RedisKeyTypes.USER, RedisKeyActions.ACCESS_TOKEN, user_id)

        token = self.redis_client.get(key)

        if token:
            return token.decode()
        else:
            return None

    def delete_user_login_token(self, user_id: str):
        """
        delete the login token of a user from redis
        """
        key = self.get_key(RedisKeyTypes.USER, RedisKeyActions.ACCESS_TOKEN, user_id)

        self.redis_client.delete(key)

    def set_user_permissions(self, user_id: str, permissions: list[str]):
        """
        set the permissions of a user in redis for fast access
        """
        key = self.get_key(RedisKeyTypes.USER, RedisKeyActions.PERMISSIONS, user_id)
        permissions = ",".join(permissions)

        self.redis_client.set(key, permissions)

    def get_user_permissions(self, user_id: str) -> list:
        """
        get the permissions of a user from redis
        """
        key = self.get_key(RedisKeyTypes.USER, RedisKeyActions.PERMISSIONS, user_id)
        permissions = self.redis_client.get(key)

        if permissions:
            return permissions.decode().split(",")
        else:
            return []


REDIS_DB = RedisManager()
