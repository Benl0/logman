'''
**Convenience package for exception hooking and logging to multiple sources**

Initialise and import the Logger via the `create_logger` function, then `get_logger` in following modules.
Exception and `sys.exit` hooks will be initialised on package import. 

_Please note, the package must be fully initialised to create the Loggers._
_Heavy inspiration and thanks to [mCoding](https://www.youtube.com/watch?v=9L77QExPmI0)._

**To Do List:**
- Selectively disable `stdout` and `stderr` output destinations
- Add directory creation checks
- Get accurate package.module name for log record
- Minor formatting error. Additional empty line is added when logging exceptions
'''

from importlib.metadata import version
from logging.handlers import QueueHandler
from pathlib import Path
import logging
import logging.config

from .classes import ExitHandlerHook, MainLogger
from .utils import (
    change_verbosity,
    get_config,
    resolve_file_paths,
    update_uid,
)

__all__ = [
    'change_verbosity',
    'get_logger',
    '_LOG_NAME',
    'MainLogger',
    'update_uid',
]

_log = None
ExitHandlerHook()

# Defaults
_LOG_NAME = 'logman'
_BACKUP_FILE = Path('~/Desktop/logman.log').expanduser()
_BACKUP_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {
            "()": "logman.classes.MainFormatter",
            "style": "{",
            "validate": True,
            "fmt": "{levelname: <8} {asctime: <8} {module_path: <17}"
        },
        "json": {
            "()": "logman.classes.JSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp",
                "logger": "name",
                "module": "module",
                "function": "funcName",
                "line": "lineno"
            }
        }
    },
    "handlers": {
        "console_stdout": {
            "class": "logging.StreamHandler",
            "formatter": "base",
            "stream": "ext://sys.stdout",
            "level": "DEBUG"
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "base",
            "filename": _BACKUP_FILE,
            "when": "midnight",
            "interval": 1,
            "backupCount": 5
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console_stdout", "file"],
        },
    },
}


def _init_log(config: dict | None = None, name: str = _LOG_NAME) -> MainLogger:
    '''
    Initialises custom Logger and applies dictConfig to the root logger.

    :param config: Logger config dictionary. If None,`log_config.json` will be used.
    :type config: dict | None
    :param name: Name of the logger. Defaults to `LOG_NAME`.
    :type name: str | None
    :return: Custom Logger class
    :rtype: MainLogger
    '''
    logging.setLoggerClass(MainLogger)
    log: MainLogger = logging.getLogger(name)  # type: ignore

    if config is None:
        config = get_config()

    config, file_paths = resolve_file_paths(config)

    try:
        logging.config.dictConfig(config)

        # Setup Log Queue Handler
        queue_handler: QueueHandler = logging.getHandlerByName(
            'queue_handler')  # type: ignore
        if queue_handler.listener is not None:
            queue_handler.listener.start()

    except (AttributeError, ValueError) as e:
        logging.config.dictConfig(_BACKUP_CONFIG)
        log.warning(
            f'Backup config loaded. Log file in "{_BACKUP_FILE}"')
        if type(e) is AttributeError:
            # QueueHandler init issue
            log.exception('Error starting queue_handler', e)
        elif type(e) is ValueError:
            # log json config issue
            log.exception('There are problems with the log config', e)

    except Exception as e:
        logging.config.dictConfig(_BACKUP_CONFIG)
        log.error(
            f'Backup config loaded. Log file in "{_BACKUP_FILE}"')
        log.exception('Unknown Error loading log config.', e)

    log.info(f'logman {version(__name__)} initialised.')
    return log


def create_logger(*args, **kwargs) -> MainLogger:
    '''
    Creates and returns MainLogger instance.

    :return: Custom Logger class
    :rtype: MainLogger
    '''
    global _log
    if not isinstance(_log, MainLogger):
        _log = _init_log(*args, **kwargs)
    return _log


def get_logger(name: str) -> MainLogger:
    '''
    Get a new mainLogger per module. **RUN AFTER `create_logger`**

    :param name: Name of the Logger. For msg formatting, use `__name__`.
    :type name: str
    :return: Custom Logger class
    :rtype: MainLogger
    '''
    global _log
    if not isinstance(_log, MainLogger):
        _log = _init_log()
    return logging.getLogger(name)  # type: ignore
