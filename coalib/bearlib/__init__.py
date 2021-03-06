"""
The bearlib is an optional library designed to ease the task of any Bear. Just
as the rest of coala the bearlib is designed to be as easy to use as possible
while offering the best possible flexibility.
"""

from coalib.settings.FunctionMetadata import FunctionMetadata


def deprecate_settings(**depr_args):
    """
     The purpose of this decorator is to allow passing old settings names to
     bears due to the heavy changes in their names.

     >>> @deprecate_settings(new='old')
     ... def run(new):
     ...     print(new)

     Now we can simply call the bear with the deprecated setting, we'll get a
     warning - but it still works!

     >>> run(old="Hello world!")
     The setting `old` is deprecated. Please use `new` instead.
     Hello world!
     >>> run(new="Hello world!")
     Hello world!

     The metadata for coala has been adjusted as well:

     >>> list(run.__metadata__.non_optional_params.keys())
     ['new']
     >>> list(run.__metadata__.optional_params.keys())
     ['old']

     You cannot deprecate an already deprecated setting. Don't try. It will
     introduce nondeterministic errors to your program.

     :param depr_args: A dictionary of settings as keys and their deprecated
                       names as values.
    """
    def _deprecate_decorator(func):

        def wrapping_function(*args, **kwargs):
            for arg, deprecated_arg in depr_args.items():
                if deprecated_arg in kwargs and arg not in kwargs:
                    print("The setting `{}` is deprecated. Please use `{}` "
                          "instead.".format(deprecated_arg, arg))
                    kwargs[arg] = kwargs[deprecated_arg]
                    del kwargs[deprecated_arg]
            return func(*args, **kwargs)

        new_metadata = FunctionMetadata.from_function(func)
        for arg, deprecated_arg in depr_args.items():
            new_metadata.add_alias(arg, deprecated_arg)
        wrapping_function.__metadata__ = new_metadata

        return wrapping_function

    return _deprecate_decorator
