import argparse
import logging
import logging.handlers
import logging_json
import random
import string
import sys
import threading
import time
from logfmter import Logfmter
from os.path import expanduser
from cysystemd import journal
from src import constants
from src.webserver import start_webserver

ERROR_VALUE = "Invalid Value:"
log_file_path = (expanduser(".") + "/spam_application.log")

parser = argparse.ArgumentParser(description='Basic Help:')
parser.add_argument('-c', '--color', type=str, default='always', help="Enable or disable color format for message field in log message")
parser.add_argument('-f', '--format', type=str, default="logfmt", help="The logging format to be used when sending log messages")
parser.add_argument('-l', '--level', type=str, default="debug", help="The logging level to be used when sending log messages")
parser.add_argument('-n', '--name', type=str, default="spam_application", help="Name of the logger used to log the call")
parser.add_argument('-p', '--path_file', type=str, default=log_file_path, help="Path to file when writing log messages to file")
parser.add_argument('-s', '--stream', type=str, default="stdout", help="The stream type that will be used when sending log messages")
parser.add_argument('-t', '--type', type=str, default="console", help="The handler type that will be used when sending log messages")
parser.add_argument('-H', '--web_host', type=str, default=constants.HOST, help="Set the host address for third party Web-server")
parser.add_argument('-P', '--web_port', type=int, default=constants.PORT, help="Set the port for third party Web-server")
parser.add_argument('-M', '--web_method', type=str, default="GET", help="Set the HTTP-method for third party Web-server")
parser.add_argument('-T', '--timeout', type=float, default=2.0, help="The interval in seconds at which the log message will be sent")
parser.add_argument('-W', '--webserver', action='store_true', help="Starting the built-in Web-server")

arguments = None
timeout = 2.0
list_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.FATAL]
log_date_format = '%Y-%m-%d, %H:%M:%S'

class MySuperColorFormatter(logging.Formatter):
    COLOR_CODES = {
        logging.DEBUG:    "\033[0;36m",
        logging.INFO:     "\033[0;32m",
        logging.WARNING:  "\033[1;33m",
        logging.ERROR:    "\033[1;31m",
        logging.CRITICAL: "\033[0;35m"
    }

    RESET_CODE = "\033[0m"
    original_formatter = None

    def __init__(self, original_formatter):
        self.original_formatter = original_formatter

    def format(self, record):
        record.levelname = record.levelname.lower()
        if (record.levelno in self.COLOR_CODES):
            record.msg = self.COLOR_CODES[record.levelno] + record.msg + self.RESET_CODE
        return self.original_formatter.format(record)

class NonColorFormatter(logging.Formatter):
    original_formatter = None

    def __init__(self, original_formatter):
        self.original_formatter = original_formatter

    def format(self, record):
        record.levelname = record.levelname.lower()
        return self.original_formatter.format(record)

def use_color():
    color = arguments.color.lower()

    if color == "always":
        return True
    elif color == "never":
        return False
    else:
        print("Something went wrong with color argument:\n")
        raise ValueError(f"{ERROR_VALUE} '%s'" % arguments.color)

def generate_random_string():
    length = random.randint(10, 20)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def log_format(pls_use_color):
    if arguments.format == "unstructured":
        log_value_format = '%(asctime)s %(name)s %(process)d %(threadName)s %(levelname)s %(message)s'
        console_formatter = logging.Formatter(fmt=log_value_format, datefmt=log_date_format)

    elif arguments.format == "logfmt":
        console_formatter = Logfmter(
            keys=["date", "name", "threadName", "thread", "processName", "process", "level", "levelnum", "msg"],
            mapping={
                "date": "asctime",
                "name": "name",
                "thread": "thread",
                "threadName": "threadName",
                "process": "process",
                "processName": "processName",
                "level": "levelname",
                "levelnum": "levelno",
                "msg": "message"
            })

    elif arguments.format == "json":
        console_formatter = logging_json.JSONFormatter(
            datefmt=log_date_format,
            fields={
                "date": "asctime",
                "name": "name",
                "thread": "thread",
                "threadName": "threadName",
                "process": "process",
                "processName": "processName",
                "levelnum": "levelno",
                "level": "levelname",
                "message": "message"
            })

    else:
        print("Something went wrong with format type:\n")
        raise ValueError(f"{ERROR_VALUE} '%s'" % arguments.format)

    if pls_use_color:
        return MySuperColorFormatter(console_formatter)
    else:
        return NonColorFormatter(console_formatter)

