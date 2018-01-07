import numpy as np
import pandas as pd
import os.path
import re


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


def convert_to_csv_format(data_row):
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


def extract_HSD_file_name(line):
    """Takes a Compend 2000 data line that signals the start of high speed
    data adquisition, and returns the name of the data file where it has been
    stored.

    INPUT:
        line: string

    OUTPUT:
        string

    EXAMPLES:
        The string 'Fast data in       =HYPERLINK("n762a_castrol_2-h001.tsv")'
        will return 'n762a_castrol_2-h001.tsv'
    """
    initial_index = line.find('"') + 1
    final_index = line.find('"', initial_index)
    return line[initial_index:final_index]


def skip_lines(file, last_skippable_line):
    """Skips lines in an opened file until last_skippable_line is encountered,
    the last line to be ignored can be given as a string that represents
    the line's beginning, or as an integer that represents the index
    of the last line to be skipped (zero based).

    The function modifies inplace the file object, and returns the last line
    to be skipped.

    INPUT:
        file: an opened file object (_io.TextIOWrapper)

        last_skippable_line: string or positive integer

    OUTPUT:
        string

    EXAMPLE:
        If a line represented by the string "High speed data using 1000 Hz
        Trigger Frequency" is encountered, the function will stop skipping
        lines if the keyword last_skippable_line has a value like, but not
        limited to:
            - "High"
            - "High speed data"
            - "High speed data using 1000 Hz Trigger Frequency"

        If the line's index position is known (for instance, it's the line no 4
        in a text editor), setting a value last_skippable_line=3 will have the
        same effect.
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


def extract_adquisition_rate(line):
    """Extracts the adquisition rate in Hz from the line of text that
    is supposed to contain that information. Raises an exception if it is not
    found.

    INPUT:
        line: string, file line containing a number followed by "Hz"

    OUTPUT:
        integer

    EXAMPLE:
        From the string 'High speed data using 1000 Hz Trigger Frequency.'
        the function will return 1000.
    """
    match = re.search(r'(\d+) Hz', line)

    if match:
        return int(match.group(1))
    else:
        raise RuntimeError(f'Adquisition rate not found in line: {line}')


def calculate_movement_directions(data, stroke_label, direction_label):
    """Calculate the movement direction for each row in the data set based
    upon the stroke values. This calculation method has the side effect of
    losing the first and the last data rows.

    INPUTS:
        data: DataFrame.

        stroke_label: string, label of the stroke column in data.

        direction_label: string, label for the new direction column.
    """
    empty_end_value = pd.Series(np.nan, index=[len(data)])
    stroke = data.loc[:, stroke_label].append(empty_end_value)

    empty_start_value = pd.Series(np.nan, index=[-1])
    stroke_minus_1 = empty_start_value.append(data.loc[:, stroke_label])

    stroke_minus_1.index += 1
    data[direction_label] = (stroke - stroke_minus_1).apply(np.sign)
    data.dropna(inplace=True)
    data.index -= 1


def filter_out_outer_values(data, stroke_label, length_factor):
    """Filters out from the data the values that don't belong inside the
    wear track's central region. That region is defined by length_factor as
    a fraction of the wear track's length.

    INPUT:
        data: DataFrame

        stroke_label: string, label of the stroke column in data

        length_factor: float between 0.0 and 1.0

    OUTPUT:
        DataFrame

    EXAMPLE:
        A length factor of 0.1 applied on a stroke length of 10 mm will filter
        out all values outside of  0.1 * 10 mm / 2 = 0.5 mm around the
        weartrack's center.
    """
    max_filter_limit = data.loc[:, stroke_label].max() * length_factor / 2
    min_filter_limit = data.loc[:, stroke_label].min() * length_factor / 2

    central_values = ((data.loc[:, stroke_label] <= max_filter_limit) &
                      (data.loc[:, stroke_label] >= min_filter_limit))

    return data.loc[central_values].copy()


def calculate_cycle_values(data, direction_label, cycle_label, initial_cycle):
    """The cycle every data row belongs to is calculated from the direction
    column and added as a new data column.
    The cycle count starts at the value provided in initial_cycle.

    INPUT:
        data: DataFrame

        direction_label: string, label of the direction column in data.

        cycle_label: string, label for the new cycle column.

        initial_cycle: integer
    """
    class Tracker:
        """This class acts as a data container for the assign_cycle function,
        since it's needed to keep track of some variables out of its scope.
        """
        cycle = initial_cycle
        initial_sign = data.get_value(0, direction_label)
        former_sign = -initial_sign

    def assign_cycle(sign):
        """Gives a cycle value to the sign provided, relative to the initial
        sign on the data and the sign assigned just before.

        INPUT:
            sign: integer with values 1 or -1

        OUTPUT:
            integer
        """
        if Tracker.initial_sign == sign and Tracker.former_sign != sign:
            Tracker.cycle += 1

        Tracker.former_sign = sign
        return Tracker.cycle

    data[cycle_label] = data.loc[:, direction_label].apply(assign_cycle)
