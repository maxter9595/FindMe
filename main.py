import json
import os
from io import BytesIO

import requests
import vk_api
from dotenv import load_dotenv
from vk_api import VkUpload
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

import VK.messages as ms
from CheckDb.Classes.CheckDb import CheckDb
from Repository.Classes.CardExceptions import CardExceptions
from Repository.Classes.CardFavorites import CardFavorites
from Repository.repository import Repository
from VK.Classes.User import User
from VK.Classes.VKService import VKService

load_dotenv()

token = os.getenv(key='VK_GROUP_TOKEN')
token_api = os.getenv(key='VK_USER_TOKEN')
api_version = os.getenv(key='API_LONG_POLL_VERSION')

vk_session = vk_api.VkApi(token=token, api_version=api_version)
longpoll = VkLongPoll(vk_session)
users_list = {}

def handle_start(user_id):
    """
    Обработка начала работы, получение и заполнение данных из профися vk
    :param user_id: id пользователя
    :return:
    """
    if not user_id in users_list.keys():
        user = User(user_id)
        users_list[user_id] = user
        users_info = vk_srv.get_users_info(token=token_api, user_id=user.get_user_id())
        if not users_info is None:
            user.set_first_name(users_info['first_name'])
            user.set_last_name(users_info['last_name'])
            user.set_gender(users_info['sex'])
            if users_info.get('bdate'):
                user.set_age(vk_srv.determine_age(users_info['bdate']))
            if users_info.get('city') is None:
                users_info['city'] = {'id': 1, 'title': 'Москва'}
            user.set_city({'id': users_info['city']['id'], 'name': users_info['city']['title']})
            hello_message = ms.get_hello_message(user.get_user_id(), user.get_first_name())
            send_message(hello_message)
        else:
            hello_message_error = ms.get_hello_mmessage_error(user.get_user_id())
            send_message(hello_message_error)
    else:
        message_id = handle_registration(users_list[event.user_id])
        users_list[event.user_id].set_id_msg_edit_id(message_id)



def handle_registration(user: User):
    """
    Обработчмк нажатия кнопки "хочу зарегистрироваться"
    :param user: параметры пользователя
    :return: id сообщения при отправке
    """
    if user.get_id_msg_edit_id() > -1:
        vk_session.method('messages.delete', {'message_ids': user.get_id_msg_edit_id(), 'delete_for_all': 1})
    message_registration = ms.get_registration_message(user)
    return send_message(message_registration)


def send_ask_edit_anketa(user: User, str_arg):
    """
    Отправка предложения заполнить значение анкеты
    и установка текущего шага для редактирования анкеты пользователя
    :param user: параметры пользователя
    :param str_arg: шаг
    """
    user.set_step('anketa_'+str_arg)
    message_edit = ms.get_edit_message(user.get_user_id(), str_arg)
    send_message(message_edit)


def send_message(message):
    """
    Отправка сформированного сообщения
    :param message: сформированное сообщение
    """
    return vk_session.method('messages.send', message)


