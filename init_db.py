import pymysql

def create_database_if_not_exists():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Jilin@123',
        port=3306
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS teaching_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
    finally:
        connection.close()

if __name__ == "__main__":
    create_database_if_not_exists()
    print("Database checking/creation completed.")
