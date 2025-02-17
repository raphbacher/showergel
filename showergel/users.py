"""
===========
Users table
===========

This module contains functions that process and store user list for Liquidsoap's harbor.
"""

import logging
import crypt
from datetime import datetime
from hmac import compare_digest
from typing import Type, List, Dict

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import Session
from sqlalchemy.dialects.sqlite import JSON, DATETIME
import arrow

from showergel.db import Base


_log = logging.getLogger(__name__)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    created_at = Column(DATETIME, default=datetime.utcnow)
    modified_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    extra = Column(JSON, default={})

    def to_dict(self) -> Dict:
        return {
            "username": self.username,
            "created_at": arrow.get(self.created_at, tzinfo='utc').isoformat(),
            "modified_at": arrow.get(self.modified_at, tzinfo='utc').isoformat(),
        }

    @classmethod
    def list(cls, db:Type[Session]) -> List[Dict]:
        return [u.to_dict() for u in db.query(cls).order_by(cls.username)]

    @classmethod
    def create(cls, db:Type[Session], username:String, password:String):
        user = cls(username=username, password=crypt.crypt(password))
        db.add(user)
        db.flush()
        return user

    @classmethod
    def from_username(cls, db:Type[Session], username:String):
        return db.query(cls).filter(cls.username == username).first()

    @classmethod
    def check(cls, db:Type[Session], username:String, password:String):
        user = cls.from_username(db, username)
        if user:
            if compare_digest(crypt.crypt(password, user.password), user.password):
                return user
        return None

    @classmethod
    def delete(cls, db:Type[Session], username:String):
        if username:
            db.query(cls).filter(cls.username == username).delete()

    def update_password(self, new_password):
        self.password = crypt.crypt(new_password)
