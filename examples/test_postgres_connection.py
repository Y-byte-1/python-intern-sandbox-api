import asyncio

import asyncpg


async def main() -> None:
    connection = await asyncpg.connect(
        user="intern",
        password="intern_password",
        database="intern_db",
        host="127.0.0.1",
        port=5432,
    )

    version = await connection.fetchval("SELECT version();")

    print("PostgreSQL connection succeeded.")
    print(version)

    await connection.close()


if __name__ == "__main__":
    asyncio.run(main())