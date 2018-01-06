import os.path
import HSD
import re
import pandas as pd


def extract_file_name(file_path, extract_file_extension):
    """Takes a file route and returns the name with or without its extesion.
    This function is OS independent.

    INPUT:
        file_path: string
        extract_file_extension: boolean

    OUTPUT:
        string representing the file name

    EXAMPLES:
        'bar.txt', './bar.txt', 'C:\foo\bar.txt' or './foo/bar.txt' will
        all return 'bar.txt' with the default keyword, otherwise returns 'bar'
    """
    file_name_with_extension = os.path.split(file_path)[-1]

    if extract_file_extension:
        return file_name_with_extension
    else:
        extension_beginning = file_name_with_extension.rfind('.')
        return file_name_with_extension[:extension_beginning]


def convert_data_row_to_csv_format(data_row):
    """Takes a data row from a Compend 2000 data file, removes the initial
    and trailing tabs, and substitutes the rest of the tabs for commas.

    INPUT:
        data_row: string

    OUTPUT:
        string

    EXAMPLES:
        '\tvalue 1\tvalue 2\tvalue 3\tvalue 4\tvalue 5\t' returns
        'value 1,value 2,value 3,value 4,value 5'
    """
    return str.join('', [data_row.strip().replace('\t', ','), '\n'])


def extract_high_speed_file_name(text_line):
    """Takes a data row that signals the start of high speed data adquisition
    from a Compend 2000 data file, and returns the name of the data file where
    it has been stored.

    INPUT:
        text_line: string

    OUTPUT:
        string

    EXAMPLES:
        The string 'Fast data in       =HYPERLINK("n762a_castrol_2-h001.tsv")'
        will return 'n762a_castrol_2-h001.tsv'
    """
    initial_index = text_line.find('"') + 1
    final_index = text_line.find('"', initial_index)
    return text_line[initial_index:final_index]


def skip_initial_rows(file, last_skippable_line):
    """Skips the first lines in an opened file, the last line to be ignored
    can be given as a string that represents totally o partially the line, or
    an integer that represents the last line to be skipped (zero based).

    The function modifies inplace the file object, and returns the last line
    to be skipped.

    INPUT:
        file: a file objext (_io.TextIOWrapper)
        last_skippable_line: str or int

    OUTPUT:
        str
    """
    if isinstance(last_skippable_line, str):
        for line in file:
            if line.startswith(last_skippable_line):
                return line
            else:
                continue
    elif isinstance(last_skippable_line, int):
        for line_number in range(last_skippable_line):
            line = file.readline()
        return line
    else:
        raise TypeError('last_skippable_line is not a string or integer')


def extract_value(line, field):

    fields = {'Total Cycles': (11, int),
              'Test Time': (4, float),
              'Load (N)': (7, float)}

    index, convert = fields[field]
    return convert(line.split('\t')[index])


def extract_adquisition_frequency(file):

    pattern = re.compile(r'^[\w\s]*?(\d+)')
    for line in file:
        match = pattern.search(line)
        if match:
            return int(match.group(1))


def digest_main_test_file(file_path):
    """Clean the main test file (that is, the one that does not contain high
    speed data) by removing these elements:
        - Data previous to the header
        - Blank space
        - "test started" and "Test finished" lines
        - Tabs at the beginning and end of data rows
        - "Fast data in..." lines

    Leaves a clean and tidy table to work with.

    INPUT:
        file_path: string, an absolute or relative path to the main test file
    """
    file_name_with_extension = extract_file_name(file_path, True)

    with open(file_name_with_extension) as source_file:
        skip_initial_rows(source_file, 'Test started at')

        data = pd.read_csv(source_file, sep='\t')
        real_number_of_columns = len(data.columns) - 2
        data.dropna(thresh=real_number_of_columns, inplace=True)
        data.dropna(axis=1, how='all', inplace=True)

    file_name = extract_file_name(file_path, False)
    data.to_csv(f'{file_name}.csv', index=False)


def digest_HSD_test_files(file_path, adquisition_rate):
    """Reads all the test's high speed data (HSD) files from the information
    on the main test file (that is, the one that does not contain high speed
    data), and creates a new file that:
        - Removes text previous to the header.
        - Adds new data columns: cycle, load, and time.
        - Summarizes the data per cycle, and only with the values located
          around the center of the wear track.

    INPUT:
        file_path: string, an absolute or relative path to the main test file.

        adquisition_rate: int, data adquisition frequency in Hz.
    """
    HSD_header = ','.join(['Cycle',
                           'Stroke (mm)',
                           'Contact Potential (mV)',
                           'Friction (N)',
                           'Time (s)',
                           'Load (N)',
                           'CoF'])

    file_name = extract_file_name(file_path, False)
    file_name_with_extension = extract_file_name(file_path, True)

    with open(file_name_with_extension) as source_file, \
        open(f'{file_name}_HSD.csv', 'w') as HSD_file:

        HSD_file.write(HSD_header + '\n')
        skip_initial_rows(source_file, 'Test started at')
        source_file.readline()

        last_load = last_time = last_cycle = None

        for line in source_file:

            if line.startswith('\t'):
                last_load = extract_value(line, 'Load (N)')
                last_cycle = extract_value(line, 'Total Cycles')
                last_time = extract_value(line, 'Test Time')

            elif line.startswith('Fast data in'):
                HSD_file_name = extract_high_speed_file_name(line)
                HSD_data = HSD.process_data(HSD_file_name,
                                            last_cycle,
                                            last_time,
                                            last_load,
                                            adquisition_rate)
                HSD_data.to_csv(HSD_file, mode='a', header=False, index=False)

            else:
                break
