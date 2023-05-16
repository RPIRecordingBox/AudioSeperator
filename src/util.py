from src import logger


def parse_time(time: str) -> float:
    """
    Parse a time str, either in seconds or HH:MM:SS (or MMN:SS)
    Kills the program if there is an error in the string

    :param time:
    :return: Length in seconds
    """
    if ":" in time:
        args = time.split(":")
        while len(args) < 3:
            args = [0] + args
        if len(args) > 3:
            logger.fatal(f"Invalid time string {time}")
        args = [int(_) for _ in args]
        return args[0] * 3600 + args[1] * 60 + args[2]

    # Parse as number
    try:
        return float(time)
    except ValueError:
        logger.fatal(f"Invalid time string {time}")


def format_time(seconds: float) -> str:
    """
    Takes a number of seconds and formats it as HH:MM:SS
    :param seconds:
    :return: Formatted time
    """
    hours = int(seconds // 3600)
    seconds -= hours * 3600
    min = int(seconds // 60)
    seconds -= min * 60
    seconds = str(int(seconds))
    hours = str(hours)
    min = str(min)

    return f"{hours.zfill(2)}:{min.zfill(2)}:{seconds.zfill(2)}"
