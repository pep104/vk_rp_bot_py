import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
from keyboards import *
import sqlite3

token = ""
db = sqlite3.connect("server.db")
sql = db.cursor()
session = vk_api.VkApi(
    token=token)
sql.execute("""CREATE TABLE IF NOT EXISTS users  (
    id INT,
    state TEXT,
    project TEXT,
    server TEXT,
    role TEXT,
    item TEXT,
    connect INT,
    balans INT
)""")

sql.execute("""CREATE TABLE IF NOT EXISTS ob  (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    platforma TEXT,
    locate TEXT,
    state TEXT,
    name TEXT,
    price INTEGER,
    photo TEXT
)""")
db.commit()


def send(user_id, message, keyboard=None, attachment=None):
    post = {
        "user_id": user_id,
        "message": message,
        "random_id": 0
    }

    if keyboard is not None:
        post["keyboard"] = keyboard.get_keyboard()
    if attachment is not None:
        post["attachment"] = attachment
    session.method("messages.send", post)


for event in VkLongPoll(session).listen():

    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        text = event.text
        user_id = event.user_id
        sql.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
        if sql.fetchone() is None:
            sql.execute(f"INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (user_id, 'nothing', "", "", "", "", -1, 0))
            db.commit()

        elif sql.execute(f'SELECT connect FROM users  WHERE id="{user_id}"').fetchone()[0] != -1:
            sql.execute(f"SELECT connect FROM users WHERE id = '{user_id}'")
            chat = sql.fetchone()[0]
            ob_id = sql.execute(f'SELECT state FROM users WHERE id="{user_id}"').fetchone()[0]
            if chat != -1:
                if text == "":
                    send(user_id, "Вы ничего не написали...", keyboard_chat_connect)
                elif text == 'Покупка состоялась' and event.payload == str(chat):
                    sql.execute(f'UPDATE users SET connect="{-1}" WHERE id="{user_id}"')
                    db.commit()
                    sql.execute(f'UPDATE users SET connect="{-1}" WHERE id="{chat}"')
                    db.commit()
                    send(chat, "СДЕЛКА ЗАКРЫТА!", keyboard_start)
                    send(user_id, "СДЕЛКА ЗАКРЫТА!", keyboard_start)
                    sql.execute(f'DELETE FROM ob WHERE id="{ob_id}"')
                    db.commit()

                elif text == 'Поддержка':
                    send('152293844',
                         f'Создатель запроса: {user_id}\n\n Его собеседник: {chat}\n\n Id объявления: {ob_id}')
                    sql.execute(f'UPDATE users SET connect="{-2}" WHERE id="{user_id}"')
                    db.commit()
                    sql.execute(f'UPDATE users SET connect="{-2}" WHERE id="{chat}"')
                    db.commit()
                    send(user_id, 'Опишите вашу проблему, модератор пстарается как можно быстрее ее решить')

                elif chat != -2:
                    sql.execute(f'SELECT state FROM users WHERE id="{user_id}"')
                    if sql.fetchone()[0] == 'prodaja':
                        keyboard_chat_connect_1 = VkKeyboard()
                        keyboard_chat_connect_1.add_button('Покупка состоялась', VkKeyboardColor.PRIMARY.POSITIVE,
                                                           user_id)
                        keyboard_chat_connect_1.add_button('Поддержка', VkKeyboardColor.PRIMARY.NEGATIVE)
                        send(chat, "!!!Собеседнник: " + text, keyboard_chat_connect_1)
                        send(user_id, "!..ваше сообщение доставлено..!", keyboard_chat_connect)
                    else:
                        keyboard_chat_connect_1 = VkKeyboard()
                        keyboard_chat_connect_1.add_button('Покупка состоялась', VkKeyboardColor.PRIMARY.POSITIVE, chat)
                        keyboard_chat_connect_1.add_button('Поддержка', VkKeyboardColor.PRIMARY.NEGATIVE)
                        send(chat, "!!!Собеседнник: " + text, keyboard_chat_connect)
                        send(user_id, "!..ваше сообщение доставлено..!", keyboard_chat_connect_1)


        elif text == "start" or text == "Меню" or text == 'Нет, вернуться в меню':
            send(user_id, "Выберите проект", keyboard_start)
            sql.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
            if sql.fetchone() is None:
                sql.execute(f"INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", (user_id, 'nothing', "", "", "", "", -1, 0))
                db.commit()

            sql.execute(f"UPDATE users SET state='nothing' WHERE id='{user_id}'")
            db.commit()


        elif text == 'Приобрести':
            post = event.payload
            sql.execute(f'SELECT balans FROM users WHERE id="{user_id}"')
            balance = int(sql.fetchone()[0])
            sql.execute(f'SELECT price FROM ob where id="{post}"')
            price_ob = int(sql.fetchone()[0])
            if balance >= price_ob:
                keyboard_chat = VkKeyboard(inline=True)
                keyboard_chat.add_button('Да, хочу', VkKeyboardColor.PRIMARY.POSITIVE, post)
                keyboard_chat.add_button('Нет, вернуться в меню', VkKeyboardColor.PRIMARY.NEGATIVE)
                send(user_id, 'Вы хотите начать диалог с продавцом?', keyboard_chat)
            else:
                send(user_id, 'У вас недостаточно средств, пополните свой баланс', keyboard_start)
        elif text == 'Да, хочу':
            post_id = event.payload
            sql.execute(f"SELECT user_id FROM ob WHERE id = '{post_id}'")
            companion_id = sql.fetchone()[0]
            sql.execute(f"SELECT price FROM ob WHERE id = '{post_id}'")
            price1 = sql.fetchone()[0]
            sql.execute(f'SELECT balans FROM users WHERE id="{user_id}"')
            ball = sql.fetchone()[0]
            sql.execute(f'UPDATE users SET balans="{int(ball) - int(price1)}" WHERE id="{user_id}"')
            sql.execute(f'UPDATE users SET balans="{int(ball) + int(price1) // 1.2}" WHERE id="{companion_id}"')
            db.commit()

            sql.execute(f'SELECT connect FROM users WHERE id="{companion_id}"')
            if sql.fetchone()[0] != -1:
                send(user_id, 'Продавец сейчас занят, дождитесь пока он завершит сделку и попробуйте позднее')
            else:
                sql.execute(f'UPDATE users SET connect="{companion_id}" WHERE id="{user_id}"')
                db.commit()
                sql.execute(f'UPDATE users SET state="{post_id}" WHERE id="{user_id}"')
                db.commit()
                sql.execute(f'UPDATE users SET connect="{user_id}" WHERE id="{companion_id}"')
                db.commit()
                sql.execute(f"SELECT name FROM ob WHERE id = '{post_id}'")
                name = sql.fetchone()[0]
                sql.execute(f"SELECT price FROM ob WHERE id = '{post_id}'")
                price = sql.fetchone()[0]
                send(companion_id,
                     f'С вами сейчас свяжется покупатель по поводу товара: {name} стоимостью {price}\n\n\n Будьте '
                     f'готовы!\n\n\n\n НАЖИМАЙТЕ НА КНОПКУ ПОДДЕРЖКА ТОЛЬКО В КРАЙНЕМ СЛУЧАЕ, ТАК КАК ЧАТ БУДЕТ '
                     f'ПРЕРВАН!', keyboard_chat_connect)
                send(user_id, 'Вы начали диалог с продавцом!\n\n\n\n НАЖИМАЙТЕ НА КНОПКУ ПОДДЕРЖКА ТОЛЬКО В КРАЙНЕМ '
                              'СЛУЧАЕ, ТАК КАК ЧАТ БУДЕТ ПРЕРВАН!', keyboard_chat_connect)
                sql.execute(f'UPDATE users SET state="prodaja" WHERE id="{companion_id}"')
                db.commit()


        elif text == "GTA 5 RP":
            send(user_id, "Выберите сервер", keyboard_choose_choose_server_gta5rp)
            sql.execute(f"UPDATE users SET project='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text == "MADJESTIK RP":
            send(user_id, "Выберите сервер", keyboard_choose_choose_server_madjestik)
            sql.execute(f"UPDATE users SET project='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text == "ARIZONA RP":
            send(user_id, "Выберите сервер", keyboard_choose_choose_server_Arizona)
            sql.execute(f"UPDATE users SET project='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text == "GRAND RP":
            send(user_id, "Выберите сервер", keyboard_choose_choose_server_GRAND)
            sql.execute(f"UPDATE users SET project='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text == "RRP GTA V":
            send(user_id, "Выберите сервер", keyboard_choose_choose_server_RRP)
            sql.execute(f"UPDATE users SET project='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text == "SMOTRARAGE":
            send(user_id, "Выберите сервер", keyboard_choose_choose_server_SMOTRA)
            sql.execute(f"UPDATE users SET project='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text in servers:
            send(user_id, "Вы хотите купить или продать?", keyboard_buy_sale)
            sql.execute(f"UPDATE users SET server='{text}' WHERE id='{user_id}'")
            db.commit()

        elif text == "Купить":
            send(user_id, "Что вы хотите купить?", keyboard_item)
            sql.execute(f"UPDATE users SET state='purchase_user' WHERE id='{user_id}'")
            db.commit()

        elif text == 'Продать':
            send(user_id, "Что вы хотите продать?", keyboard_item)
            sql.execute(f"UPDATE users SET state='sale' WHERE id='{user_id}'")
            db.commit()

        elif text in items:
            sql.execute(f"UPDATE users SET item='{text}' WHERE id='{user_id}'")
            db.commit()
            sql.execute(f"SELECT state FROM users WHERE id = '{user_id}'")
            if sql.fetchone()[0] == "purchase_user":
                sql.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                per1 = sql.fetchone()

                per2 = per1[2] + per1[3] + per1[5]
                sql.execute(f"SELECT * FROM ob WHERE locate = '{per2}'")
                posts = sql.fetchall()

                if not posts:
                    send(user_id, 'На данный момент нет ни одного объявления', keyboard_start)
                else:
                    send(user_id,
                         f'Платформа: {per1[2]}\n Сервер: {per1[3]}\n Раздел: {per1[5]}\n\n\n\n\n\n\n Выберите необходимые товары')
                    for i in posts:
                        if i[-1] == 'photo':
                            key = VkKeyboard(inline=True)
                            key.add_button("Приобрести", VkKeyboardColor.PRIMARY.POSITIVE, i[0])
                            send(user_id, f"Название: {i[-3]}\nСтоимость: {i[-2]}", key)
                        else:
                            key = VkKeyboard(inline=True)
                            key.add_button("Приобрести\n\n\n\n\n\n\n\n", VkKeyboardColor.PRIMARY.POSITIVE, i[0])
                            send(user_id, f"-----------------------------\n Название: {i[-3]}\nСтоимость: {i[-2]}\n ",
                                 key, i[-1])
            else:
                send(user_id, "Введите название товара и его цену через пробел \nНапример: куртка burberry 100000 "
                              "\nСоветуем прикрепить фотографию товара")
                sql.execute(f"UPDATE users SET state='sale' WHERE id='{user_id}'")
                db.commit()
        elif sql.execute(f'SELECT state FROM users WHERE id="{user_id}"').fetchone()[0] == 'sale':
            arr = event.attachments
            sql.execute(f"SELECT state FROM users WHERE id = '{user_id}'")
            if sql.fetchone()[0] == 'sale':
                sql.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
                per1 = sql.fetchone()
                per2 = per1[2] + per1[3] + per1[5]
                m = text.split()
                if len(m) == 1:
                    send(user_id,
                         'Неправильный формат объявления, введдите название и стоимость (цифрами) через пробел')
                else:
                    try:
                        price = int(m[-1])
                        m.pop()
                        name = " ".join(m)
                        if not arr:
                            sql.execute(
                                f"INSERT INTO ob(user_id, platforma, locate, state, name, price, photo) VALUES (?,?,?,?,?,?,?)",
                                (user_id, "vk", per2, "purchase_ob", name, int(price * 1.2), f'photo'))
                        else:
                            p = requests.get(f"https://api.vk.com/method/messages.getById?access_token=vk1.a"
                                             f".ZOVw19gA4jwPOHHjreUDa6E5pvVBbFM9EMMTLABFycsYUVg0f9Y9OKHtbecTHPTtKm-hcxBxrL3_TQ"
                                             f"-1AQgj6lNTYnl2mvQrBYfbtPDlbxOvRDSrCojos8yh3n2TEkcitobSKom6cIUZEP8tGeYodRDEmA4y3WGY15GIOEhmk-c6vshqgEA5MlSREc9TSa7_Sb2gWNX1tAu4rR-LWzQIoQ&message_ids={event.message_id}&v=5.131")

                            access_key = p.json()['response']['items'][0]['attachments'][0]['photo']['access_key']
                            photo_id = p.json()['response']['items'][0]['attachments'][0]['photo']['id']
                            owner_id = p.json()['response']['items'][0]['attachments'][0]['photo']['owner_id']
                            sql.execute(
                                f"INSERT INTO ob(user_id, platforma, locate, state, name, price, photo) VALUES (?,?,?,?,?,?,?)",
                                (user_id, "vk", per2, "purchase_ob", name, int(price * 1.2),
                                 f'photo{owner_id}_{photo_id}_{access_key}'))
                        db.commit()
                        sql.execute(f"UPDATE users SET state='sale' WHERE id='{user_id}'")
                        db.commit()
                        send(user_id,
                             f"Ваше обьявление успешно добавлено\nПроект: {per1[2]}\nСервер: {per1[3]}\nРаздел: {per1[5]}\n"
                             f"Наименование: {name}\n Стоимость: {price}",
                             keyboard_start)
                    except:
                        send(user_id,
                             'Неправильный формат объявления, введдите название и стоимость (цифрами) через пробел')
        elif text == 'Баланс':
            sql.execute(f'SELECT balans FROM users WHERE id="{user_id}"')
            send(user_id, f'Ваш баланс: {sql.fetchone()[0]}', keyboard_balance)
        else:
            send(user_id, 'Ваша команда не распознана, воспользуйтесь специальными кнопками или напишите "Меню"')
