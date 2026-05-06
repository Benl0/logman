from json import load
from pathlib import Path
from typing import Any
import logging
import os


def change_verbosity(verbosity: int, handler_name: str = 'console_stdout') -> None:
    """Changes the `console_stdout` handler verbosity level"""
    if type(verbosity) is not int:
        logging.warning(
            f'Invalid data type for verbosity\n{type(verbosity)} - {verbosity}'
        )
        return

    handler = logging.getHandlerByName(handler_name)
    if handler is None:
        logging.error(
            f'Rquested Handler, "{handler_name}", does not exist or has not \
            been initialised'
        )
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
        logging.debug(f'stdout log level changed: {old_level} > {handler.level}')


def get_config() -> dict:
    """Grabs module filepath and reads the config file in the same directory"""
    _config_path = (
        Path(os.path.realpath(os.path.dirname(__file__))) / 'default_config.json'
    )

    with open(_config_path, 'r') as j:
        log_config: dict = load(j)
    return log_config


def resolve_filepaths(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve and expand file paths of file based Handlers.

    Requires the full logging config as it will update values

    :param config: Log config
    :type config: dict[str, Any]
    :raises TypeError: If no handlers are found in the config
    :return: Tuple of amended config and the filepaths
    :rtype: tuple[dict, list[Path]]
    """
    handlers_conf: dict[str, dict[str, Any]] | None = config.get('handlers')
    if handlers_conf is None:
        raise TypeError('Could not find handlers in config')

    file_paths: list[Path] = list()
    for handle in handlers_conf.values():
        fp: str | None = handle.get('filename')
        if fp is not None:
            file_path = Path(fp).expanduser().resolve()
            file_path = validate_filepath(file_path)
            file_paths.append(file_path)
            handle['filename'] = file_path

    return config


def validate_filepath(fp: Path) -> Path:
    """Check if filepath exists and creates it if not."""
    if not fp.suffix:
        fp = fp / 'logman.log'  # Ensures there is a filename at the end of the path
    if not fp.parent.exists():
        fp.parent.mkdir(parents=True, exist_ok=True)
    return fp


def update_uid(id: str):
    """Update the `id` key for the JSONL file handler"""
    j_handler = logging.getHandlerByName('jsonl')
    j_handler.formatter.uid = id


def json_line_formatter():
    raise NotImplementedError


def dir_check(fp: str | Path) -> None:
    raise NotImplementedError
