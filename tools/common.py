import os
import sys
import thread
import threading
import ctypes

# For OS specific tasks
IS_DARWIN = sys.platform == 'darwin'
IS_LINUX = 'linux' in sys.platform
IS_WINDOWS = sys.platform == 'win32'


def debug(s):
    sys.stdout.write(str(s))
    sys.stdout.flush()


def listdir(path):
    # type: (str) -> list
    if not os.path.isdir(path):
        return []
    return sorted(os.listdir(path), key=lambda s: s.lower())


def try_delete(path):
    try:
        os.remove(path)
    except OSError:
        pass


def stdout_flush(s):
    sys.stdout.write(s)
    sys.stdout.flush()


class TimeoutError(Exception):
    pass


def interrupt_main_thread():
    """Extremely dangerous and discouraged. Interrupts the main thread."""
    main_thread_id = threading.main_thread().ident
    if main_thread_id is None:
        print("Could not get main thread ID.")
        return

    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(main_thread_id), ctypes.py_object(KeyboardInterrupt)
    )

    if res == 0:
        print("Invalid thread ID.")
    elif res > 1:
        # Re-raise the exception if something bad happened.
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(main_thread_id), None)
        print("PyThreadState_SetAsyncExc failed.")


class Timeout(object):
    """
    A timeout context manager that uses a thread based timer instead of SIGALRM

    Usage example:
        with Timeout(5):  # 5 seconds
            do_slow_stuff()

    By default when a timeout occurs, a TimeoutError will be raised
    To have the block exit silently, use TimeoutSilent

    NOTE: this can only interrupt the main thread, so using this
    from other threads will not work
    """
    raise_timeout = True  # Raises a TimeoutError if this is True

    def __init__(self, seconds):
        self.timer = threading.Timer(seconds, interrupt_main_thread)
        self.timed_out = False

    def __enter__(self):
        self.timer.start()
        return self

    def __exit__(self, extype, ex, trace):
        if extype is None:
            return self.timer.cancel()
        elif extype is KeyboardInterrupt:
            # The timer sent an interrupt after the timeout
            self.timed_out = True

            # Option to silently timeout
            if not self.raise_timeout:
                return True

            # raise a TimeoutError in place of the interrupt
            raise TimeoutError('Timed out after {}s'.format(self.timer.interval))


class TimeoutSilent(Timeout):
    raise_timeout = False
