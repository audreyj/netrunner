import sys, socket
import connection

""" This demonstrates a two-player game to be played from two different PCs
    connected to a local network (LAN) or even via the Internet. The code
    requeres access to the module 'connection' for handling of generel server
    and client code.

    Data send between the two players must be 'string'-format.
"""

#####################################################################
## --- NEXT 4 LINES MUST BE MODIFIED TO MATCH ACTUAL SITUATION --- ##
MY_SERVER_HOST = '192.168.1.59'
MY_SERVER_PORT = 9999
OTHER_HOST = '192.168.1.18'
OTHER_PORT = 9992
#####################################################################

class Player():
    def __init__(self, pos):
        pass


class Player_1(Player):
    def __init__(self, pos=(200, 200)):
        super().__init__(pos)


class Player_2(Player):
    def __init__(self, pos=(400, 200)):
        super().__init__(pos)


def ip_value(ip):
    """ ip_value returns ip-string as integer """
    return int(''.join([x.rjust(3, '0') for x in ip.split('.')]))


def define_players():
    if ip_value(MY_SERVER_HOST) > ip_value(OTHER_HOST):
        me = Player_1()
        enemy = Player_2()
    else:
        me = Player_2()
        enemy = Player_1()
    return me, enemy


def event_handling():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            server.shutdown()
            pygame.quit()
            sys.exit()


def get_input():
    input('test: ')


def data_transfer():
    me_data = me.make_data_package()
    connection.send(me_data, OTHER_HOST, OTHER_PORT)  # the send code
    enemy_data = server.receive()  # the receive code


def update_screen():
    print('test')


me, enemy = define_players()
server = connection.Server(MY_SERVER_HOST, MY_SERVER_PORT)

while True:
    update_screen()
    event_handling()
    get_input()
    data_transfer()
