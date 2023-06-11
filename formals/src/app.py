import kivy

kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from server import server_starter
import multiprocessing
import threading
import time
import socket
import shlex

# сокет
sock = None
# словарь с виджетами
widgets = None
# параметры игры, которые приедут от сервера
game_params = None
# количество очков за выбранный вопрос
active_score = 0
# количество игроков, которые уже получили отказ (для ведущего)
reject_counts = 0
# флаг, определяющий есть в игре активный вопрос или нет (для игрока)
flag_passive = True
red = [1, 0, 0, 1] 
green = [0, 1, 0, 1] 
blue = [0, 0, 1, 1] 
purple = [1, 0, 1, 1]
white = [1, 1, 1, 1]


class MainMenu(Screen):
    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(Label(text="Своя игра", font_size=40))

        self.buttons = [
            ("Создать игру", "create_game"),
            ("Присоединиться к игре", "join_game"),
            ("Правила", "rules"),
            ("Выход", "exit"),
        ]

        for text, screen_name in self.buttons:
            button = Button(
                text=text,
                size_hint=(1, 0.2),
                on_release=self.switch_to_screen(screen_name),
            )
            self.layout.add_widget(button)

        self.add_widget(self.layout)

    def switch_to_screen(self, screen_name):
        def switch(*args):
            if screen_name == "exit":
                App.get_running_app().stop()
            else:
                self.manager.current = screen_name

        return switch


class CreateGame(Screen):
    def __init__(self, **kwargs):
        super(CreateGame, self).__init__(**kwargs)
        self.layout = GridLayout(cols=2, padding=10, spacing=10)

        self.layout.add_widget(Label(text="Название игры:", font_size=20))
        self.game_name = TextInput(multiline=False)
        self.layout.add_widget(self.game_name)

        self.layout.add_widget(Label(text="Пароль:", font_size=20))
        self.password = TextInput(multiline=False, password=True)
        self.layout.add_widget(self.password)

        self.layout.add_widget(Label(text="Количество игроков:", font_size=20))
        self.players_slider = Slider(min=2, max=5, value=2, step=1)
        self.layout.add_widget(self.players_slider)

        self.layout.add_widget(Label(text="Прикрепить пакет:", font_size=20))
        self.package_path = TextInput(multiline=False)
        self.layout.add_widget(self.package_path)

        self.create_room_button = Button(
            text="Создать комнату", on_release=self.create_room
        )
        self.layout.add_widget(self.create_room_button)
        self.layout.add_widget(Label())

        self.add_widget(self.layout)

    def create_room(self, *args):
        game_name = self.game_name.text
        password = self.password.text
        players_count = int(self.players_slider.value)
        package_path = self.package_path.text


        # создание комнаты
        print("Создание комнаты")
        print(f"Название игры: {game_name}")
        print(f"Пароль: {password}")
        print(f"Количество игроков: {players_count}")
        print(f"Путь к пакету: {package_path}")

        print("HELLO THERE")
        server_thread = multiprocessing.Process(target = server_starter, args=(game_name, password, package_path, players_count))
        server_thread.start()
        print("HELLO PUPPY")
        time.sleep(0.1)
        self.manager.add_widget(Game(True, password, "master_oogway", name="game"))       
        # Переход на экран игры после создания комнаты
        self.manager.current = "game"