def set_param(user: User, text: str):
    """
    Запись текущего пункта анкеты в класс User
    :param user: параметры пользователя
    :param text: значение параметра
    """
    if user.get_step() == 'anketa_first_name':
        user.set_first_name(text)
    elif user.get_step() == 'anketa_last_name':
        user.set_last_name(text)
    elif user.get_step() == 'anketa_age':
        try:
            age = int(text)
            if 1 <= age <= 120:
                user.set_age(age)
            else:
                user.set_age(18)
        except (ValueError, TypeError):
            user.set_age(18)
    elif user.get_step() == 'anketa_gender':
        try:
            user.set_gender(int(text))
        except (ValueError, TypeError):
            user.set_gender(2)
    elif user.get_step() == 'anketa_city':
        city = vk_srv.get_city_by_name(token=token_api, text=text)
        if city is None:
            city = {'id': 1, 'name': 'Москва'}
        user.set_city(city)
    else:
        if user.get_step() == 'criteria_gender':
            try:
                user.get_criteria().gender_id = int(text)
            except (ValueError, TypeError):
                user.get_criteria().gender_id = 2
        elif user.get_step() == 'criteria_age':
            try:
                age = text.split('-')
                if len(age) == 2:
                    age_from = int(age[0].strip())
                    age_to = int(age[1].strip())
                    if age_from > age_to:
                        raise ValueError("Начальный возраст не может быть больше конечного")
                    user.get_criteria().age_from = age_from
                    user.get_criteria().age_to = age_to
                else:
                    raise ValueError("Invalid format")
            except (ValueError, TypeError, IndexError):
                user.get_criteria().age_from = 18
                user.get_criteria().age_to = 28
        elif user.get_step() == 'criteria_status':
            try:
                user.get_criteria().status = int(text)
            except (ValueError, TypeError):
                user.get_criteria().status = 2
        elif user.get_step() == 'criteria_has_photo':
            try:
                user.get_criteria().has_photo = int(text)
            except (ValueError, TypeError):
                user.get_criteria().has_photo = 0
        elif user.get_step() == 'criteria_city':
            city = vk_srv.get_city_by_name(token=token_api, text=text)
            if city is None:
                city = {'id': 1, 'name': 'Москва'}
            user.get_criteria().city = city


def save_anketa(user: User):
    repository.add_user(user)
    vk_session.method('messages.delete',
                      dict(message_ids=user.get_id_msg_edit_id(),
                           delete_for_all=1))
    user.set_id_msg_edit_id(-1)


def main_menu(user: User):
    user.set_list_cards(None)
    user.set_index_view(-1)
    user.set_id_msg_edit_id(-1)

    message_main_menu = ms.get_main_menu_message(user)
    send_message(message_main_menu)


def upload_photo(upload, url):
    try:

        if url:
            img = requests.get(str(url), timeout=10).content
            f = BytesIO(img)

            response = upload.photo_messages(f)[0]

            owner_id = response['owner_id']
            photo_id = response['id']
            access_key = response['access_key']

            return {'owner_id': owner_id, 'photo_id': photo_id, 'access_key': access_key}

        else:
            return {}

    except requests.exceptions.Timeout:
        print(f"Timeout error when loading photo: {url}")
        return {}
    
    except requests.exceptions.RequestException as e:
        print(f"Error loading photo {url}: {e}")
        return {}
    
    except Exception as e:
        print(f"Unexpected error in upload_photo: {e}")
        return {}

def find_users(upload, user: User, vk_srv, token):
    try:
        list_cards = vk_srv.users_search(user.get_criteria(), token_api)
        if list_cards:
            user.set_list_cards(list_cards)
            user.set_index_view(-1)
            view_next_card(upload, user, vk_srv, token)
        else:
            message_error_search = ms.get_message_error_search(user.get_user_id())
            send_message(message_error_search)
    except Exception as e:
        print(f"Error in find_users: {e}")
        message_error = ms.get_message_error_search(user.get_user_id())
        send_message(message_error)
        main_menu(user)

def view_next_card(upload, user: User, vk_srv, token):
    try:
        if user.get_size_list_cards() > 0:
            next_index = user.get_index_view()
            next_index = next_index + 1
            if next_index == user.get_size_list_cards():
                next_index = next_index - 1
            user.set_index_view(next_index)

            photos = user.get_list_cards()[next_index].photos
            attachment = []
            for photo in photos:
                try:
                    photo_struct = upload_photo(upload, photo)
                    if photo_struct:
                        attachment.append(f'photo{photo_struct["owner_id"]}_{photo_struct["photo_id"]}_{photo_struct["access_key"]}')
                except Exception as e:
                    print(f"Error processing photo {photo}: {e}")
                    continue

            if attachment:
                message_view = ms.get_message_view(','.join(attachment), user.get_card(), user)
                send_message(message_view)
            else:
                message_view = ms.get_message_view('', user.get_card(), user)
                send_message(message_view)
                print(f"No photos loaded for user {user.get_card().id}")

            if user.get_size_list_cards()-1 > next_index:
                try:
                    if not user.get_list_cards()[next_index+1].photos:
                        vk_srv.add_photos(user.get_list_cards()[next_index+1], token)
                except Exception as e:
                    print(f"Error preloading next card: {e}")
        else:
            main_menu(user)
    except Exception as e:
        print(f"Critical error in view_next_card: {e}")
        main_menu(user)

