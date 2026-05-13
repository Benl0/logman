# Logman

_Personal convenience package for exception hooking and logging to multiple sources._
_Separated from another project that shall remain private._

**Heavy inspiration, credit and thanks to [mCoding](https://www.youtube.com/watch?v=9L77QExPmI0).**

> [!WARNING]
> Currently only tested on UNIX systems with `Py3.12` or above.

## Usage

1. Create a config dict. Use the [default_config.json](logman/default_config.json) as a guide. 

2. At program start, run the `create_logger()` function.

   ```python
   import logman

   log = logman.create_logger(name='logman', config=conf_dict)
   ```
   - If no config is passed, the default config will be used.


3. In following modules and scops, run the `get_logger()` function.

   ```python
   from logman import get_logger

   log = get_logger(__name__)
   ```
   - Optionally, pass the module `__name__` value. This can be used in the log format to have full packge.module.sub-module tracking in the message.
   - _e.g._ `DEBUG    11:18:56 package.sub-package.module:51  : JSON opened successfully`



## Formatting the log

> [!WARNING]
> _Use the [default_config.json](logman/default_config.json) as a guide. Seriously. It's really finnicky..._

> [!TIP]
> Within the config, it's recommended to specify `"style": "{"`. This is to allow character spacing via f string formatting syntax.

There are three Formatter classess:

### `MainFormatter`

Primary formatter class for logging a large number of information. There is no need to add the `{message}` record attribute as this will be added automatically.

Also features the "custom" record `{module_path}` which is just a combination of `{name}` and `{lineno}`.

```json
"formatters": {
   "base": {
      "()": "logman.classes.MainFormatter",
      "style": "{",
      "validate": true,
      "fmt": "{levelname: <8} {asctime: <8} {module_path: <17}"
   }
}
```

```
INFO      15:31:42,900445 logman:237        : Informative message.
                                            : Second line!
```

### `SimpleFormatter`

A secondary formatter intended for clutter-free messages (e.g. to console). No fancy formatting other than  indenting new lines by 10 whitespaces.

```json
"formatters": {
   "simple": {
      "()": "logman.classes.SimpleFormatter",
      "style": "{",
      "validate": true,
      "format": "{levelname: <9} : {message}"
   }
}
```

```
INFO       : Informative message.
           : Second line!
```

### `JSONFormatter`

Convert the log record into JSON. Only intended for output to a JSONLines file (for now).
Specify what goes to the JSON using the `fmt_keys` dict.

```json
"formatters": {
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
}
```

## Record Attributes

_Quick reference for the [Logging Record Attributes](https://docs.python.org/3/library/logging.html#logrecord-attributes)._

**Default**

|       Key  |              Key | 
| :--------: | :--------------: | 
|      args  |            msecs | 
|   asctime  |              msg | 
|   created  |             name | 
|  exc_info  |         pathname | 
|  exc_text  |          process | 
|  filename  |      processName | 
|  funcName  |  relativeCreated | 
| levelname  |       stack_info | 
|   levelno  |         taskName | 
|    lineno  |           thread | 
|   message  |       threadName | 
|    module  |                  | 

**Custom:**

|         Key  | Desc                         |
| :----------: | :--------------------------- |
| module_path  | Combined `name` and `lineno` |
