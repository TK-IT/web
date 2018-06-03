import inspect
import functools


def parameter(*keys):
    """
    In SheetImage.parameters we store a JSON dictionary containing
    parameter values that control image extraction.

    For instance, extract_cols is controlled by a parameter named
    'width' with some default value such as 4. We want to store
    the value of the 'width' parameter along with the SheetImage
    so that we can rerun the function in the future with the same
    parameters.

    >>> class SheetImageMock:  # Dummy SheetImage for doctests
    ...     def __init__(self): self.parameters = {}
    >>> sheet_image = SheetImageMock()

    The @parameter('width') decorator will set the value of the 'width'
    parameter to whatever value was used previously if it is not given
    explicitly.

    >>> @parameter('width')
    ... def foo(sheet_image, width=4):
    ...     print('Width is %s' % width)
    >>> foo(sheet_image)
    Width is 4
    >>> sheet_image.parameters
    {'foo.width': 4}

    If we run the function with a different value of width, this is
    recorded with sheet_image:

    >>> foo(sheet_image, width=10)
    Width is 10
    >>> sheet_image.parameters
    {'foo.width': 10}

    Note that the default value of 'width' is ignored when 'foo.width' is in
    sheet_image.parameters.
    >>> foo(sheet_image)
    Width is 10

    To reuse parameters across functions, you can specify that the parameter is
    in a different function's namespace:
    >>> @parameter('foo.width')
    ... def bar(sheet_image, width=4):
    ...     print('In bar, width is %s' % width)
    >>> bar(sheet_image)
    In bar, width is 10

    You can also declare multiple parameters:
    >>> @parameter('a b')
    ... def multi(sheet_image, a=1, b=2):
    ...     print(a, b)
    >>> multi(sheet_image)
    1 2
    >>> multi(sheet_image)
    1 2
    """

    if len(keys) == 1:
        keys = keys[0].split()

    def decorator(fn):
        signature = inspect.signature(fn)
        key_params = []
        for full_key in keys:
            if "." not in full_key:
                full_key = "%s.%s" % (fn.__name__, full_key)
            origin_function, key = full_key.split(".")
            try:
                key_param = signature.parameters[key]
            except KeyError:
                raise TypeError("Function must accept an argument called %r" % (key,))
            if key_param.default is signature.empty:
                raise TypeError("Function parameter %r must have a default" % (key,))
            key_params.append((full_key, key, key_param.default))

        def update_kwargs(bound_args, parameters, kwargs):
            for full_key, key, default in key_params:
                if key in bound_args.arguments:
                    parameters[full_key] = bound_args.arguments[key]
                elif full_key in parameters:
                    kwargs[key] = parameters[full_key]
                else:
                    parameters[full_key] = default

        if "parameters" in signature.parameters:

            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                bound_args = signature.bind(*args, **kwargs)
                parameters = bound_args.arguments["parameters"]
                update_kwargs(bound_args, parameters, kwargs)
                return fn(*args, **kwargs)

        elif "sheet_image" in signature.parameters:

            @functools.wraps(fn)
            def wrapped(*args, **kwargs):
                bound_args = signature.bind(*args, **kwargs)
                parameters = bound_args.arguments["sheet_image"].parameters
                update_kwargs(bound_args, parameters, kwargs)
                return fn(*args, **kwargs)

        else:

            @functools.wraps(fn)
            def wrapped(*args, parameters, **kwargs):
                bound_args = signature.bind(*args, **kwargs)
                update_kwargs(bound_args, parameters, kwargs)
                return fn(*args, **kwargs)

        return wrapped

    return decorator
