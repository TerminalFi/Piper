
# Inspired by Vim
# ! Code from @OdatNurd
# * Modifications by Terminal

import sublime
import sublime_plugin

from shutil import which
from subprocess import run
import time
import shlex
from datetime import datetime


def command_path(cmd: str) -> str:
    return which(cmd)


def verify_shell_cmd(cmd: str) -> bool:
    return bool(which(cmd))


def execute_with_stdin(cmd, flags, shell, text):
    before = time.perf_counter()
    complete_command = [command_path(cmd)]
    if flags:
        complete_command.extend(shlex.split(flags))

    p = run(complete_command, capture_output=True,
            input=text, encoding='utf-8')
    after = time.perf_counter()
    return (p, after - before)


class CommandInputHandler(sublime_plugin.TextInputHandler):
    def name(self):
        return "command"

    def placeholder(self):
        return "Command"

    def initial_text(self):
        return "echo"

    def preview(self, command):
        return sublime.Html(f'<strong>Command:</strong> <em>{command_path(command)}</em>')

    def validate(self, command):
        if verify_shell_cmd(command):
            return True
        return False

    def next_input(self, command):
        return FlagInputHandler(command)


class FlagInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, args):
        self.args = args

    def name(self):
        return "flags"

    def placeholder(self):
        return "Flags"

    def validate(self, flags):
        return True

    def preview(self, flags):
        return sublime.Html(f'<strong>Command:</strong> {self.args["command"]} {flags}')


class PipeVimCommand(sublime_plugin.TextCommand):
    def run(self, edit, command, flags: str = ''):
        if not all(self.view.sel()):
            regions = [sublime.Region(0, self.view.size())]
        else:
            regions = self.view.sel()

        if not command:
            raise ValueError("shell_cmd or cmd is required")

        if command and not isinstance(command, str):
            raise ValueError("shell_cmd must be a string")

        if not verify_shell_cmd(command):
            raise ValueError("command not recognized")

        failures = False
        start = time.perf_counter()
        logs = list()

        def log(message):
            nonlocal logs
            log_text = str(datetime.now()) + ' ' + message
            logs.append(log_text)

        text = ' '.join([self.view.substr(region) for region in regions])
        p, time_elapsed = execute_with_stdin(command, flags, False, text)

        log(f'command "{command!r}" executed with return code {p.returncode} in {time_elapsed * 1000:.3f}ms')
        result_view = self.view.window().new_file()
        result_view.set_scratch(True)
        if p.returncode == 0:
            result_view.insert(edit, 0, p.stdout)
        else:
            failures = True
            result_view.insert(edit, 0, p.stderr)

    def input(self, args):
        return CommandInputHandler()
