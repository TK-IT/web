# Regnskab

To start, create `regnskabsite/settings/__init__.py` with the following contents:

```
from .common import *

DEBUG = True
SECRET_KEY = r'''fill me in from pwgen -sy 50 1'''
```

... where you use `pwgen -sy 50 1` to create a random secret key.


## Apache configuration

Note that running SciPy in Apache and `mod_wsgi`
[requires](https://mail.scipy.org/pipermail/scipy-user/2011-November/031014.html)
running in the global WSGI application group.

Use the following directive in your Apache WSGI configuration:

```
WSGIApplicationGroup %{GLOBAL}
```
