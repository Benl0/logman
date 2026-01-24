from json import load
from pathlib import Path
import logging
import os


def change_verbosity(verbosity: int, handler_name: str = 'console_stdout') -> None:
    '''Changes the `console_stdout` handler verbosity level'''
    if type(verbosity) != int:
        logging.warning(
            f'Invalid data type for verbosity\n{type(verbosity)} - {verbosity}')
        return

    handler = logging.getHandlerByName(handler_name)
    if handler is None:
        logging.error(
            f'Rquested Handler, "{handler_name}", does not exist or has not \
            been initialised')
        return

    if verbosity == 1:
        new_level = logging.INFO
    elif verbosity >= 2:
        new_level = logging.DEBUG
    else:
        new_level = logging.INFO

    old_level = handler.level
    if new_level >= old_level:
        return
    else:
        handler.setLevel(new_level)
        logging.debug(
            f'stdout log level changed: {old_level} > {handler.level}')


def get_config() -> dict:
    '''Grabs module filepath and reads the config file in the same directory'''
    _config_path = Path(
        os.path.realpath(os.path.dirname(__file__))) / 'default_config.json'

    with open(_config_path, 'r') as j:
        log_config: dict = load(j)
    return log_config


def resolve_file_paths(config: dict) -> tuple[dict, list]:
    '''Resolve FileHandler file paths. Returns fixed config and filepaths'''
    file_paths = list()
    handlers_conf: dict[str, dict] = config.get('handlers')

    for handle in handlers_conf.values():
        fp: str | None = handle.get('filename')
        if fp is None:
            continue
        else:
            file_path = Path(fp).expanduser().resolve()
            handle['filename'] = file_path
            file_paths.append(file_path)

    return config, file_paths


def update_uid(id: str):
    '''Update the `id` key for the JSONL file handler'''
    j_handler = logging.getHandlerByName('jsonl')
    j_handler.formatter.uid = id


def json_line_formatter():
    raise NotImplementedError


def dir_check(fp: str | Path) -> None:
    raise NotImplementedError
