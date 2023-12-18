import sublime
import sublime_plugin
import threading
import os
import socket
import requests
import getpass
from hashlib import sha224
from time import sleep
__version__ = '1.8'
settings_file = 'WorkX3.sublime-settings'
settings = {}
PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))


hostkey = sha224(("%s %s" % (getpass.getuser(), socket.gethostname())).encode()).hexdigest()

# Log Levels
DEBUG = 'DEBUG'
INFO = 'INFO'
WARNING = 'WARNING'
ERROR = 'ERROR'


def log(lvl, message, *args, **kwargs):
    try:
        if lvl == DEBUG and not settings.get('debug'):
            return
        msg = message
        if len(args) > 0:
            msg = message.format(*args)
        elif len(kwargs) > 0:
            msg = message.format(**kwargs)
        print('[WorkBot] [{lvl}] {msg}'.format(lvl=lvl, msg=msg))
    except RuntimeError:
        sublime.set_timeout(lambda: log(lvl, message, *args, **kwargs), 0)


class Listener(threading.Thread):
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)

    def work(self, item):
        if isinstance(item['data'], bytes):
            print(item['data'].decode('utf-8'))
        # print(item['channel'], ":", item['data'])

    def run(self):
        for item in self.pubsub.listen():
            if item['data'] == b"KILL":
                self.pubsub.unsubscribe()
                log(WARNING, 'Killed!')
                print(self, "unsubscribed and finished")
                break
            else:
                self.work(item)


class WorkSendToBotCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sublime.active_window().run_command("show_panel", {"panel": "console", "toggle": True})

        for selection in self.view.sel():
            # if the user didn't select anything, search the currently highlighted word
            if selection.empty():
                text = self.view.word(selection)

            text = self.view.substr(selection)

            params = dict(
                user=hostkey
            )
            for riga in text.splitlines():
                if riga.strip() == '':
                    continue
                params['text'] = riga.strip()
                r = requests.post(settings.get("host"), params, timeout=60)

                if r.status_code == requests.codes.ok:
                    for line in r.text.splitlines():
                        print(line)
                else:
                    log(ERROR, 'Errore invio a Work, riprovare')
                    log(ERROR, r.text)
                    sleep(1)
                sleep(0.5)





def plugin_loaded():
    global settings
    log(INFO, 'Initializing MecomWork plugin v%s' % __version__)
    settings = sublime.load_settings(settings_file)
