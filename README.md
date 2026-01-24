# Logman

_Convenience package for exception hooking and logging to multiple sources_

An offshoot from a separate project that shall remain private. Forked this away to recycle elsewhere.

> [!WARNING]
> Currently only tested on UNIX systems with `Py3.12`. A lot of core functionallity is missing too.

## Usage

1. At program start, run the `create_logger()` function.
   a. If desired, pass custom dict formatted config at this stage.

```python
# package/__init__.py
from logman import create_logger

log = create_logger()
```

2. In separate modules, run the `get_logger()` function, passing a name for the local logger.

```python
# package/module.py
from logman import get_logger

log = get_logger(__name__)
```

## Formatting the log

> Default format:
>
> ```
> {levelname: <8} {asctime: <8} {module_path: <17}
> ```
>
> ```
> INFO      15:31:42,900445 logman:237        : Informative message.
>                                             : Also, more lines down here!
> ```

### Log Record

Use the following keys in the config `$["formatters"]["base"]["fmt"]` field.

**Default**

|       Key | Desc |             Key | Desc |
| --------: | :--- | --------------: | :--- |
|      args |      |           msecs |      |
|   asctime |      |             msg |      |
|   created |      |            name |      |
|  exc_info |      |        pathname |      |
|  exc_text |      |         process |      |
|  filename |      |     processName |      |
|  funcName |      | relativeCreated |      |
| levelname |      |      stack_info |      |
|   levelno |      |        taskName |      |
|    lineno |      |          thread |      |
|   message |      |      threadName |      |
|    module |      |                 |      |

**Custom:**

|         Key | Desc                         |
| ----------: | :--------------------------- |
| module_path | Combined `name` and `lineno` |
