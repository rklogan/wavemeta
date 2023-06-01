"""Module to batch extract sample rates from a set of wav files"""

# NERD STUFF
# All imports come standard with Python
# argparse parses command line arguments
# enum is used for bitmasking
# json to generate json files
# sys is used to get the command line arguments
# os is used to interact with the operating system
#    used to make paths cross compatable (Windows/Mac/Linux)
# wave lets us read wave files

import argparse
from enum import Enum
import json
import sys
import os
import wave

# Lazy short hand to indicate a line break in f-strings
ENDL = '\n'

# This is just a way to pack all of the data from the user request into one number
# For example:
#     0000 0000 0001 means I only want the number of channels
#     0000 0000 0010 means I only want the number of bytes per sample
#     0000 0000 0011 means I want the number of channels and the number of bytes per sample
#     And so on...
#     ?111 1111 1111 means I want all the available data
class Masks(Enum):
    def __lt__(self, other):
        return self.value < other.value
    def __le__(self, other):
        return self.value <= other.value
    def __gt__(self, other):
        return self.value > other.value
    def __ge__(self, other):
        return self.value >= other.value
    def __eq__(self, other):
        return self.value == other.value
    def __ne__(self, other):
        return self.value != other.value

    NONE            = 0
    NUM_CHANNELS    = 1
    BYTES           = 1 << 1
    BITS            = 1 << 2
    FREQ            = 1 << 3
    FREQK           = 1 << 4
    LENGTH          = 1 << 5
    LENGTH_M        = 1 << 6
    LENGTH_U        = 1 << 7
    NUM_FRAMES      = 1 << 8
    COMP_NAME       = 1 << 9
    COMP_TYPE       = 1 << 10
# END NERD STUFF

class WavMetadata():
    """Class to parse a wav file's metadata"""
    def __init__(self, filepath: str):
        """Initializor
        
        Args:
            filepath (str): path to the file to analyze
        """
        self.filepath = filepath
        self._populate_metadata()

    def _populate_metadata(self):
        """Populates the metadata from file."""
        with wave.open(self.filepath) as wav_file:
            self._bytes_per_sample = wav_file.getsampwidth()
            self._comp_name = wav_file.getcompname()
            self._comp_type = wav_file.getcomptype()
            self._num_channels = wav_file.getnchannels()
            self._num_frames = wav_file.getnframes()
            self._sample_freq = wav_file.getframerate()

    def as_dict(self, flags: int=0) -> dict:
        """Returns a python dict for the given flags
        
        Args:
            flags (int): The flags to unmask.

        Returns:
            (dict): A dictionary containing the requested data.
        """
        # null op if flags are negative, None of OOB; nothing was requested
        if flags < Masks.NONE.value or flags is None or flags > max(Masks).value:
            return None

        # Use 0 as a sentinal for all flags on, so more can be added later        
        if flags==0:
            for i in range(1, max(Masks).value + 1):
                flags |= 1 << i

        # populate the dictionary
        data = {}
        if flags & Masks.NUM_CHANNELS.value:
            data["Number Of Channels"] = self._num_channels
        if flags & Masks.BYTES.value:
            data["Bytes Per Sample"] = self._bytes_per_sample
        if flags & Masks.BITS.value:
            data["Bits Per Sample"] = self._bytes_per_sample * 8
        if flags & Masks.FREQ.value:
            data["Sample Rate (Hz)"] = self._sample_freq
        if flags & Masks.FREQK.value:
            data["Sample Rate (kHz)"] = self._sample_freq / 1000.0
        if flags & Masks.LENGTH.value:
            data["Time Between Samples (s)"] = 1.0 / self._sample_freq
        if flags & Masks.LENGTH_M.value:
            data["Time Between Samples (ms)"] = 1.0 / self._sample_freq * 10 ** 3
        if flags & Masks.LENGTH_U.value:
            data["Time Between Samples (us)"] = 1.0 / self._sample_freq * 10 ** 6
        if flags & Masks.NUM_FRAMES.value:
            data["Number Of Samples"] = self._num_frames
        if flags & Masks.COMP_NAME.value:
            data["Compression Name"] = self._comp_name
        if flags & Masks.COMP_TYPE.value:
            data["Compression Type"] = self._comp_type

        return data

    def as_csv_string(self, flags) -> str:
        """Generates a csv representation of the requested data.

        Args:
            flags(int): The bitmask of the flags to export

        Returns:
            (str): A String containing a csv representation of this object
        """
        data = ""
        for name, value in self.as_dict(flags).items():
            data += f'{name},{value}{ENDL}'
        return data

    def as_json_string(self, flags) -> str:
        """Generates a json representation of the requested data.

        Args:
            flags (int): The bitmask of the flags to export.
        
        Returns:
            (str): A string containing a json representation of this object.
        """
        return json.dumps(
            self.as_dict(flags),
            sort_keys=True,
            indent=4,
        )


