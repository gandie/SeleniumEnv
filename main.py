'''
wrap firefox into asyncore server to send annoying alerts via telnet and other clients

Built from python2 asyncore example
'''

from selenium.webdriver import Firefox
import time
import asyncore
import socket
import _thread
from selenium.common.exceptions import WebDriverException


import socket

from selenium.webdriver.remote.command import Command


def get_status(driver):
    try:
        print(driver.window_handles)
        return True
    except WebDriverException:
        return False


class EchoHandler(asyncore.dispatcher_with_send):

    def __init__(self, sock, driver):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.driver = driver

    def browser_notify(self, msg):
        self.driver.execute_script(u'alert("{}");'.format(msg))
        print(msg)

    def browser_get(self, url):
        self.driver.execute_script(u'document.location.href = "{}";'.format(url))

    def browser_handle(self, text):
        commands = {
            'say': self.browser_notify,
            'get': self.browser_get
        }

        for command in commands:
            if text.startswith(command):
                commands[command](''.join(text.split(' ', 1)[1:]))

    def handle_read(self):
        data = self.recv(8192)
        text = data.strip().decode('utf-8', 'ignore')
        if data:
            self.browser_handle(text)
            self.send(data)


class EchoServer(asyncore.dispatcher):

    def __init__(self, host, port, driver):
        asyncore.dispatcher.__init__(self)

        self.driver = driver

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            handler = EchoHandler(sock, self.driver)


def runserver(driver):
    server = EchoServer('localhost', 8080, driver)
    asyncore.loop()


driver = Firefox()
driver.get('https://google.de')

_thread.start_new_thread(runserver, (driver, ))

while True:
    time.sleep(1)
    if not get_status(driver):
        break

driver.quit()