class JoinGame(Screen):
    def __init__(self, **kwargs):
        super(JoinGame, self).__init__(**kwargs)
        self.layout = GridLayout(cols=2, padding=10, spacing=10)

        self.layout.add_widget(Label(text="Название игры:", font_size=20))
        self.game_name = TextInput(multiline=False)
        self.layout.add_widget(self.game_name)

        self.layout.add_widget(Label(text="Пароль:", font_size=20))
        self.password = TextInput(multiline=False, password=True)
        self.layout.add_widget(self.password)

        self.layout.add_widget(Label(text="Ваше имя:", font_size=20))
        self.player_name = TextInput(multiline=False)
        self.layout.add_widget(self.player_name)

        self.join_button = Button(text="Присоединиться", on_release=self.join_game)
        self.layout.add_widget(self.join_button)
        self.layout.add_widget(Label())

        self.add_widget(self.layout)

    def join_game(self, *args):
        game_name = self.game_name.text
        password = self.password.text
        player_name = self.player_name.text

        print("Присоединение к игре")
        print(f"Название игры: {game_name}")
        print(f"Пароль: {password}")
        print(f"Ваше имя: {player_name}")

        self.manager.add_widget(Game(False, password, player_name, name="game"))
        # Переход на экран игры после присоединения к комнате
        self.manager.current = "game"


def empty_func(*args):
    """пустышка: ставится в обработчик кнопки, если ее надо "деактивировать"""
    pass

def choose_button(th, q):
    """генератор функций для кнопок с ценами вопросов"""
    def func(arg):
        # это будет происходить, если нажать на кнопку
        # p.s. flag_passive=True если сейчас нет активного вопроса и False иначе
        global sock, flag_passive
        if flag_passive:
            request = f"choose '{th}' {q}"
            print(f"CLIENT {request}")
            sock.send((request+'\n').encode())
    return func


def answer_button(player_name):
    """генератор функций для кнопок ответа пользователя"""
    global widgets
    def func():
        # это будет происходить, если нажать на кнопку
        global sock
        request = f"answer {player_name} {widgets['text_fields']['answer'].text}"
        widgets['text_fields']['answer'].background_color = (0, 0, 0, 1/255)
        widgets['text_fields']['answer'].text = ''
        widgets['buttons']['answer'].background_color = red
        widgets['buttons']['answer'].text = ''
        widgets['text_fields']['answer'].readonly = True
        new_func = empty_func
        widgets['buttons']['answer'].on_release = new_func
        sock.send((request+'\n').encode())
    return func


def reject_button(player_name):
    """Генератор функции для кнопки 'отказа' у ведущего"""
    global widgets
    def func():
        # это будет происходить, если нажать на кнопку
        global sock, reject_counts
        reject_counts += 1
        widgets['labels']['curr_ans'].text = ""
        widgets['buttons']['accept'].on_release = empty_func
        widgets['buttons']['accept'].background_color = red
        widgets['buttons']['reject'].on_release = empty_func
        widgets['buttons']['reject'].background_color = red
        request = f"verdict reject {player_name} {reject_counts}"
        print(f"MASTER {request}")
        sock.send((request+'\n').encode())
    return func


def accept_button(player_name):
    """Генератор функции для кнопки 'принятия' у ведущего"""
    global widgets
    def func():
        # это будет происходить, если нажать на кнопку
        global sock
        widgets['labels']['curr_ans'].text = ""
        widgets['buttons']['accept'].on_release = empty_func
        widgets['buttons']['accept'].background_color = red
        widgets['buttons']['reject'].on_release = empty_func
        widgets['buttons']['reject'].background_color = red
        request = f"verdict accept {player_name}"
        print(f"MASTER {request}")
        sock.send((request+'\n').encode())
    return func