def view_back_card(user):
    try:
        next_index = user.get_index_view()
        next_index = next_index - 1
        if next_index < 0:
            next_index = 0
        user.set_index_view(next_index)

        photos = user.get_list_cards()[next_index].photos
        attachment = []
        for photo in photos:
            try:
                photo_struct = upload_photo(upload, photo)
                if photo_struct:
                    attachment.append(f'photo{photo_struct["owner_id"]}_{photo_struct["photo_id"]}_{photo_struct["access_key"]}')
            except Exception as e:
                print(f"Error processing photo {photo}: {e}")
                continue

        message_view = ms.get_message_view(','.join(attachment) if attachment else '', user.get_card(), user)
        send_message(message_view)
    except Exception as e:
        print(f"Error in view_back_card: {e}")
        main_menu(user)

def check_user(user_id):
    user = repository.get_user(user_id)
    if user is None:
        message_invitation = ms.get_message_invitation(user_id)
        send_message(message_invitation)
    else:
        main_menu(user)

    return user


def handle_criteria(user: User):
    if user.get_criteria() is None:
        criteria_dict = repository.open_criteria(user.get_user_id())
        user.set_criteria(criteria_dict)
    message_criteria = ms.get_message_criteria(user)
    if user.get_id_msg_edit_id() > -1:
        vk_session.method('messages.delete', {'message_ids': user.get_id_msg_edit_id(), 'delete_for_all': 1})
    return send_message(message_criteria)


def send_ask_edit_criteria(user, str_arg):
    user.set_step('criteria_'+str_arg)
    message_edit = ms.get_edit_message(user.get_user_id(), str_arg)
    send_message(message_edit)


def add_favorites(repository, user: User):
    repository.add_favorites(user)


def go_to_favorites(upload, user: User, repository):
    list_cards = repository.get_favorites(user.get_user_id())
    if not list_cards is None:
        user.set_list_cards(list_cards)
        user.set_index_view(-1)
        view_next_card(upload, user, vk_srv, token)
    else:
        message_error_search = ms.get_message_error_search(user.get_user_id())
        send_message(message_error_search)


def delete_from_list(user: User, repository):
    if len(user.get_list_cards()) > 0:
        if isinstance(user.get_list_cards()[0], CardFavorites):
            repository.delete_favorites(user.get_user_id(), user.get_card().id)
        elif isinstance(user.get_list_cards()[0], CardExceptions):
            repository.delete_exceptions(user.get_user_id(), user.get_card().id)

    user.delete_card()
    view_next_card(upload, user, vk_srv, token)


def save_criteria(user: User):
    repository.save_criteria(user)
    users_list[event.user_id].set_id_msg_edit_id(message_id)
    vk_session.method('messages.delete',
                      dict(message_ids=user.get_id_msg_edit_id(),
                           delete_for_all=1))
    message_done_registration = ms.get_message_done_registration(user.get_user_id())
    send_message(message_done_registration)
    main_menu(user)


def go_to_exceptions(upload, user: User, repository):
    list_cards = repository.get_exceptions(user.get_user_id())
    if not list_cards is None:
        user.set_list_cards(list_cards)
        user.set_index_view(-1)
        view_next_card(upload, user, vk_srv, token)
    else:
        message_error_search = ms.get_message_error_search(user.get_user_id())
        send_message(message_error_search)


def add_exceptions(repository, user: User):
    repository.add_exceptions(user)


