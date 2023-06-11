import time
import socket
import multiprocessing
from parser import parse_package

semop_window = multiprocessing.Semaphore(value=0)
game_params = None

class GameParams:
    def __init__(self, table: dict[str, list[int]], game_name: str, players_count: int):
        self.table = table
        self.game_name = game_name
        self.players_count = players_count
        self.cur_players = 0
        self.players = ['' for i in range(players_count)]
    
    def set_player(self, name):
        self.players[self.cur_players] = name

class Player:
    semop_answer = multiprocessing.Semaphore(value=0)
    semop_request = multiprocessing.Semaphore(value=0)
    fin_semop = multiprocessing.Semaphore(value=0)
    answer = ''
    request = ''
    waiting = False


    def my_read(self, sock):
        """Функция, читающая из сокета."""
        time.sleep(0.1)
        while True:
            res = sock.recv(4096)
            res = res.decode()
            if res == 'quit':
                print("READER DONE")
                sock.send('bye'.encode())
                self.fin_semop.release()
                break

            answer = res
            self.semop_answer.release()
            waiting = False
        return True

    def my_write(self):
        """Функция, пишущая в сокет."""
        global request
        while True:
            self.semop_request.acquire()
            self.sock.send(request)
            if request == b"'quit'\n":
                print("WRITER DONE")
                self.fin_semop.release()
                break
        return True

    def play(self, game_name, players_count):
        pass


    def __init__(self, game_name, password, package_path, players_count):
        global game_params
        package = parse_package(package_path)
        cur_round = package.rounds[0]
        themes = cur_round.themes
        cur_table = {th: [q for q in themes[th].questions] for th in themes}
        game_params = GameParams(cur_table, game_name, players_count)
        print("WTF")
        semop_window.release()
        self.name = 'master_oogway'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 1337))
        self.sock.send((f"{self.name}\n").encode())
        self.res = self.sock.recv(4096)

        if self.res == b'hello':
            self.sock.send(password.encode())
            self.res = self.sock.recv(4096)
            reader = multiprocessing.Process(target=self.my_read, args=(self.sock,))
            writer = multiprocessing.Process(target=self.my_write, args=(self.sock,))

            reader.start()
            writer.start()
        else:
            print(f"Nickname {self.name} is allready taken, please log in with another nickname")
            self.sock.close()
        self.play(game_name, package_path, players_count)

def master_starter(game_name, password, package_path, players_count):
    Player(game_name, password, package_path, players_count)

##master_starter('game_name', 'password', 'Game.siq', 3)