def client_read(player_name):
    """Функция, читающая из сокета и меняющая интерфейс
      в соответсвии с получаемыми сообщениями (для обычных игроков)"""
    global sock, widgets, game_params, active_score, flag_passive
    time.sleep(0.1)
    while True:
        # получаем сообщение и разбиавем его на части
        res = sock.recv(4096)
        res = res.decode()
        res = shlex.split(res)
        print(f"READER HAS GOT {res}")
        match res[0]:
            case "choose":
            # сообщение от сервера начинается с choose, если кто-то выбрал кнопку с ценой вопроса
            # соответсвенно далее - изменения интерфейса после этого события
            # общий формат сообщения от сервера следующий:
            # choose - res[0] <theme> - res[1] <question_cost> - res[2]
                flag_passive = False
                print("CHOOSE", res)
                active_score = res[2]
                widgets['buttons']['questions'][res[1]][res[2]].text = ''
                widgets['buttons']['questions'][res[1]][res[2]].on_release = empty_func
                widgets['text_fields']['answer'].background_color = white
                widgets['text_fields']['answer'].readonly = False
                widgets['buttons']['answer'].background_color = green
                widgets['buttons']['answer'].color = 'black'
                widgets['buttons']['answer'].text = 'Ответить'
                widgets['buttons']['answer'].font_size = 40
                new_func = answer_button(player_name)
                widgets['buttons']['answer'].on_release = new_func
                # Локаль
                widgets['labels']['q_label'].text = f"ТЕКСТ ВОПРОСА: {game_params['table'][res[1]][res[2]][0]}"
                widgets['labels']['q_label'].text_size = widgets['labels']['q_label'].size
                widgets['labels']['q_label'].font_size = 20
                # Локаль
                widgets['labels']['info'].text = f"info: ТЕКУЩИЙ ВОПРОС: {[res[1]]}, {[res[2]]}"
                widgets['labels']['info'].text_size = widgets['labels']['info'].size
            case "answer":
            # сообщение от сервера начинается с answer, если кто-то из игроков отослал ответ ведущему
            # общий формат сообщения от сервера следующий:
            # answer - res[0] <имя ответчика> - res[1] <сам по себе ответ> - res[2]
                if res[1] != player_name:
                    widgets['buttons']['answer'].background_color = red
                    widgets['buttons']['answer'].on_release = empty_func
                    # Локаль
                    widgets['labels']['info'].text = f"Игрок {res[1]} ответил: {res[2]}"
                    widgets['labels']['info'].text_size = widgets['labels']['info'].size
            case "verdict":
            # сообщение от сервера начинается с verdict, если ведущий нажал на кнопку принять или отклонить
            # общий формат сообщения от сервера следующий:
            # verdict - res[0] <accept/reject> - res[1] <имя игрока> - res[2] 
                if res[1] == 'accept':
                    flag_passive = True
                    widgets['labels']['q_label'].text = ""
                    if res[2] == player_name:
                        # Локаль
                        widgets['labels']['info'].text = "info: Ваш ответ правильный"
                    else:
                        # Локаль
                        widgets['labels']['info'].text = f"info: Игрок {res[2]} ответил правильно"
                    new_score = int(widgets['labels']['scores'][res[2]].text) + int(active_score)
                    widgets['labels']['scores'][res[2]].text = str(new_score)
                    widgets['text_fields']['answer'].background_color = (0, 0, 0, 1/255)
                    widgets['text_fields']['answer'].text = ''
                    widgets['buttons']['answer'].background_color = red
                    widgets['buttons']['answer'].text = ''
                    widgets['text_fields']['answer'].readonly = True
                    new_func = empty_func
                    widgets['buttons']['answer'].on_release = new_func
                    widgets['labels']['q_label'].text = ""
                else:
                    if res[2] == player_name:
                        # Локаль
                        widgets['labels']['info'].text = "info: Ваш ответ неправтльный"
                    else:
                        # Локаль
                        widgets['labels']['info'].text = f"info: Игрок {res[2]} ответил неправильно"
                        if widgets['buttons']['answer'] != '':
                            widgets['buttons']['answer'].background_color = green
                            new_func = answer_button(player_name)
                            widgets['buttons']['answer'].on_release = new_func
                    print(f"REJECT FINISH {game_params['cur_players'].index(None)}, {int(res[3])}")
                    if None in game_params['cur_players']:
                        check_ind = game_params['cur_players'].index(None)-1
                    else:
                        check_ind = game_params['players_count']-1
                    # res[3] есть только в случае rejecta и в нем 
                    # содержится счетчик reject_counts от сервера
                    if check_ind == int(res[3]):
                        flag_passive = True
                        widgets['labels']['q_label'].text = ""
                        widgets['text_fields']['answer'].background_color = (0, 0, 0, 1/255)
                        widgets['text_fields']['answer'].text = ''
                        widgets['buttons']['answer'].background_color = red
                        widgets['buttons']['answer'].text = ''
                        widgets['text_fields']['answer'].readonly = True
                        new_func = empty_func
                        widgets['buttons']['answer'].on_release = new_func
                    
            case "connect":
            # сообщение от сервера начинается с connect, если кто-то подключился
            # общий формат сообщения от сервера следующий:
            # connect- res[0] <Имя игрока> - res[1] 
                # Локаль
                widgets['labels']['info'].text = f"info: Игрок {res[1]} подключился"
                widgets['labels']['info'].text_size = widgets['labels']['info'].size
                free_place = game_params['cur_players'].index(None)
                game_params['cur_players'][free_place] = res[1]
                widgets['labels']['players'][f"player_{free_place}"].text = res[1]
                widgets['labels']['players'][res[1]] = widgets['labels']['players'][f"player_{free_place}"]
                widgets['labels']['scores'][res[1]] = widgets['labels']['scores'][f"player_{free_place}"]
    return True


