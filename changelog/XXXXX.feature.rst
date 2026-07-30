Added :class:`pytest.IniOption`, a typed key for reading configuration options with :func:`config.getini <pytest.Config.getini>`.

The module registering an option can declare a key carrying the option's name and value type, and read the option through it. The value then has the declared type, so type checkers can check what is done with it — for example, that a ``match`` statement over an option with a fixed set of valid values covers all of them.

pytest's own enum-valued options are now read this way.
