import json
from MagicBook import DEFAULT_HYPNOTISM
from pymysql.converters import escape_string

def getDatabaseReady(cursor, connection):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    databaseName = 'chatbot'
    tableName = 'user_info'

    # 若不存在，则创建 chatbot 数据库，使用 utf8mb4 字符集
    cursor.execute("SHOW DATABASES")
    database_list = cursor.fetchall()
    if (databaseName,) in database_list:
        print("Database already exists")
    else:
        cursor.execute(f"CREATE DATABASE {databaseName} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("Database created")
    cursor.execute(f"USE {databaseName}")

    # 若不存在，则创建 user_info 数据表
    create_table = f'''CREATE TABLE IF NOT EXISTS {tableName} (
                        id INT NOT NULL AUTO_INCREMENT,
                        user_id VARCHAR(190) NOT NULL,
                        user_key VARCHAR(190) NOT NULL,
                        prompts JSON,
                        PRIMARY KEY (id),
                        UNIQUE KEY (user_id)
                    )'''
    cursor.execute(create_table)

def initUser(cursor, connection, userId):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    select_user_info = f"SELECT * FROM user_info WHERE user_id={userId}"
    cursor.execute(select_user_info)
    user = cursor.fetchone()
    
    if user is None:
        insert_user_info = f"INSERT INTO user_info (user_id, user_key, prompts) VALUES (%s, %s, %s)"
        values = (userId, '', json.dumps(DEFAULT_HYPNOTISM))
        cursor.execute(insert_user_info, values)
        connection.commit()
        hypnotism = DEFAULT_HYPNOTISM.copy()
    else:
        hypnotism = json.loads(user[3])
    
    return hypnotism

def getUserKey(cursor, connection, userId):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    select_user_info = f"SELECT user_key FROM user_info WHERE user_id={userId}"
    cursor.execute(select_user_info)
    row = cursor.fetchone()
    key = None if row[0] == '' else row[0]
    return key

def updateUserKey(cursor, connection, userId, userKey):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    update_user_key = f"UPDATE user_info SET user_key='{userKey}' WHERE user_id={userId}"
    cursor.execute(update_user_key)
    connection.commit()

def getUserPrompts(cursor, connection, userId):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    select_prompts = f"SELECT prompts FROM user_info WHERE user_id={userId}"
    cursor.execute(select_prompts)
    result = cursor.fetchone()
    prompts = json.loads(result[0])
    return prompts

def updateUserPrompts(cursor, connection, userId, prompts):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    update_user_prompts = f"UPDATE user_info SET prompts=%s WHERE user_id=%s"
    values = (json.dumps(prompts), userId)
    cursor.execute(update_user_prompts, values)
    connection.commit()

def deleteUser(cursor, connection, userId):
    connection.ping(reconnect=True) # 检查连接是否存在，断开的话重连
    update_user_prompts = f"DELETE FROM user_info where user_id=%s"
    values = (userId, )
    cursor.execute(update_user_prompts, values)
    connection.commit()