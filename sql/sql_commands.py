# import sqlite3
# from config import PATH_TO_DB
#
#
# con = sqlite3.connect(PATH_TO_DB)
#
# cursor = con.cursor()
#
# #Создание таблицы с соответсвующими колонками
# cursor.execute("""CREATE TABLE users(id INTEGER, username TEXT,
#                 first_name TEXT,last_name TEXT,start_date TEXT,
#                 finish_date TEXT, status INTEGER, link TEXT)"""
#                )
#
# # Щаблон для данных в таблице
# insert_query = "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?);"
#
#
# #Список пользователей которых необходимо добавить
# users_data = [
#     (425895564, 'Georgetheframe', 'George', 'M'),
#     (0000, 'Ge', 'Geor', 'Moto',)
# ]
# #Добавление юзеров из списка
# cursor.executemany(insert_query, users_data)
#
#
# #Добавление одного юзера
# user = (425895564, 'Georgetheframe', 'George', 'M', 4, 2, 1)
# cursor.execute(insert_query, user)
#
#
# # Добавление строчки в таблицу из переменных
# id = 425895564
# username = 'Georgetheframe'
# first_name = 'George'
# last_name = 'fff'
#
# insert_query = "INSERT INTO users VALUES (?, ?, ?, ?)"
# cursor.executemany(insert_query, (id, username, first_name, last_name))
#
#
# #Извлечние столбца из таблицы
# cursor.execute("SELECT id FROM users")
# print(cursor.fetchall())
# for row in cursor:
#     print(row)
# db_connect().commit()
# db_connect().close()
#
# #Печать всех данных в дб. Экзекутор передает в курсок данные, которые мы задаем
# cursor.execute("SELECT * FROM users")
# data = cursor
# [print(row) for row in data]
#
#
# cursor.execute("SELECT * FROM users WHERE first_name IS 'George'")
# cursor.execute("SELECT * FROM users WHERE first_name IS 'George'")
#
#
# #Извлечение строк по условию
# cursor.execute("SELECT * FROM users WHERE first_name IS 'George'")
# for row in cursor:
#     print(row)
#
#
# #Извлечение первой записи в таблице
# print(cursor.fetchone())
# #Вывод списка строк
# print(cursor.fetchall())
#
# #Проверка на наличие юзера в Таблице
# print(all(map(lambda x: 425895564 not in x, result)))
#
# #Изменение данных в таблице по определенному уловию
# cursor.execute("UPDATE users SET status=1 WHERE first_name IS 'George'")
# #После апдейта курсор обнулился, через селект вставляем их в курсор
# cursor.execute("SELECT * FROM users")
#
# data = cursor.fetchall()
# [print(row) for row in data]
#
# #Удаление данных
# cursor.execute("DELETE FROM users WHERE first_name IS 'George'")
# print(cursor.fetchall())
#
# con.commit()
# con.close()