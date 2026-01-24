from datetime import datetime, timezone
from json import dumps
from time import strftime, localtime
from typing import override
import atexit
import logging
import os
import sys
import traceback


LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}

# ======================================================================
# ======================================================================


class MainFormatter(logging.Formatter):
    '''Custom log record formatter. Keeps messages aligned'''
    minimum_indent = 46

    @override
    def format(self, record):
        '''Features multiline indentation inspired by the following:
        https://stackoverflow.com/a/66855071'''

        # Merged attribute to help with formatting
        record.module_path = f'{record.name}:{record.lineno}'
        header = f'{super().format(record): <{self.minimum_indent}} : '

        l = len(header) - 2
        indent = ' ' * l
        indent += ': '

        first_line, *trailing = record.msg.splitlines(True)
        header += first_line
        return header + ''.join(indent + line for line in trailing)

    @override
    def formatTime(self, record: logging.LogRecord, datefmt=None):
        '''Cleaner default while keeping the possibility to set `datefmt`

        New default format: `HH:mm:ss,SSSSSS`'''
        if datefmt:
            ct = localtime(record.created)
            s = strftime(datefmt, ct)
        else:
            ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
            s = f'{ct.hour:02d}:{ct.minute:02d}:{ct.second:02d}'
        return s


class SimpleFormatter(logging.Formatter):
    '''Custom log record formatter. Keeps messages aligned
    For the `simple` formatter'''

    @override
    def format(self, record):
        f = ''
        og_msg = super().format(record)
        return og_msg.replace('\n', f'\n{f: <10}: ')


class JSONFormatter(logging.Formatter):
    '''Custom log record formatter. Reformats all to jsonl

    Add additional info to the log via the `extra` parameter:
    `log.info('msg', extra={"hello"="world"}`'''

    uid = ''

    def __init__(self, *, fmt_keys: dict[str, str] | None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord):
        msg = self._prep_log_to_dict(record)
        return dumps(msg, default=str)

    def _prep_log_to_dict(self, record: logging.LogRecord):
        always_fields = {
            'message': record.getMessage(),
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        }
        if record.exc_info is not None:
            always_fields['exc_info'] = self.formatException(
                record.exc_info)
        if record.stack_info is not None:
            always_fields['stack_info'] = self.formatStack(
                record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val
        # FIXME: Import ID from rolls
        message['id'] = self.uid

        return message


class InfoFilter(logging.Filter):
    '''Allows LogRecords of level INFO and below'''
    @override
    def filter(self, record: logging.LogRecord):
        return record.levelno <= logging.INFO


class ErrorFilter(logging.Filter):
    '''Allows LogRecords of level WARNING and above'''
    @override
    def filter(self, record: logging.LogRecord):
        return record.levelno >= logging.WARNING


class MainLogger(logging.Logger):
    def __init__(self, name: str, level: int | str = 0):
        super().__init__(name, level)
        # logging.root is required as parent to ensure correct log propegation
        self.parent = logging.root

    @override
    def exception(self, msg: str | None = None,
                  exc: BaseException | None = None,
                  popup: bool = False,
                  limit: int | None = None,
                  *args, **kwargs) -> None:
        '''Override of the base exception method.

        Args:
            msg: `str` Additional information
            exc: `BaseException` Called exception class
            popup: `bool` Create a popup window with traceback info
            limit: `int` How many lines of the traceback to log. Defaults to all'''
        if exc:
            exc_info = (type(exc), exc, exc.__traceback__)
        else:
            exc_info = sys.exc_info()

        if exc_info[0] is None:
            self.warning(
                '"exc_logger" was called but no exception was found. There might be a bug here!')
            return

        if msg is None:
            msg = 'An unxepcted error occured'

        exc_info[1].add_note(msg)
        full_tb = str().join(traceback.format_exception(exc_info[0],
                                                        value=exc_info[1],
                                                        tb=exc_info[2],
                                                        limit=limit))

        # FIXME: import message_box or add it as a class method
        # if popup:
        #     from ..utils.utils import message_box
        #     message_box(header=exc_info[0].__name__, msg=msg)

        extra_info: dict | None = kwargs.get('extra')
        if extra_info is None:
            kwargs['extra'] = {
                'exception': exc_info[1], 'exception_msg': msg}
        else:
            extra_info['exception'] = exc_info[1]
            extra_info['exception_msg'] = msg

        # stacklevel=2 to get lineno of original caller
        self.log(logging.CRITICAL, full_tb,
                 stacklevel=2, *args, **kwargs)

    def get_module(self):
        raise NotImplementedError

    def _popup(self, header: str, body: str):
        raise NotImplementedError


# ======================================================================
# ======================================================================


class ExitHandlerHook:
    '''Exit and Excpetion Handler hook.

    Will hook both sys.exit and sys.excepthook when initiated. 
    Raised exception will call `log.exception` and exit

    Also runs double-duty and closes log's `queue_handler` thread'''

    def __init__(self) -> None:
        self.exit_code = None
        self.base_exception = None
        self.exception_type = None
        self.exception_tb_str = str()

        self.hook()
        atexit.register(self.wrap_up)

    def hook(self):
        self._orig_exit = sys.exit
        self._orig_exc_handler = sys.excepthook
        sys.exit = self.exit
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        self.exit_code = code
        self._orig_exit(code)

    def exc_handler(self, exc_type, exc, *args):
        self.base_exception = exc
        self.exception_type = exc_type

        self.exception_tb_str = str().join(traceback.format_exception(
            type(self.exception_type), value=exc, tb=exc.__traceback__))
        # Commented out to avoid printing the exception twice directly to stderr
        # self._orig_exc_handler(exc_type, exc, *args)

    def wrap_up(self):
        from . import get_logger
        self.log: MainLogger = get_logger(__name__)

        if self.exit_code is not None and self.exit_code != 0:
            self.log.warning(f'Exiting with errors: {self.exit_code}',
                             extra={"rc": self.exit_code})
        elif self.exception_tb_str:
            self.log.exception(f'\nSomething went wrong. Please read the message above and look back through the logs',
                               exc=self.base_exception,
                               popup=True,
                               extra={"exc_type": self.exception_type,
                                      "exc_msg": self.base_exception,
                                      "rc": 1})
        else:
            self.log.info('Exiting program: 0', extra={"rc": 0})

        self._stop_queue_handler()

    def _stop_queue_handler(self):
        q_handler = logging.getHandlerByName('queue_handler')
        if q_handler is None:
            self.log.info('Goodbye!')
        else:
            try:
                self.log.debug('queue_handler found')
                self.log.info('Stopping logs. Goodbye!')
                q_handler.listener.stop()
            except AttributeError as e:
                self.log.exception('Error closing queue thread')
                raise e
