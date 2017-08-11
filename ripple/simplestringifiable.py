class SimpleStringifiable(object):
    """
    A SimpleStringifiable object is an object which can have its __repr__ and
    __str__ methods defined in a generic way. Generally, this is a good default
    implementation of __str__ and __repr__ for objects which have no potential
    for recursive representations involving refs back and forth between
    objects.

    Example usage:

    >>> class A(SimpleStringifiable):
    >>>     def __init__(self, val1, val2):
    >>>         self.val1 = val1
    >>>         self.val2 = val2
    >>>
    >>> x = A('hello world', 'goodnight moon')
    >>> repr(x)
    A(val1='hello world',val2='goodnight moon')
    >>> print(str(x))
    A:
        val1: hello world
        val2: goodnight moon
    """
    def __repr__(self):
        """
        repr of a SimpleStringifiable looks like a constructor invocation
        """
        key_sorted_dict = sorted(self.__dict__.items())
        strified_dict = ','.join(
            "{0}={1}".format(k, repr(v))
            for (k, v) in key_sorted_dict)
        return "{0}({1})".format(self.__class__.__name__, strified_dict)

    def __str__(self):
        """
        str of a SimpleStringifiable is for long-form logging and strs in an
        indented format as a multiline string
        """
        output = "{0}:".format(self.__class__.__name__)
        key_sorted_dict = sorted(self.__dict__.items())
        for (k, v) in key_sorted_dict:
            output = "{0}\n    {1}: {2}".format(
                output, k, repr(v))

        return output
