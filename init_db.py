import pymysql
from settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

def create_database_if_not_exists():
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()

if __name__ == "__main__":
    create_database_if_not_exists()
    print("Database checking/creation completed.")