# ведущему приезжают такие же запросы от сервера, что и клиенту
def master_read():
    global sock, widgets, game_params, reject_counts
    time.sleep(0.1)
    while True:
        res = sock.recv(4096)
        res = res.decode()
        res = shlex.split(res)
        print(f"READER HAS GOT {res}")
        match res[0]:
            case "choose":
                reject_counts = 0
                active_score = res[2]
                print("CHOOSE", res)
                widgets['buttons']['questions'][res[1]][res[2]].text = ''
                # Локаль
                widgets['labels']['q_label'].text = f"ТЕКСТ ВОПРОСА: {game_params['table'][res[1]][res[2]][0]}"
                widgets['labels']['q_label'].text_size = widgets['labels']['q_label'].size
                widgets['labels']['q_label'].font_size = 20
                # Локаль
                widgets['labels']['right_ans'].text = f"Правильный ответ: {game_params['table'][res[1]][res[2]][1]}"
                widgets['labels']['right_ans'].text_size = widgets['labels']['right_ans'].size
                # Локаль
                widgets['labels']['info'].text = f"info: ТЕКУЩИЙ ВОПРОС: {[res[1]]}, {[res[2]]}"
                widgets['labels']['info'].text_size = widgets['labels']['info'].size
            case "answer":
                # Локаль
                widgets['labels']['curr_ans'].text = f"Ответ игрока {res[1]}: {res[2]}"
                widgets['labels']['curr_ans'].text_size = widgets['labels']['curr_ans'].size
                new_func = accept_button(res[1])
                widgets['buttons']['accept'].on_release = new_func
                widgets['buttons']['accept'].background_color = green
                new_func = reject_button(res[1])
                widgets['buttons']['reject'].on_release = new_func
                widgets['buttons']['reject'].background_color = green
            case "verdict":
                if res[1] == 'accept':
                    widgets['labels']['q_label'].text = ""
                    widgets['labels']['right_ans'].text = ""
                    # Локаль
                    widgets['labels']['info'].text = f"info: Игрок {res[2]} ответил правильно"
                    widgets['labels']['info'].text_size = widgets['labels']['info'].size
                    new_score = int(widgets['labels']['scores'][res[2]].text) + int(active_score)
                    widgets['labels']['scores'][res[2]].text = str(new_score)
                else:
                    # Локаль
                    widgets['labels']['info'].text = f"info: Игрок {res[2]} ответил неправильно"
                    widgets['labels']['info'].text_size = widgets['labels']['info'].size
                    if None in game_params['cur_players']:
                        check_ind = game_params['cur_players'].index(None)-1
                    else:
                        check_ind = game_params['players_count']-1
                    if check_ind == int(res[3]):
                        widgets['labels']['q_label'].text = ""
                        widgets['labels']['right_ans'].text = ""
            case "connect":
                # Локаль
                widgets['labels']['info'].text = f"info: Игрок {res[1]} подключился"
                widgets['labels']['info'].text_size = widgets['labels']['info'].size
                free_place = game_params['cur_players'].index(None)
                game_params['cur_players'][free_place] = res[1]
                widgets['labels']['players'][f"player_{free_place}"].text = res[1]
                widgets['labels']['players'][res[1]] = widgets['labels']['players'][f"player_{free_place}"]
                widgets['labels']['scores'][res[1]] = widgets['labels']['scores'][f"player_{free_place}"]