if __name__ == '__main__':
    upload = VkUpload(vk_session)

    check_db = CheckDb()
    repository = Repository()

    print('Bot is running...')

    if check_db.check_db():
        print('Database is ready and initialized')
        print(f"Error status: {check_db.error}")
        
        users_list = repository.get_users()
        vk_srv = VKService()

        for event in VkLongPoll(vk_session).listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    text = event.text.lower()
                    payload = event.extra_values.get('payload')

                    if text == 'start':
                        handle_start(event.user_id)

                    elif text == 'хочу зарегистрироваться':
                        message_id = handle_registration(users_list[event.user_id])
                        users_list[event.user_id].set_id_msg_edit_id(message_id)

                    elif payload:
                        payload = json.loads(payload)
                        if payload.get('action_edit_anketa'):
                            str_arg = payload.get('action_edit_anketa')
                            send_ask_edit_anketa(users_list[event.user_id], str_arg)

                        elif payload.get('action_edit_criteria'):
                            str_arg = payload.get('action_edit_criteria')
                            send_ask_edit_criteria(users_list[event.user_id], str_arg)

                        elif payload.get('action_save_criteria'):
                            save_criteria(users_list[event.user_id])

                        elif payload.get('action_save_anketa'):
                            save_anketa(users_list[event.user_id])
                            message_id = handle_criteria(users_list[event.user_id])
                            users_list[event.user_id].set_id_msg_edit_id(message_id)

                        elif payload.get('action_cancel'):
                            action = payload.get('action_cancel')

                            if action == 'cancel_edit_anketa':
                                users_list[event.user_id].set_step(None)
                                message_id = handle_registration(users_list[event.user_id])
                                users_list[event.user_id].set_id_msg_edit_id(message_id)

                        elif payload.get('action_main_manu'):
                            action = payload.get('action_main_manu')

                            if action == 'go_to_main_manu':
                                main_menu(users_list[event.user_id])

                            elif action == 'find_users':
                                find_users(upload, users_list[event.user_id], vk_srv, token_api)

                            elif action == 'go_to_favorites':
                                go_to_favorites(upload, users_list[event.user_id], repository)

                            elif action == 'go_to_exception':
                                go_to_exceptions(upload, users_list[event.user_id], repository)

                            elif action == 'criteria':
                                message_id = handle_criteria(users_list[event.user_id])
                                users_list[event.user_id].set_id_msg_edit_id(message_id)

                        elif payload.get('action_view'):
                            action = payload.get('action_view')
                            if action == 'go_to_next':
                                view_next_card(upload, users_list[event.user_id], vk_srv, token_api)

                            elif action == 'go_to_back':
                                view_back_card(users_list[event.user_id])

                            elif action == 'add_favorites':
                                add_favorites(repository, users_list[event.user_id])

                            elif action == 'add_favorites':
                                add_favorites(repository, users_list[event.user_id])

                            elif action == 'delete_from_list':
                                delete_from_list(users_list[event.user_id], repository)

                            elif action == 'add_exceptions':
                                add_exceptions(repository, users_list[event.user_id])

                    elif not users_list.get(event.user_id) is None and not users_list[event.user_id].get_step() is None:
                        set_param(users_list[event.user_id], text)
                        if 'anketa' in users_list[event.user_id].get_step():
                            message_id = handle_registration(users_list[event.user_id])
                            users_list[event.user_id].set_id_msg_edit_id(message_id)
                        else:
                            message_id = handle_criteria(users_list[event.user_id])
                            users_list[event.user_id].set_id_msg_edit_id(message_id)

                    else:
                        if not event.user_id in users_list.keys():
                            user = check_user(event.user_id)
                            if user:
                                users_list[event.user_id] = user
            
            except Exception as e:
                print(f"Error processing event: {e}")
                error_message = {
                    'user_id': event.user_id,
                    'message': 'Произошла ошибка. Попробуйте еще раз.',
                    'random_id': get_random_id(),
                }
                send_message(error_message)