def set_up_parser() -> argparse.ArgumentParser:
    """Sets up the argument parser.

    Returns:
        (argparse.ArgumentParser): A populated parser
    """

    parser = argparse.ArgumentParser(
        prog="Wav Data Extractor",
        description="Gets data from wav files",
        usage='wavemeta.py -i /path/to/source/files -o /path/to/dest/dir -of metadata -json --bits --sample_rate_k --num_samples'
    )

    parser.add_argument(
        '-i',
        '--input_directory',
        default='./',
        help='The directory containing the wav files. Defaults to current.',
    )
    parser.add_argument(
        '-o',
        '--output_file',
        default='./metadata',
        help='The output file without extension. Defaults to current/metadata.'
    )
    parser.add_argument(
        '-csv',
        '--csv',
        action='store_true',
        help='Set to write csv file.'
    )
    parser.add_argument(
        '-json',
        '--json',
        action='store_true',
        help='Set to write json file.'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Display the output data on the terminal.'
    )
    parser.add_argument(
        '-nc',
        '--num_channels',
        action='store_true',
        help="Set to get the number of channels in the file."
    )
    parser.add_argument(
        '-by',
        '--bytes',
        action='store_true',
        help="Set to get the number of bytes per sample."
    )
    parser.add_argument(
        '-bi',
        '--bits',
        action='store_true',
        help='set to get the number of bits per sample.'
    )
    parser.add_argument(
        '-sr',
        '--sample_rate',
        action='store_true',
        help='Set to get the sample rate in Hz.'
    )
    parser.add_argument(
        '-srk',
        '--sample_rate_k',
        action='store_true',
        help='Set to get the sample rate in kHz.'
    )
    parser.add_argument(
        '-l',
        '--length',
        action='store_true',
        help='Set to get the time between samples in seconds.'
    )
    parser.add_argument(
        '-lm',
        '--length_ms',
        action='store_true',
        help='Set to get the time between samples in milliseconds.'
    )
    parser.add_argument(
        '-lu',
        '--length_us',
        action='store_true',
        help='Set to get the time between samples in microseconds.'
    )
    parser.add_argument(
        '-ns',
        '--num_samples',
        action='store_true',
        help='Set to get the number of samples.'
    )
    parser.add_argument(
        '-ct',
        '--comp_type',
        action='store_true',
        help='Set to get the type of compression used on this file.'
    )
    parser.add_argument(
        '-cn',
        '--comp_name',
        action='store_true',
        help='Set to get the name of the compression used on this file.'
    )

    return parser

