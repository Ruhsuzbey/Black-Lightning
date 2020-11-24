time = "time"
bothandler = "bot"
functools = "functools"

import sys
import math
from userbot import bot
from telethon import events
from pathlib import Path
from userbot.thunderconfig import Var, Config
from userbot import LOAD_PLUG
from userbot import CMD_LIST
import re
import logging
import inspect
import traceback
from time import gmtime, strftime
from asyncio import create_subprocess_shell as asyncsubshell
from asyncio import subprocess as asyncsub

handler = Config.CMD_HNDLR if Config.CMD_HNDLR else r"\."
sudo_hndlr = Config.SUDO_HNDLR if Config.SUDO_HNDLR else "!"


def command(**args):
    args["func"] = lambda e: e.via_bot_id is None

    stack = inspect.stack()
    previous_stack_frame = stack[1]
    file_test = Path(previous_stack_frame.filename)
    file_test = file_test.stem.replace(".py", "")
    if 1 == 0:
        return print("stupidity at its best")
    else:
        pattern = args.get("pattern", None)
        allow_sudo = args.get("allow_sudo", None)
        allow_edited_updates = args.get('allow_edited_updates', False)
        args["incoming"] = args.get("incoming", False)
        args["outgoing"] = True
        if bool(args["incoming"]):
            args["outgoing"] = False

        try:
            if pattern is not None and not pattern.startswith('(?i)'):
                args['pattern'] = '(?i)' + pattern
        except BaseException:
            pass

        reg = re.compile('(.*)')
        if pattern is not None:
            try:
                cmd = re.search(reg, pattern)
                try:
                    cmd = cmd.group(1).replace(
                        "$",
                        "").replace(
                        "\\",
                        "").replace(
                        "^",
                        "")
                except BaseException:
                    pass

                try:
                    CMD_LIST[file_test].append(cmd)
                except BaseException:
                    CMD_LIST.update({file_test: [cmd]})
            except BaseException:
                pass

        if allow_sudo:
            args["from_users"] = list(Var.SUDO_USERS)
            # Mutually exclusive with outgoing (can only set one of either).
            args["incoming"] = True
        del allow_sudo
        try:
            del args["allow_sudo"]
        except BaseException:
            pass

        if "allow_edited_updates" in args:
            del args['allow_edited_updates']

        def decorator(func):
            if allow_edited_updates:
                bot.add_event_handler(func, events.MessageEdited(**args))
            bot.add_event_handler(func, events.NewMessage(**args))
            try:
                LOAD_PLUG[file_test].append(func)
            except BaseException:
                LOAD_PLUG.update({file_test: [func]})
            return func

        return decorator


def load_module(shortname):
    if shortname.startswith("__"):
        pass
    elif shortname.endswith("_"):
        import userbot.utils
        import importlib
        path = Path(f"userbot/plugins/{shortname}.py")
        name = "userbot.plugins.{}".format(shortname)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("Successfully (re)imported " + shortname)
    else:
        import userbot.utils
        import importlib
        path = Path(f"userbot/plugins/{shortname}.py")
        name = "userbot.plugins.{}".format(shortname)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.bot = bot
        mod.tgbot = bot.tgbot
        mod.Var = Var
        mod.command = command
        mod.logger = logging.getLogger(shortname)
        # support for uniborg
        sys.modules["uniborg.util"] = userbot.utils
        mod.Config = Config
        mod.borg = bot
        mod.userbot = bot
        # auto-load
        mod.admin_cmd = admin_cmd
        mod.sudo_cmd = sudo_cmd
        mod.edit_or_reply = edit_or_reply
        mod.eor = eor
        # support for paperplaneextended
        sys.modules["userbot.events"] = userbot.utils
        spec.loader.exec_module(mod)
        # for imports
        sys.modules["userbot.plugins." + shortname] = mod
        print("Successfully (re)imported " + shortname)
        # support for other third-party plugins
        sys.modules["userbot.utils"] = userbot.utils
        sys.modules["userbot"] = userbot


