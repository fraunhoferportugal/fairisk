# Logging

This project uses the [Python logging module](https://docs.python.org/3/library/logging.html) with module name '**fairisk**'.

To configure the logger, you can use the default logging API.


### Examples

Set log level to debug:
```python
import logging
logging.getLogger('fairisk').setLevel(logging.DEBUG)
```

Disable logs:
```python
import logging
logging.getLogger('fairisk').propagate = False
```
