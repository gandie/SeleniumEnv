'''
wrap firefox into asyncore server to send annoying alerts via telnet and other clients

Built from python2 asyncore example
'''

# BUILTIN
import time
import asyncore
import socket
import _thread
import socket

# SELENIUM
from selenium.webdriver import Firefox
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.command import Command


def browserClosed(driver):
    '''check driver for open window handles to stop main loop when broswer is
    closed'''
    try:
        print(driver.window_handles)
        return False
    except WebDriverException:
        return True


class EchoHandler(asyncore.dispatcher_with_send):

    '''handle incoming connections, read data and call JS in broswer using
    webdriver reference from server'''

    def __init__(self, sock, driver):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.driver = driver

    def browser_notify(self, msg):
        self.driver.execute_script(u'alert("{}");'.format(msg))
        print(msg)

    def browser_get(self, url):
        self.driver.execute_script(u'document.location.href = "{}";'.format(url))

    def browser_handle(self, text):
        '''parse incoming string and call matching method'''
        commands = {
            'say': self.browser_notify,
            'get': self.browser_get
        }

        for command in commands:
            if text.startswith(command):
                # put string after command into one argument and call method
                commands[command](''.join(text.split(' ', 1)[1:]))

    def handle_read(self):
        '''read bytes from socket, expect utf-8 and send to handler'''
        data = self.recv(8192)
        text = data.strip().decode('utf-8', 'ignore')
        if data:
            self.browser_handle(text)
            self.send(data)


class CommandServer(asyncore.dispatcher):

    def __init__(self, host, port, driver):
        asyncore.dispatcher.__init__(self)

        self.driver = driver
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        '''pass incoming connection and driver reference to handler'''
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            handler = EchoHandler(sock, self.driver)


def runserver(driver):
    server = CommandServer('0.0.0.0', 8080, driver)
    asyncore.loop()


def main():
    '''start browser and pass webdriver reference to server'''
    driver = Firefox()
    driver.get('https://google.de')

    # throw server on separate thread
    _thread.start_new_thread(runserver, (driver, ))

    # main loop: exit when browser is closed
    while True:
        time.sleep(1)
        if browserClosed(driver):
            break

    driver.quit()


if __name__ == '__main__':
    main()