def remove_plugin(shortname):
    try:
        try:
            for i in LOAD_PLUG[shortname]:
                bot.remove_event_handler(i)
            del LOAD_PLUG[shortname]

        except BaseException:
            name = f"userbot.plugins.{shortname}"

            for i in reversed(range(len(bot._event_builders))):
                ev, cb = bot._event_builders[i]
                if cb.__module__ == name:
                    del bot._event_builders[i]
    except BaseException:
        raise ValueError


def admin_cmd(pattern=None, **args):
    args["func"] = lambda e: e.via_bot_id is None

    stack = inspect.stack()
    previous_stack_frame = stack[1]
    file_test = Path(previous_stack_frame.filename)
    file_test = file_test.stem.replace(".py", "")
    allow_sudo = args.get("allow_sudo", False)

    # get the pattern from the decorator
    if pattern is not None:
        if pattern.startswith(r"\#"):
            # special fix for snip.py
            args["pattern"] = re.compile(pattern)
        else:
            args["pattern"] = re.compile(handler + pattern)
            cmd = handler + pattern
            try:
                CMD_LIST[file_test].append(cmd)
            except BaseException:
                CMD_LIST.update({file_test: [cmd]})

    args["outgoing"] = True
    # should this command be available for other users?
    if allow_sudo:
        args["from_users"] = list(Var.SUDO_USERS)
        # Mutually exclusive with outgoing (can only set one of either).
        args["incoming"] = True
        del args["allow_sudo"]

    # error handling condition check
    elif "incoming" in args and not args["incoming"]:
        args["outgoing"] = True

    # add blacklist chats, UB should not respond in these chats
    if "allow_edited_updates" in args and args["allow_edited_updates"]:
        args["allow_edited_updates"]
        del args["allow_edited_updates"]

    # check if the plugin should listen for outgoing 'messages'

    return events.NewMessage(**args)


""" Userbot module for managing events.
 One of the main components of the userbot. """


def register(**args):
    """ Register a new event. """
    args["func"] = lambda e: e.via_bot_id is None

    stack = inspect.stack()
    previous_stack_frame = stack[1]
    file_test = Path(previous_stack_frame.filename)
    file_test = file_test.stem.replace(".py", "")
    pattern = args.get('pattern', None)
    disable_edited = args.get('disable_edited', True)

    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = '(?i)' + pattern

    if "disable_edited" in args:
        del args['disable_edited']

    reg = re.compile('(.*)')
    if pattern is not None:
        try:
            cmd = re.search(reg, pattern)
            try:
                cmd = cmd.group(1).replace(
                    "$",
                    "").replace(
                    "\\",
                    "").replace(
                    "^",
                    "")
            except BaseException:
                pass

            try:
                CMD_LIST[file_test].append(cmd)
            except BaseException:
                CMD_LIST.update({file_test: [cmd]})
        except BaseException:
            pass

    def decorator(func):
        if not disable_edited:
            bot.add_event_handler(func, events.MessageEdited(**args))
        bot.add_event_handler(func, events.NewMessage(**args))
        try:
            LOAD_PLUG[file_test].append(func)
        except Exception:
            LOAD_PLUG.update({file_test: [func]})

        return func

    return decorator


