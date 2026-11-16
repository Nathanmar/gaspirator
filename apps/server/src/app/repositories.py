"""Data access for users and organisations.

Routes only talk to the `UserRepository` / `OrganizationRepository` interfaces. The
in-memory versions below are used until PostgreSQL is wired: the database version only
has to implement the same methods, then be returned by `app.dependencies`. Routes and
tests do not change.

The stored shapes follow the contract, so they map 1:1 to the future tables:
- `StoredUser`   -> table `users` (`Me` fields + `organization_id` + `password_hash`)
- `Organization` -> table `organizations` (the contract schema as is)
"""

from typing import Protocol

from pydantic import BaseModel, EmailStr

from app.schemas import Organization, UserRole


class StoredUser(BaseModel):
    id: int
    email: EmailStr
    firstname: str
    lastname: str
    role: UserRole
    organization_id: int | None
    password_hash: str


class UserRepository(Protocol):
    async def get(self, user_id: int) -> StoredUser | None: ...

    async def get_by_email(self, email: str) -> StoredUser | None: ...

    async def add(self, user: StoredUser) -> StoredUser:
        """Store a new user; the `id` given is ignored and a new one is assigned."""
        ...

    async def update(self, user: StoredUser) -> StoredUser: ...


class OrganizationRepository(Protocol):
    async def get(self, organization_id: int) -> Organization | None: ...

    async def get_by_legal_id(self, legal_id: str) -> Organization | None: ...

    async def add(self, organization: Organization) -> Organization:
        """Store a new organisation; the `id` given is ignored and a new one is assigned."""
        ...

    async def update(self, organization: Organization) -> Organization: ...


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._rows: dict[int, StoredUser] = {}
        self._next_id = 1

    async def get(self, user_id: int) -> StoredUser | None:
        return self._rows.get(user_id)

    async def get_by_email(self, email: str) -> StoredUser | None:
        email = email.lower()
        return next((u for u in self._rows.values() if u.email.lower() == email), None)

    async def add(self, user: StoredUser) -> StoredUser:
        stored = user.model_copy(update={"id": self._next_id})
        self._rows[stored.id] = stored
        self._next_id += 1
        return stored

    async def update(self, user: StoredUser) -> StoredUser:
        self._rows[user.id] = user
        return user


class InMemoryOrganizationRepository:
    def __init__(self) -> None:
        self._rows: dict[int, Organization] = {}
        self._next_id = 1

    async def get(self, organization_id: int) -> Organization | None:
        return self._rows.get(organization_id)

    async def get_by_legal_id(self, legal_id: str) -> Organization | None:
        return next((o for o in self._rows.values() if o.legal_id == legal_id), None)

    async def add(self, organization: Organization) -> Organization:
        stored = organization.model_copy(update={"id": self._next_id})
        self._rows[stored.id] = stored
        self._next_id += 1
        return stored

    async def update(self, organization: Organization) -> Organization:
        self._rows[organization.id] = organization
        return organization
