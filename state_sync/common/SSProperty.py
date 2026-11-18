# -*- coding: utf-8 -*-


class SyncCond:
    NONE = 0
    OWN_ONLY = 1
    OWN_EXCEPT = 2


class SSProperty:

    def __init__(self, type=None, default=None, cond=SyncCond.NONE):
        self.type = type
        self.default = default
        self.cond = cond

        self.changed = False
        self.value = default

    def __get__(self, instance, owner):
        return self.value