def create_console_handler(console_log_output='stdout', console_log_level='warning'):
    console_log_output = console_log_output.lower()

    if console_log_output == "stdout":
        console_log_output = sys.stdout

    elif console_log_output == "stderr":
        console_log_output = sys.stderr

    else:
        print("Something went wrong with type of console stream:\n")
        raise ValueError(f"{ERROR_VALUE} '%s'" % console_log_output)

    console_handler = logging.StreamHandler(console_log_output)

    try:
        console_handler.setLevel(console_log_level.upper())

    except Exception as error:
        print("Something went wrong with log level in console mode:\n")
        raise ValueError('{m}'.format(m = str(error)))

    result_log_format = log_format(use_color())
    console_handler.setFormatter(result_log_format)
    return console_handler

def create_journald_handler(console_log_level='warning'):
    journald_handler = journal.JournaldLogHandler()

    try:
        journald_handler.setLevel(console_log_level.upper())

    except Exception as error:
        print("Something went wrong with log level in jounrald mode:\n")
        raise ValueError('{m}'.format(m = str(error)))

    result_log_format = log_format(use_color())
    journald_handler.setFormatter(result_log_format)
    return journald_handler

def create_http_handler(console_log_level='warning'):
    address = f"{arguments.web_host}:{arguments.web_port}"
    http_handler = logging.handlers.HTTPHandler(address, url=f"http://{address}", method=arguments.web_method, secure=False)

    try:
        http_handler.setLevel(console_log_level.upper())

    except Exception as error:
        print("Something went wrong with log level in file mode:\n")
        raise ValueError('{m}'.format(m = str(error)))

    return http_handler

def create_file_handler(console_log_level='warning'):
    file_handler = logging.FileHandler(arguments.path_file)

    try:
        file_handler.setLevel(console_log_level.upper())

    except Exception as error:
        print("Something went wrong with log level in file mode:\n")
        raise ValueError('{m}'.format(m = str(error)))

    result_log_format = log_format(use_color())
    file_handler.setFormatter(result_log_format)
    return file_handler

def create_logger(name, handler):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

def exec_logger():
    if arguments.type == "console":
        exec_logger = create_logger(arguments.name, create_console_handler(
            console_log_level=arguments.level, 
            console_log_output=arguments.stream
        ))

    elif arguments.type == "journald":
        exec_logger = create_logger(arguments.name, create_journald_handler(
            console_log_level=arguments.level
        ))

    elif arguments.type == "http":
        exec_logger = create_logger(arguments.name, create_http_handler(
            console_log_level=arguments.level
        ))

    elif arguments.type == "file":
        exec_logger = create_logger(arguments.name, create_file_handler(
            console_log_level=arguments.level
        ))

    else:
        print("Something went wrong with type of handler:\n")
        raise ValueError(f"{ERROR_VALUE} '%s'" % arguments.type)

    return exec_logger

def main():
    try:
        global arguments
        arguments = parser.parse_args()
        timeout = arguments.timeout
        constants.HOST = arguments.web_host
        constants.PORT = arguments.web_port

        if arguments.webserver:
            webserver_thread = threading.Thread(target=start_webserver)
            webserver_thread.daemon = True
            webserver_thread.start()

        log = exec_logger()
        while 1:
            time.sleep(timeout)
            log_level = logging.getLevelName(random.choice(list_levels))
            getattr(log, log_level.lower())

            if 'DEBUG' in log_level:
                log.debug(f'Сообщение для отладки, цвет — синий: {generate_random_string()}')

            elif 'INFO' in log_level:
                log.info(f'Информационное сообщение, цвет — зеленый: {generate_random_string()}')

            elif 'WARNING' in log_level:
                log.warning(f'Предупреждающее сообщение, цвет — желтый: {generate_random_string()}')

            elif 'ERROR' in log_level:
                log.error(f'Сообщение об ошибке, цвет — красный: {generate_random_string()}')

            elif 'CRITICAL' in log_level:
                log.critical(f'Сообщение о критической ошибке, цвет — фиолетовый: {generate_random_string()}')

    except Exception as error:
        print(error)

if __name__ == "__main__":
    main()
