from scipy.ndimage import uniform_filter1d, median_filter
from scipy.io import wavfile
import scipy.signal
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr
import nussl

from src import logger

NPERSEG = 2048
BANDPASS_FOR_LOUDNESS_CALC = [500, 2000]
LOUDNESS_FILTER_SIZE = 11

BLOCK_SIZE_S = 0.2 # Block size in seconds
ACTIVE_SPEAKER_MEDIAN_FILTER_SIZE = 5


def process(name: str, chan1: str, chan2: str, args):
    """
    Process a file with a given name
    :param name: Output file name
    :param chan1: Wave file with channels 0 and 1
    :param chan2: Wave file with channels 1 and 2
    :param args: Args from argsparse
    """

    # TODO: apply gain

    name = name.rsplit(".", 1)[0] # Get name without extension

    logger.log("+ Loading channel data... ", end="")
    logger.start_timer()

    # Assumption (1): channels 0 and 1 correspond to a nearby mic pair, and 2 and 3 correspond
    # to another pair. This assumption is used once later on
    # Two file case
    if chan2 != None:
        rate, data1 = wavfile.read(chan1)
        rate, data2 = wavfile.read(chan2)
        channels = [
            data1[:, 0], data1[:, 1],
            data2[:, 0], data2[:, 1]
        ]
    else:
        rate, data = wavfile.read(chan1)
        channels = [
            data[:, 0], data[:, 1],
            data[:, 2], data[:, 3]
        ]

    # Crop
    channels = [c[int(args.start * rate):int((args.start + args.length) * rate)] for c in channels]
    logger.log(f"4 channels loaded ({logger.stop_timer()}s)")

    # Apply gain:
    if args.gain != 0:
        largest = np.abs(channels).max()
        if largest * args.gain >= 2 ** 15:
            max_gain = 10 * np.log(2 ** 15 / largest)
            logger.warn(f"Provided gain of {args.ogain} dB will result in clipping! Recommended max value: {round(max_gain, 2)} dB")

        channels = [c * args.gain for c in channels]


    # Compute the average loudness (over a small window) of each channel
    # using the STFT and an average filter
    channel_loudness_smoothed = []

    for i in range(4):
        f, _, Zxx = scipy.signal.stft(channels[i], rate, nperseg=NPERSEG)
        start_freq_i = next((index for index, value in enumerate(f) if value > BANDPASS_FOR_LOUDNESS_CALC[0]), -1)
        end_freq_i   = next((index for index, value in enumerate(f) if value > BANDPASS_FOR_LOUDNESS_CALC[1]), -1)

        if start_freq_i < 0 or end_freq_i < 0:
            raise ValueError(f"Bandpass parameters {BANDPASS_FOR_LOUDNESS_CALC[0]} to {BANDPASS_FOR_LOUDNESS_CALC[1]} are too broad, failed to find satisfying range")

        Zxx = np.sum(Zxx[start_freq_i:end_freq_i, :], axis=0)
        Zxx = uniform_filter1d(np.abs(Zxx), size=LOUDNESS_FILTER_SIZE)
        channel_loudness_smoothed.append(Zxx)

        if args.plot:
            plt.plot(np.linspace(args.start, args.start + args.length, len(Zxx)), Zxx / (NPERSEG // 2) - i * 2)


    # Estimate speaker
    # ----------------
    BLOCK_SIZE = int(rate * BLOCK_SIZE_S) // (NPERSEG // 2)

    def is_quiet(snippet):
        """
        Determine if a snippet has someone talking
        :param snippet: Array of numbers
        :return:
        """
        return np.mean(snippet) < 8 # Mean makes it invariant of length, may not work for block sizes that are too large

    block_count = len(channel_loudness_smoothed[0]) // BLOCK_SIZE
    active_speaker_lines = np.zeros((4, block_count))

    for block in range(0, block_count):
        # Correlations stores pairs of channels that have a high correlation
        # key: "a,b" where a and b are integers in 0,1,2,3, value: pearson correlation coeff (0 to 1)
        correlations = {}

        for i in range(4):
            for j in range(i + 1, 4):
                a = channel_loudness_smoothed[i][block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE]
                b = channel_loudness_smoothed[j][block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE]

                if is_quiet(a) or is_quiet(b):
                    continue

                c = pearsonr(a, b)[0]
                if c > 0.85:
                    correlations[f"{i},{j}"] = c

        speaking = [] # List of speaker groups, ie [[1,2,3]] means 1,2, and 3 are active with high corr.

        # Fast check based on assumption (1):
        # This is the only way you can have two distinct speaker groups
        # (assuming from assum. (1) that groupings like 1,2, 0,4 can't occur)
        # Thus this is the only check for multiple speaker groups, the rest
        # just assume a single large group like [[0,1,2]]
        if len(correlations.keys()) == 2 and "0,1" in correlations and "2,3" in correlations:
            speaking = [[0,1], [2,3]]
        else:
            # Speaking is set of whoever is in the keys
            keys = correlations.keys()
            s = set()
            for k in keys:
                a, b = k.split(",")
                s.add(int(a))
                s.add(int(b))
            if len(s):
                speaking = [list(s)]

        # Remove any group from speaking that isn't not quiet
        possible_speakers = set([i for i in range(4) if not is_quiet(channel_loudness_smoothed[i][block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE])])
        for chunk in speaking:
            # For each group save loudest chunk, remove others
            # Assumption (2): loudest speaker in a group is the true speaker,
            # rest are crosstalk
            loudest = -1
            loudest_val = -1
            for c in chunk:
                loudness = np.sum( channel_loudness_smoothed[c][block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE] )
                if loudness > loudest_val:
                    loudest = c
                    loudest_val = loudness

            for c in chunk:
                if c != loudest:
                    possible_speakers.remove(c)

        for speaker in possible_speakers:
            active_speaker_lines[speaker][block] = 1

    for i in range(4):
        active_speaker_lines[i] = median_filter(active_speaker_lines[i], size=ACTIVE_SPEAKER_MEDIAN_FILTER_SIZE, cval=0, mode='constant')

    if args.plot:
        for i in range(4):
            plt.plot(np.linspace(args.start, args.start + args.length, len(active_speaker_lines[0])), active_speaker_lines[i] - i * 2)

    # Determine runs of overlapping speakers (2 or more at a time, aka active_speaker_lines summed over speakers
    # is 2 or more. overlap is a binary signal of whether two or more are speaking at a time)
    overlap = np.sign(active_speaker_lines[0] + active_speaker_lines[1] + active_speaker_lines[2] + active_speaker_lines[3] - 1)
    overlap[overlap < 0] = 0
    overlap_runs = np.split(overlap, np.where(np.diff(overlap) != 0)[0]+1)
    run_i = 0

    for run in overlap_runs:
        # Ensure run length > STFT window length
        # Also ensure run is a 1 and not a 0 (0 meaning one or less speakers active)
        if run[0] == 1 and len(run) > 16: # Overlap, perform DUET
            # Create an n-channel wav file where n is the number of speakers
            # that speak at least once in the run
            possible = [speaker for speaker in range(4) if active_speaker_lines[speaker][run_i]]
            chan_runs = np.array([
                channels[speaker][(NPERSEG // 2) * BLOCK_SIZE * run_i:(NPERSEG // 2) * BLOCK_SIZE * (run_i + len(run))] for speaker in possible
            ], dtype=np.int16)

            signal2 = nussl.AudioSignal(
                audio_data_array=chan_runs, sample_rate=rate)
            signal2.embed_audio()
            
            # Sep with DUET
            separator = nussl.separation.spatial.Duet(
                signal2, num_sources=chan_runs.shape[0])
            estimates = separator()

            for pi, p in enumerate(possible):
                def similarity(est):
                    """
                    Compute similarity between estimate and
                    original recorded snippet for that channel
                    """
                    org = chan_runs[pi]

                    # Project estimate onto original
                    score = np.dot(est, org) / np.linalg.norm(est)
                    return score

                ests = []
                for est in estimates:
                    for i in range(chan_runs.shape[0]):
                        # Estimate is scaled from -1 to 1, rescale to 16 bit range
                        ests.append(est.audio_data[i, :] * 2 ** 16)

                est_best = max(ests, key=similarity)
                channels[p][(NPERSEG // 2) * BLOCK_SIZE * run_i:(NPERSEG // 2) * BLOCK_SIZE * (run_i + len(run))] = est_best

        run_i += len(run)

    # Zero out everything when not speaking
    for block in range(0, block_count - 1):
        for speaker in range(4):
            channels[speaker][(NPERSEG // 2) * block * BLOCK_SIZE:(NPERSEG // 2) * (block + 1) * BLOCK_SIZE] *= int(active_speaker_lines[speaker][block])

    if args.plot:
        plt.plot(np.linspace(args.start, args.start + args.length, len(overlap)), overlap + 2)
        plt.show()

    
    # Save output
    # --------------------------------
    logger.log("+ Saving output... ", end="")
    logger.start_timer()

    channels = np.array(channels, dtype=np.int16).T
    scipy.io.wavfile.write("cropped-merge.wav", rate, channels)

    logger.log(f"done ({logger.stop_timer()}s)")