def make_flags(
        num_channels: bool = False,
        bytes_per_sample: bool = False,
        bits_per_sample: bool = False,
        sample_freq: bool = False,
        sample_freq_kHz: bool = False,
        sample_length: bool = False,
        sample_length_millis: bool = False,
        sample_length_micros: bool = False,
        num_frames: bool = False,
        comp_type: bool = False,
        comp_name: bool = False,
    ) -> int:
    """Generates a bit mask for the requested data
    
    Args:
        num_channels (bool): Get the number of audio channels. Defaults to False.
        bytes_per_sample (bool): Get the number of bytes used for each sample. Defaults to False.
        bits_per_sample (bool): Get the number of bits used for each sample. Defaults to False.
        sample_freq (bool): Get the sampling frequency in Hz. Defaults to False..
        sample_freq_kHz (bool): Get the sampling frequency in kHz. Defaults to False.
        sample_length (bool): Get the time between samples in seconds. Defaults to False.
        sample_length_millis (bool): Get the time between samples in milliseconds. Defaults to False.
        sample_length_micros (bool): Get the time between samples in microseconds. Defaults to False.
        num_frames (bool): Get the number of samples in the file. Defaults to False.
        comp_type (bool): Get the compression type used on the file. Defaults to False.
        comp_name (bool): Get the name of the compression used on the file. Defaults to False.

    Returns:
        (int): the bit mask
    """
    return (0
        | int(num_channels)
        | int(bytes_per_sample) << 1
        | int(bits_per_sample) << 2
        | int(sample_freq) << 3
        | int(sample_freq_kHz) << 4
        | int(sample_length) << 5
        | int(sample_length_millis) << 6
        | int(sample_length_micros) << 7
        | int(num_frames) << 8
        | int(comp_type) << 9
        | int(comp_name) << 10
    )

def convert_full_data_to_csv(full_data: dict) -> str:
    """Converts the dictionary to a csv string
    
    Args:
        (dict(dict(str, *))): Dict that looks like this
            {
                FILENAME:
                {
                    KEY: Value
                    KEY: Value
                    ...
                }
                ...
            }
        
    Returns:
        (str): A string that looks like:
            Filename,KEY,KEY,...\n
            FILENAME,Value,Value,...\n
            ...
    """
    # construct the headers
    header_row = []
    for filename in full_data:
        for candidate_header in full_data[filename]:
            if candidate_header not in header_row:
                header_row.append(candidate_header)
    header_row.sort()
    header_row.insert(0, 'Filename')

    # populate the rest of the table
    full_table = [header_row]
    num_cols = len(header_row)
    for filename, data in full_data.items():
        row = [None] * num_cols
        row[0] = filename
        for name, value in data.items():
            row[header_row.index(name)] = str(value)
        full_table.append(row)

    # convert to string
    tmp = []
    for row in full_table:
        tmp.append(",".join(row))
    return '\n'.join(tmp)

def main() -> None:
    """Main thread for execution.
    """
    # Collect data from the terminal
    parser = set_up_parser()
    args = parser.parse_args(sys.argv[1:])
    flags = make_flags(
        args.num_channels,
        args.bytes,
        args.bits,
        args.sample_rate,
        args.sample_rate_k,
        args.length,
        args.length_ms,
        args.length_us,
        args.num_samples,
        args.comp_type,
        args.comp_name,
    )

    # Load/prep the data
    full_data = {}
    for filename in os.listdir(args.input_directory):
        if filename.endswith('.wav'):
            wav = WavMetadata(os.path.join(args.input_directory, filename))
            full_data[filename[:-4]] = wav.as_dict(flags)
    
    #write the files
    if args.csv:
        csv_string = convert_full_data_to_csv(full_data)
        if args.verbose:
            # Lazy attempt to make the table look nice
            print(csv_string.replace(',', '\t'))

        with open(f'{args.output_file}.csv', 'w') as csv_file:
            csv_file.write(csv_string)
        
    if args.json:
        json_data = json.dumps(
            full_data,
            sort_keys=True,
            indent=4,
        )
        if args.verbose:
            print(json_data)

        with open(f'{args.output_file}.json', 'w') as json_file:
            json_file.write(json_data)


if __name__ == '__main__':
    main()
    