def errors_handler(func):
    async def wrapper(tele):
        try:
            await func(tele)
        except BaseException:
            date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            text = "**userbot CRASH REPORT**\n\n"
            link = "[this group](https://t.me/blackthunderot)"
            text += "You may report this, if needed."
            text += f"Forward this message to {link}.\n"
            text += "Nothing except the fact of error and date is logged here.\n"
            errlog = "\n\nDisclaimer:\nPrivacy comes first"
            errlog += "\nThis file is uploaded only here"
            errlog += "and not anywhere else."
            errlog += "\nIf needed, you may report this to @userbotHelpChat."
            errlog += "\nDon't worry, no one will see your data!\n\n"
            errlog += "==========||--BEGIN USERBOT TRACEBACK LOG--||=========="
            errlog += "\nDate: " + date
            errlog += "\nGroup ID: " + str(tele.chat_id)
            errlog += "\nSender ID: " + str(tele.sender_id)
            errlog += "\n\nEvent Trigger:\n"
            errlog += str(tele.text)
            errlog += "\n\nTraceback info:\n"
            errlog += str(traceback.format_exc())
            errlog += "\n\nError text:\n"
            errlog += str(sys.exc_info()[1])
            errlog += "\n\n==========||--END USERBOT TRACEBACK LOG--||=========="

            command = "git log --pretty=format:\"%an: %s\" -10"
            errlog += "\n\n\n==========||--BEGIN COMMIT LOG--||==========\n"
            errlog += "\n\nLast 10 commits:\n"
            process = await asyncsubshell(command, stdout=asyncsub.PIPE, stderr=asyncsub.PIPE)
            stdout, stderr = await process.communicate()
            result = str(stdout.decode().strip()) + \
                str(stderr.decode().strip())
            errlog += result
            errlog += "\n\n\n==========||--END OF COMMIT LOG--||==========\n"
            file = open("error.log", "w+")
            file.write(errlog)
            file.close()

            await tele.client.send_file(Var.PRIVATE_GROUP_ID, "error.log", caption=text)
            return await func(tele)
        except Exception:
            pass
    return wrapper


async def progress(current, total, event, start, type_of_ps, file_name=None):
    """Generic progress_callback for both
    upload.py and download.py"""
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion
        progress_str = "[{0}{1}]\nProgress: {2}%\n".format(
            ''.join(["█" for i in range(math.floor(percentage / 5))]),
            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))
        tmp = progress_str + \
            "{0} of {1}\nETA: {2}".format(
                humanbytes(current),
                humanbytes(total),
                time_formatter(estimated_total_time)
            )
        if file_name:
            await event.edit("{}\nFile Name: `{}`\n{}".format(
                type_of_ps, file_name, tmp))
        else:
            await event.edit("{}\n{}".format(type_of_ps, tmp))


def humanbytes(size):
    """Input size in bytes,
    outputs in a human readable format"""
    # https://stackoverflow.com/a/49361727/4723940
    if not size:
        return ""
    # 2 ** 10 = 1024
    power = 2**10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"


def time_formatter(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " day(s), ") if days else "") + \
        ((str(hours) + " hour(s), ") if hours else "") + \
        ((str(minutes) + " minute(s), ") if minutes else "") + \
        ((str(seconds) + " second(s), ") if seconds else "") + \
        ((str(milliseconds) + " millisecond(s), ") if milliseconds else "")
    return tmp[:-2]


class Loader():
    def __init__(self, func=None, **args):
        self.Var = Var
        bot.add_event_handler(func, events.NewMessage(**args))


def sudo_cmd(pattern=None, **args):
    args["func"] = lambda e: e.via_bot_id is None

    stack = inspect.stack()
    previous_stack_frame = stack[1]
    file_test = Path(previous_stack_frame.filename)
    file_test = file_test.stem.replace(".py", "")
    allow_sudo = args.get("allow_sudo", False)

    # get the pattern from the decorator
    if pattern is not None:
        if pattern.startswith(r"\#"):
            # special fix for snip.py
            args["pattern"] = re.compile(pattern)
        else:
            args["pattern"] = re.compile(sudo_hndlr + pattern)
            cmd = sudo_hndlr + pattern
            try:
                CMD_LIST[file_test].append(cmd)
            except BaseException:
                CMD_LIST.update({file_test: [cmd]})

    args["outgoing"] = True
    # should this command be available for other users?
    if allow_sudo:
        args["from_users"] = list(Var.SUDO_USERS)
        # Mutually exclusive with outgoing (can only set one of either).
        args["incoming"] = True
        del args["allow_sudo"]

    # error handling condition check
    elif "incoming" in args and not args["incoming"]:
        args["outgoing"] = True

    # add blacklist chats, UB should not respond in these chats
    if "allow_edited_updates" in args and args["allow_edited_updates"]:
        args["allow_edited_updates"]
        del args["allow_edited_updates"]

    # check if the plugin should listen for outgoing 'messages'

    return events.NewMessage(**args)