class Game(Screen): 
    def __init__(self, master, password, player_name, **kwargs):
        global sock, widgets, game_params
        # Установка соединения с сервером
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 1321))
        sock.send((f"{player_name}\n").encode())
        res = sock.recv(4096)
        print(f"RECEIVED {res}")
        print(password.encode())
        sock.send((password + '\n').encode())
        res = sock.recv(4096)
        # Если пароль неверен, то здесь в res будет "sorry" вместо "hello"
        print(f"RECEIVED {res}")
        print("Starting reader")
        print("Started reader")
        sock.send(('give me a pack' + '\n').encode())
        # Получаем от сервера строку с описанем игры
        game_params = eval(sock.recv(8192).decode())
        game_params['cur_players'] = []

        super(Game, self).__init__(**kwargs)
        # присваиваме ГЛОБАЛЬНОЙ переменной widgets шаблонный вид.
        # Далее, перед добавлением любого виджета на какой-либо layout 
        # он будет добавляться в какую-то ячейку словаря widgets
        widgets = {'buttons': {}, 'labels': {}, 'text_fields': {}, 'layouts': {}}
        layout = BoxLayout(orientation='vertical')
        # текущий список игроков, включая ведущего и нас
        players = game_params["players"]
        # колво игроков
        cur_players = len(players)
        # максимально допустимое число игроков (указано при создании пати)
        players_count = game_params["players_count"]
        players_layout = GridLayout(rows=2, cols=players_count, spacing=10)
        for p in range(players_count):
            # если текущий индекс есть в фактическом массиве игроков,
            # то берем имя от туда, иначе шаблон: "player_i"
            if p < cur_players:
                cur_text = players[p]
            else:
                cur_text = f"player_{p}"
            # Лейблы с именами игроков
            cur_label = Label(text=cur_text, font_size=20)
            widgets['labels'].setdefault('players', {})
            widgets['labels']['players'][cur_text] = cur_label
            players_layout.add_widget(cur_label) #name
        for p in range(players_count):
            # То же самое, что и предыдущий виджет, но для лейблов с очками
            if p < cur_players:
                cur_text = players[p]
                game_params["cur_players"].append(cur_text)
            else:
                cur_text = f"player_{p}"
                game_params["cur_players"].append(None)
            cur_label = Label(text='0', font_size=20)
            widgets['labels'].setdefault('scores', {})
            widgets['labels']['scores'][cur_text] = cur_label
            players_layout.add_widget(cur_label) #score
            
        game_field = GridLayout(cols=2, padding=10, spacing=10)
        q_table = GridLayout(cols=game_params['table_size'][1]+1, padding=10, spacing=10)
        # Локаль
        q_label = Label(text='Ищи вопрос тут', font_size=40)
        for th in game_params['table']:
            # Лейблы с названиями тем
            cur_label = Label(text=th, font_size=20)
            cur_label.text_size = cur_label.size
            widgets['buttons'].setdefault('questions', {})
            widgets['labels'].setdefault('themes', {})
            widgets['labels']['themes'][th] = cur_label
            q_table.add_widget(cur_label)
            for q in game_params['table'][th]:
                if master:
                    but_func = empty_func
                else:
                    but_func = choose_button(th, q)
                # Кнопки с ценами вопросов
                button = Button(
                    text=str(q),
                    size_hint=(1, 0.2),
                    on_release=but_func,
                )
                widgets['buttons']['questions'].setdefault(th, {})
                widgets['buttons']['questions'][th][str(q)] = button
                q_table.add_widget(button)
        widgets['labels']['q_label'] = q_label
        widgets['layouts']['table'] = q_table
        game_field.add_widget(q_table)
        game_field.add_widget(q_label)
        
        gamer_tools = BoxLayout(orientation='horizontal')
        # Лейбл для вывода сообщений через "info:"
        info = Label(text='info:', size=(10,10))
        widgets['labels']['info'] = info
        gamer_tools.add_widget(info)
        
        if master:
            # Для окна ведущего
            answers = BoxLayout(orientation='vertical')
            # Лейбл на котором будет отображаться верный ответ
            # Локаль
            right_ans = Label(text='Верный ответ:')
            widgets['labels']['right_ans'] = right_ans
            answers.add_widget(right_ans)
            # Лейбл на котором будет отображаться текущий ответ игрока
            # Локаль
            curr_ans = Label(text='Ответ игрока')
            widgets['labels']['curr_ans'] = curr_ans
            answers.add_widget(curr_ans)
            gamer_tools.add_widget(answers)
            
            buttons = BoxLayout(orientation='vertical')
            # Кнопка для принятия ответа
            # Локаль
            button_accept = Button(text='Принять', background_color = red)
            widgets['buttons']['accept'] = button_accept
            buttons.add_widget(button_accept)
            # Кнопка для отклонения ответа
            # Локаль
            button_reject = Button(text='Отклонить', background_color = red)
            widgets['buttons']['reject'] = button_reject
            buttons.add_widget(button_reject)
            gamer_tools.add_widget(buttons)
        else:
            #Для окна игрока
            # кнопка для отправки ответа
            ans_button = Button(text='', background_color = red)
            widgets['buttons']['answer'] = ans_button
            gamer_tools.add_widget(ans_button)
            # Поле для ввода ответа
            ans_field = TextInput(background_color=(0, 0, 0, 1/255), readonly=True)
            widgets['text_fields']['answer'] = ans_field
            gamer_tools.add_widget(ans_field)
        
        layout.add_widget(players_layout)
        layout.add_widget(game_field)
        layout.add_widget(gamer_tools)
        widgets['layouts']['players'] = players_layout
        widgets['layouts']['game'] = game_field
        widgets['layouts']['tools'] = gamer_tools
        widgets['layouts']['main'] = layout
        self.add_widget(layout)
        # для ведущего своя функция-reader
        if master:
            reader_thread = threading.Thread(target = master_read, daemon = True)
        else:
            reader_thread = threading.Thread(target = client_read, args = (player_name,), daemon = True)
        reader_thread.start() 


class Rules(Screen):
    def __init__(self, **kwargs):
        super(Rules, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.rules_label = Label(text="Правила и инструкции", font_size=30)
        self.layout.add_widget(self.rules_label)

        self.rules_text = """Здесь вы можете добавить инструкции."""

        self.rules = Label(
            text=self.rules_text, font_size=18, halign="left", valign="top"
        )
        self.rules.text_size = self.rules.size
        self.layout.add_widget(self.rules)

        self.back_button = Button(
            text="Назад", size_hint=(1, 0.2), on_release=self.back_to_main_menu
        )
        self.layout.add_widget(self.back_button)

        self.add_widget(self.layout)

    def back_to_main_menu(self, *args):
        self.manager.current = "main_menu"


class MyApp(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MainMenu(name="main_menu"))
        screen_manager.add_widget(CreateGame(name="create_game"))
        screen_manager.add_widget(JoinGame(name="join_game"))
        screen_manager.add_widget(Rules(name="rules"))
        ## screen_manager.add_widget(Game(name="game"))

        return screen_manager

def main():
    MyApp().run()
