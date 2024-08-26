import asyncio
import os
import typing as t
from datetime import timedelta

from hypercorn import Config
from hypercorn.asyncio import serve
from piccolo.apps.user.tables import BaseUser
from piccolo.engine import PostgresEngine
from piccolo.table_reflection import TableStorage
from piccolo_api.session_auth.tables import SessionsBase

from piccolo_admin import create_admin

USERNAME = "piccolo"
PASSWORD = "piccolo123"


class Sessions(SessionsBase):
    pass


class User(BaseUser, tablename="piccolo_user"):
    pass


# Before we call main we also need to run
# cd admin_ui
# npm install
# npm run build
async def main():
    db = PostgresEngine(
        config={
            "database": os.environ["POSTGRES_DB"],
            "user": os.environ["POSTGRES_USER"],
            "password": os.environ["POSTGRES_PASSWORD"],
            "host": os.environ["POSTGRES_HOST"],
            "port": int(os.environ["POSTGRES_PORT"]),
        },
        extensions=tuple(),
    )

    # TODO Patch engine= in
    storage = TableStorage(engine=db)
    await storage.reflect(
        schema_name="public",
    )

    # This tuple IS unique
    # however auto_include_related within
    # create_admin makes it non unique TableConfigs
    found_tables = storage.tables.values()

    for table_class in found_tables:
        table_class._meta._db = db

    # TODO Provide an argument such as auth provider
    #      such that we can make it function unauth
    app = create_admin(
        found_tables,
        auth_table=User,
        session_table=Sessions,
        auto_include_related=False,
    )

    # Server
    class CustomConfig(Config):
        use_reloader = True
        accesslog = "-"

    await serve(app, CustomConfig())


if __name__ == "__main__":
    asyncio.run(main())
