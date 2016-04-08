import re


def convert(string):
    """
    Covert list in order asc
    :param  str string:
    :return: int
    """
    return int("".join(re.findall("\d*", string)))
