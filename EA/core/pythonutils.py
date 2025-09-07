try:
    import _pythonutils
except ImportError:

    class _pythonutils:

        @staticmethod
        def try_highwater_gc():
            return False

        @staticmethod
        def change_gc_policy(*args):
            return False
try_highwater_gc = _pythonutils.try_highwater_gctry:
    change_gc_policy = _pythonutils.change_gc_policy
except AttributeError:

    def change_gc_policy(*args):
        pass
