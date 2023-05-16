from colorama import Fore, Back, Style
from src import config
import sys, time

LOGGER_ENABLED = config.LOGGER_ENABLED
timer = 0


def start_timer():
    """
    Start timer for display
    """
    global timer
    timer = time.time()


def stop_timer() -> str:
    """
    Stop timer and return time elapsed in seconds
    :return: time elapsed, rounded to 3 digits
    """
    return "{:.3f}".format(time.time() - timer)


def fatal(msg: str, end="\n"):
    """
    Same as error() but terminates the program
    Always prints regardless if enabled or not
    :param msg: String to print
    """
    print(Fore.RED + msg + Style.RESET_ALL, end=end)
    sys.exit(1)


def error(msg: str, end="\n"):
    """
    Print red text
    :param msg: Message to print
    """
    if not LOGGER_ENABLED: return
    print(Fore.RED + msg + Style.RESET_ALL, end=end)


def warn(msg: str, end="\n"):
    """
    Print yellow text
    :param msg: Message to print
    """
    if not LOGGER_ENABLED: return
    print(Fore.YELLOW + msg + Style.RESET_ALL, end=end)


def log(msg: str, end="\n"):
    """
    Print gray text
    :param msg: Message to print
    """
    if not LOGGER_ENABLED: return
    print(Fore.LIGHTBLACK_EX + msg + Style.RESET_ALL, end=end)


def display(msg: str, end="\n"):
    """
    Print regular text
    :param msg: Message to print
    """
    if not LOGGER_ENABLED: return
    print(msg, end=end)


def title(msg: str, end="\n"):
    """
    Print prominent blue text
    :param msg: Message to print
    """
    if not LOGGER_ENABLED: return
    print(Back.LIGHTBLUE_EX + Fore.WHITE + msg + Style.RESET_ALL, end=end)


def start_progressbar():
    """
    Usage: store = logger.start_progressbar()
    Prints the beginning of the progressbar
    """
    if not LOGGER_ENABLED: return
    print(Fore.LIGHTGREEN_EX + "  " + ("_" * config.PROGRESS_BAR_LENGTH) + "  0%" + Style.RESET_ALL, end="\r", flush=True)
    return [0, 0]


def update_progressbar(store, percentage):
    """
    Usage: store = logger.update_progressbar(store, new percentage (0 to 1))
    Prints new segements as needed

    :param store: Store var
    :param percentage: Progress from 0 to 1
    :return: New store value
    """
    if not LOGGER_ENABLED: return
    rounded = round(100 * percentage)

    if rounded > store[0]:
        print("\r", end="", flush=True)
        print("  " + Back.LIGHTGREEN_EX + (" " * store[1]) + \
                 Style.RESET_ALL + Fore.LIGHTGREEN_EX + ("_" * (config.PROGRESS_BAR_LENGTH - store[1])) + \
                 f"  {rounded}%" + Style.RESET_ALL,
                 end="")

        if percentage >= store[1] / config.PROGRESS_BAR_LENGTH:
            return [rounded, store[1] + 1]
    return [rounded, store[1]]
