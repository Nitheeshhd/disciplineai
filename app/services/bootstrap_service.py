from __future__ import annotations

from app.core.config import Settings
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository


class BootstrapService:
    def __init__(self, session, settings: Settings):
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)

    async def seed_roles_and_admin(self) -> None:
        admin_role = await self.users.ensure_role("admin", "Platform administrator")
        await self.users.ensure_role("analyst", "Analytics read access")
        user_role = await self.users.ensure_role("user", "Standard user")

        admin_email = "admin@disciplineai.local"
        existing_admin = await self.users.get_by_email(admin_email)
        if existing_admin is None:
            admin_user = await self.users.create_user(
                email=admin_email,
                hashed_password=hash_password("Admin@12345"),
                telegram_user_id=0,
                first_name="System",
                last_name="Admin",
            )
            await self.users.assign_role(admin_user.id, admin_role.id)
            await self.users.assign_role(admin_user.id, user_role.id)
        await self.session.commit()
