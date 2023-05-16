from src import logger, process, util
import argparse
from colorama import Fore, Style

argParser = argparse.ArgumentParser()
argParser.add_argument("-i", "--input", help="List of files to input, can either be one 4 channel wave or two 2 channel waves", nargs="+", type=str)
argParser.add_argument("-o", "--output", help="Out file name, defaults to out.wav", nargs=1, type=str)
argParser.add_argument("-p", "--plot", help="Whether to display a plot", action="store_true")
argParser.add_argument("-g", "--gain", help="Gain to apply to the raw audio data (dB), default: +0 dB",
    nargs='?', type=float)
argParser.add_argument("-s", "--start", help="Number of seconds in to start at in the file, defaults to 0. Understands HH:MM:SS format",
    nargs='?', type=str)
argParser.add_argument("-l", "--length", help="Length from start to parse, defaults to -1 (the remainder of the file). Understands HH:MM:SS format",
    nargs='?', type=str)

args = argParser.parse_args()

# Defaults
if not args.gain:
    args.gain = 0
if not args.start:
    args.start = "0"
if not args.length:
    args.length = "-1"
if args.input and len(args.input) == 1:
    args.input.append(None)
if not args.output:
    args.output = "out.wav"

# dB to raw
args.ogain = args.gain
args.gain = 10 ** (args.gain / 10)

# Process times
args.start = util.parse_time(args.start)
args.length = util.parse_time(args.length)

# Invalid arguments
if not args.input:
    logger.fatal(f"No input file provided, use -i or --input to supply either a 4 channel wav or two 2 channel waves")
if len(args.input) not in [1, 2]:
    logger.fatal("You must provide an input wav file with 4 channels or two input wav files with 2 channels")
if args.start < 0:
    logger.fatal(f"Start time must be greater or equal to 0, got {args.start}")
if args.length < -1 or args.length == 0:
    logger.fatal(f"Length must be -1 or greater than 0, got {args.start}")

logger.title("Arguments")
logger.display(f"+ {Style.BRIGHT}Gain: {Style.NORMAL + Fore.YELLOW}+{args.ogain} dB (x{round(args.gain, 2)}){Style.RESET_ALL}")

if args.start != 0 or args.length > 0:
    logger.display(f"+ {Style.BRIGHT}Snippet: {Style.NORMAL + Fore.YELLOW}s{util.format_time(args.start)} + {util.format_time(args.length)}{Style.RESET_ALL}")
logger.display("")

logger.title(f"Processing: {args.input}")
process.process(args.output, args.input[0], args.input[1], args)
logger.display("Done!")
