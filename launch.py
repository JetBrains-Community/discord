"""
Virtualenv and launcher script rolled into one.

This is copied in part from https://docs.python.org/3/library/venv.html.
"""

import os.path
import sys
import time
import venv
from subprocess import Popen

win32 = os.name == 'nt'


class ExtendedEnvBuilder(venv.EnvBuilder):
    def post_setup(self, context):
        # install the bot-specific packages
        if win32:
            pip = "./venv/Scripts/pip.exe"
        else:
            pip = "./venv/bin/pip"
        proc = Popen([pip, "install", "-U", "-r", "requirements.txt"])
        proc.communicate()


def run():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    if win32:
        path = "./venv/Scripts/python.exe"
    else:
        path = "venv/bin/python3"

    print("\n\nSpawning (w/ autoreboot): {} {}\n\n".format(os.path.abspath(path), "bot.py"))
    proc = Popen([os.path.abspath(path), "bot.py", *sys.argv[1:]],
                 cwd=os.getcwd(), env=env)

    result = proc.communicate()
    print("\n\nBot died, restarting.")
    time.sleep(1)


if __name__ == "__main__":
    print("Need to create environment:", not os.path.exists("./venv"))
    if not os.path.exists("./venv"):
        print("Creating a new virtual environment...")
        builder = ExtendedEnvBuilder(with_pip=True)
        builder.create("./venv")

    if win32:
        while True:
            try:
                run()
            except (KeyboardInterrupt, EOFError):
                break
    else:
        run()

    print("Bye!")
