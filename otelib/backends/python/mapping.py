"""Mapping strategy."""
from .base import BasePythonStrategy


import json
from uuid import uuid4

from oteapi.models import MappingConfig, AttrDict
from oteapi.plugins import create_strategy

class Mapping(BasePythonStrategy):
    """Context class for the data resource strategy interfaces for managing i/o
    operations."""

    def create(self, **kwargs) -> None:
        session_id = kwargs.pop("session_id", None)
        data = MappingConfig(**kwargs)

        resource_id = 'mapping-'+str(uuid4())
        self.id = resource_id
        self.cache[resource_id] = data.json()

        if session_id:
            session = self.cache[session_id]
            list_key = "mapping_info"
            if list_key in session:
                session[list_key].extend([resource_id])
            else:
                session[list_key] = [resource_id]

        return 

    def fetch(self, session_id: str) -> bytes:
        resource_id = self.id

        config = MappingConfig(**json.loads(self.cache[resource_id]))
        session_data = None if not session_id else self.cache[session_id]
        session_update = create_strategy("mapping", config)
        session_update = session_update.get(session=session_data)

        if session_update and session_id:
            self.cache[session_id].update(session_update)

        return AttrDict(**session_update).json()

    def initialize(self, session_id: str) -> bytes:
        resource_id = self.id

        config = MappingConfig(**json.loads(self.cache[resource_id]))
        if session_id:
            session_data = self.cache[session_id]
        else:
            session_data = None
        
        strategy = create_strategy("mapping", config)
        session_update = strategy.initialize(session=session_data)
        if session_update and session_id:
            self.cache[session_id].update(session_update)

        return AttrDict(**session_update).json()