async def edit_or_reply(event, text):
    if event.sender_id in Config.SUDO_USERS:
        reply_to = await event.get_reply_message()
        if reply_to:
            return await reply_to.reply(text)
        return await event.reply(text)
    return await event.edit(text)


async def eor(event, text):
    if event.sender_id in Config.SUDO_USERS:
        reply_to = await event.get_reply_message()
        if reply_to:
            return await reply_to.reply(text)
        return await event.reply(text)
    return await event.edit(text)

# TGBot


def assistant_cmd(add_cmd, is_args=False):
    def cmd(func):
        serena = bot.tgbot
        if is_args:
            pattern = bothandler + add_cmd + "(?: |$)(.*)"
        elif is_args == "stark":
            pattern = bothandler + add_cmd + " (.*)"
        elif is_args == "snips":
            pattern = bothandler + add_cmd + " (\S+)"
        else:
            pattern = bothandler + add_cmd + "$"
        serena.add_event_handler(
            func, events.NewMessage(incoming=True, pattern=pattern)
        )

    return cmd


def is_admin():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            serena = bot.tgbot
            sed = await serena.get_permissions(event.chat_id, event.sender_id)
            user = event.sender_id
            kek = bot.uid
            if sed.is_admin:
                await func(event)
            if event.sender_id == kek:
                pass
            elif not user:
                pass
            if not sed.is_admin:
                await event.reply("Only Admins Can Use it.")

        return wrapper

    return decorator


def is_bot_admin():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            serena = bot.tgbot
            pep = await serena.get_me()
            sed = await serena.get_permissions(event.chat_id, pep)
            if sed.is_admin:
                await func(event)
            else:
                await event.reply("I Must Be Admin To Do This.")

        return wrapper

    return decorator


def only_pro():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            kek = list(Config.SUDO_USERS)
            mm = bot.uid
            if event.sender_id == mm:
                await func(event)
            elif event.sender_id == kek:
                await func(event)
            else:
                await event.reply("Only Owners, Sudo Users Can Use This Command.")

        return wrapper

    return decorator


def god_only():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            moms = bot.uid
            if event.sender_id == moms:
                await func(event)
            else:
                pass

        return wrapper

    return decorator


def only_groups():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            if event.is_group:
                await func(event)
            else:
                await event.reply("This Command Only Works On Groups.")

        return wrapper

    return decorator


def only_group():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            if event.is_group:
                await func(event)
            else:
                pass

        return wrapper

    return decorator


def peru_only():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            kek = list(Config.SUDO_USERS)
            mm = bot.uid
            if event.sender_id == mm:
                await func(event)
            elif event.sender_id == kek:
                await func(event)
            else:
                pass

        return wrapper

    return decorator


def only_pvt():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event):
            if event.is_group:
                pass
            else:
                await func(event)

        return wrapper

    return decorator


def start_assistant(shortname):
    if shortname.startswith("__"):
        pass
    elif shortname.endswith("_"):
        import importlib
        import sys
        from pathlib import Path

        path = Path(f"userbot/plugins/assistant{shortname}.py")
        name = "userbot.plugins.assistant.{}".format(shortname)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("Starting Your Assistant Bot.")
        print("Assistant Sucessfully imported " + shortname)
    else:
        import importlib
        import sys
        from pathlib import Path

        path = Path(f"userbot/plugins/assistant/{shortname}.py")
        name = "userbot.plugins.assistant.{}".format(shortname)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.tgbot = bot.tgbot
        mod.serena = bot.tgbot
        mod.assistant_cmd = assistant_cmd
        mod.god_only = god_only()
        mod.only_groups = only_groups()
        mod.only_pro = only_pro()
        mod.pro_only = only_pro()
        mod.only_group = only_group()
        mod.is_bot_admin = is_bot_admin()
        mod.is_admin = is_admin()
        mod.peru_only = peru_only()
        mod.only_pvt = only_pvt()
        spec.loader.exec_module(mod)
        sys.modules["userbot.plugins.assistant" + shortname] = mod
        print("Assistant Has imported " + shortname)
