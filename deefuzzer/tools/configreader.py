__author__ = 'Dennis'


class ConfigReader():
    """
    Common tools for ingesting and reading dict-based configurations for an object
    """

    def __init__(self, configdict=None):
        self.__config = configdict

    def option(self, key, default=None, clean=True):
        """
        Gets a keyed configuration setting and returns it.  If a key is not found, returns the default value instead.
        Optionally cleans a return value (if it's a string).
        :param key: The configuration key to obtain.
        :param default: The default value to return if the key is not found
        :param clean: Whether or not a returned string should have .strip() applied
        :return:
        """
        try:
            if not isinstance(key, list):
                key = [key]
            r = self.__config
            for k in key:
                if not isinstance(r, dict) and not isinstance(r, list):
                    return default

                if isinstance(k, list):
                    f = False
                    for y in k:
                        if not f and y in r:
                            k = y
                            f = True

                if k not in r:
                    return default

                r = r[k]
            if isinstance(r, str):
                if clean:
                    r = r.strip()
                if not len(r):
                    return default
            return r
        except:
            pass
        return default
