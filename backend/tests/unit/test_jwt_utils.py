"""Unit tests for JWT utilities (authentication)"""
import pytest
from datetime import datetime, timedelta
from jwt import InvalidTokenError  # Błąd gdy token invalid

# Importy z twojej aplikacji - tutaj jest klucz!
from app.utils.jwt_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class TestPasswordHashing():
    def test_hash_password_creates_hash(self):
        password = "test123"

        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password

    def test_verify_password(self):
        """Checking if password is verifiable"""
        password = "test123"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_verify_password_wrong_password(self):
        password = "test123"
        wrong_password = "test456"

        hashed = hash_password(password)

        assert not verify_password(wrong_password, hashed)

    def test_different_password_have_different_hashes(self):
        password1 = "test123"
        password2 = "test456"

        hash1 = hash_password(password1)
        hash2 = hash_password(password2)

        assert hash1 != hash2


class TestJWTTokens():
       
        def test_create_token_contains_data(self):
            
            user_id = "user123"
            data = {"sub": user_id}

            token = create_access_token(data)
            decoded = decode_token(token)

            assert decoded["sub"] == user_id
        

        def test_decode_token_returns_dict(self):

            data = {"sub": "user123"}

            token = create_access_token(data)
            decoded = decode_token(token)

            assert isinstance(decoded, dict)
