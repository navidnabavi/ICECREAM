import getopt
import os
import sys
from pydoc import locate
from bottle import Bottle, run
from ICECREAM.baseapp import BaseApp
from settings import default_address, apps


def get_default_address():
    _default = default_address
    return _default


commands_list = ['startapp', 'runserver', 'wsgi']
list_files = ['models.py', 'controller.py', 'schemas.py', 'urls.py']


class CommandsParser(object):
    def __init__(self, opt_commands):
        self.command = None
        self.subcommands = None
        self.opt_commands = opt_commands

    def get_command(self, ):
        if self.opt_commands[0] in commands_list:
            self.command = self.opt_commands[0]
            return self.command

    def get_subcommand(self, ):
        if self.opt_commands[0] in commands_list:
            self.command = self.opt_commands[0]
            self.opt_commands.remove(self.command)
            self.subcommands = []
            for command in self.opt_commands:
                self.subcommands.append(str(command))
        return self.subcommands

    def has_command(self) -> bool:
        if not self.opt_commands:
            return True
        return False

    def has_subcommand(self) -> bool:
        if not self.get_subcommand():
            return False
        return True


class CommandManager(object):

    def __init__(self, commands):
        self.command = CommandsParser(commands)

    def execute(self):
        if self.command.has_command():
            core = Core()
            return core.execute_wsgi()
        if self.command.get_command() == 'startapp':
            if self.command.has_subcommand():
                self.create_app(self.command.get_subcommand()[0])
            else:
                sys.stdout.write('ICECREAM: Need to provide an app name' + '\n')
        elif self.command.get_command() == 'runserver':
            core = Core()
            if self.command.has_subcommand():
                return core.execute_runserver(self.command.get_subcommand()[0])
            else:
                return core.execute_runserver(None)

    @staticmethod
    def create_app(app_name):
        try:
            path = app_name
            if not os.path.exists(path):
                os.makedirs(path)
            for file in list_files:
                filename = file
                with open(os.path.join(path, filename), 'wb') as temp_file:
                    temp_file.write('"ICECREAM"'.encode())
        except IOError as err:
            raise err.filename


class Core(object):
    def __init__(self, ):
        self.core = Bottle()
        self.__register_routers(self.core)

    def execute_wsgi(self):
        return self.core

    def execute_runserver(self, address):
        __address = self.__convert_command_to_address(address)
        run(self.core, host=__address['host'], port=__address['port'])
        return self.core

    @staticmethod
    def __convert_command_to_address(argv):
        """convert command to address"""
        try:
            _address = get_default_address()
            if argv is not None:
                arg_address = argv.split(':')
                _address['host'] = arg_address[0]
                _address['port'] = arg_address[1]
        except Exception as e:
            raise ValueError('ICECREAM: Please provide a valid address')
        return _address

    @staticmethod
    def __initialize_baseapps():
        """subclasses populate from settings route"""
        try:
            for app in apps:
                baseapp_class = locate(app)
                instance = baseapp_class()
        except Exception as exception:
            raise ValueError("undefined app")

    def __get_subclasses(self, cls):
        """all of inherited classes from base app populate"""
        for subclass in cls.__subclasses__():
            yield from self.__get_subclasses(subclass)
            yield subclass

    def __register_routers(self, core):
        """pass bottle core to subclasses"""
        self.__initialize_baseapps()
        base_app_subclasses = self.__get_subclasses(BaseApp)
        for sub_class in base_app_subclasses:
            sub_class.call_router(sub_class, core=core)