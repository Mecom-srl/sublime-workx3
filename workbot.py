try:
    import sublime
    import sublime_plugin
except ImportError:
    pass

import threading
import os
import socket
import requests
import getpass
from hashlib import sha224
from time import sleep

# disable ssl warning
requests.packages.urllib3.disable_warnings()

__version__ = '2.3'
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


# classe thread che fa le richieste via http
class WorkBotThread(threading.Thread):
    def __init__(self, text):
        self.text = text
        threading.Thread.__init__(self)

    def run(self):
        params = dict(
            user=hostkey
        )
        for riga in self.text.splitlines():
            if riga.strip() == '':
                continue
            params['text'] = riga.strip()
            r = requests.post(settings.get("host"), params, timeout=60, verify=False)

            if r.status_code == requests.codes.ok:
                for line in r.text.splitlines():
                    print(line)
            else:
                log(ERROR, 'Errore invio a Work, riprovare')
                log(ERROR, r.text)
                sleep(3)
            sleep(1)


class WorkSendToBotCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sublime.active_window().run_command("show_panel", {"panel": "console", "toggle": True})

        for selection in self.view.sel():
            # if the user didn't select anything, search the currently highlighted word
            if selection.empty():
                text = self.view.word(selection)
            text = self.view.substr(selection)
            log(INFO, 'Invio comandi a Work ...')
            WorkBotThread(text).start()


def plugin_loaded():
    global settings
    log(INFO, 'Initializing MecomWork plugin v%s' % __version__)
    settings = sublime.load_settings(settings_file)