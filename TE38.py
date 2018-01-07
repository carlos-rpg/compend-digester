"""TE38 functions that 'digest' the data files generated by Compend 2000.

A TE38 test with high speed data (HSD) recorded by Compend 2000 creates a
set of TSV files that follow this structure:

- test.TSV
- test-h001.TSV
- test-h002.TSV
- test-h003.TSV
- etc...

Where 'test' is a name chosen by the machine operator. If HSD capabilites are
not enabled, Compend 2000 just generates test.TSV

These data files are often cumbersome to work with, this module has functions
to deal with them in the public functions section (see module structure). In
order to work correctly, some requirements must be fullfilled:

- The original file names must be left intact.
- The files' line structure must be left also intact.
- The current working directory must be the same as the directory where the
  data files live.

It is mandatory to have Python v3.6 and Pandas v0.20 to work propertly.

MODULE STRUCTURE:
    01. CONSTANTS

    02. SUBROUTINES

    03. PUBLIC FUNCTIONS
"""


import shared_functions as sf
import pandas as pd
import numpy as np

# ####################################
# 01. CONSTANTS
# ####################################

# High speed data labels, default nomenclature
CYCLE = 'HSD Cycle'
STROKE = 'HSD Stroke'
TIME = 'HSD Time'
FRICTION = 'HSD Friction'
LOAD = 'HSD Load'
COF = 'HSD CoF'
DIRECTION = 'HSD Direction'

# High speed data labels, final nomenclature
HSD_FINAL_LABELS = ['Cycle',
                    'Stroke (mm)',
                    'Contact Potential (mV)',
                    'Friction (N)',
                    'Time (s)',
                    'Load (N)',
                    'CoF']


# ####################################
# 02. SUBROUTINES
# ####################################


def process_HSD_file(data_file,
                     initial_cycle,
                     initial_time,
                     initial_load,
                     frequency_adquisition):

    # Read the tsv data file excluding the first rows
    data = pd.read_csv(data_file, skiprows=4, sep='\t')

    # Center the stroke data so the max and min limits are equidistant to
    # zero
    limits_average = (data.loc[:, STROKE].max() +
                      data.loc[:, STROKE].min()) / 2

    data.loc[:, STROKE] -= limits_average

    # Calculate a time column
    final_time = initial_time + len(data) / frequency_adquisition
    data[TIME] = np.linspace(initial_time, final_time, len(data))

    # Calculate a movement direction column
    directions = data.loc[:, FRICTION].apply(np.sign)

    if directions.isin([-1]).any():
        data[DIRECTION] = directions
    else:
        sf.calculate_movement_directions(data, STROKE, DIRECTION)

    # Calculate the cycle every data row belongs to
    sf.calculate_cycle_values(data, DIRECTION, CYCLE, initial_cycle)

    # Filter out data that isn't located around the centre
    filtered_data = sf.filter_out_outer_values(data, STROKE, 0.1)

    # Forces in absolute value
    HSD_abs_friction = filtered_data.loc[:, FRICTION].abs()
    filtered_data.loc[:, FRICTION] = HSD_abs_friction

    # Group data by cycle and average values for each group
    averaged_data = filtered_data.groupby(CYCLE).mean()

    # Add a load column
    averaged_data[LOAD] = initial_load

    # Calculate a coefficient of friction column
    HSD_Friction = averaged_data.loc[:, FRICTION]
    HSD_Load = averaged_data.loc[:, LOAD]
    averaged_data[COF] = HSD_Friction / HSD_Load

    # Save data
    averaged_data.drop([DIRECTION, 'HSD Force Input'],
                       axis=1,
                       inplace=True)
    averaged_data.reset_index(inplace=True)
    return averaged_data


def concatenate_HSD_files(main_test_file, HSD_test_file, adquisition_rate):
    """Concatenates TE38 high speed data (HSD) files into one single file.

    The function scans through main_test_file looking for lines where high
    speed data adquisition started, and prepares it before concatenating.

    INPUT:
        main_test_file: an opened file object (_io.TextIOWrapper)
        HSD_test_file: an opened file object (_io.TextIOWrapper)
    """
    last_load = last_time = last_cycle = None

    for line in main_test_file:

        if line.startswith('\t'):
            last_load = extract_value(line, 'Load (N)')
            last_cycle = extract_value(line, 'Total Cycles')
            last_time = extract_value(line, 'Test Time')
        elif line.startswith('Fast data in'):
            HSD_file_name = sf.extract_HSD_file_name(line)
            HSD_data = process_HSD_file(HSD_file_name,
                                        last_cycle,
                                        last_time,
                                        last_load,
                                        adquisition_rate)
            HSD_data.to_csv(HSD_test_file, mode='a', header=False, index=False)
        else:
            break


def extract_value(line, column_label):
    """Extract a value from a TE38 data line. Which value is extracted is
    indicated by the column_label parameter. Assumes that line has the
    following format:

    "\tTime\tThis Step\tStep Time\tTest Time\t (...) \tStroke (mm)\t"

    INPUT:
        line: string, a TE38 data line
        column_label: string, a TE38 data column label

    OUTPUT:
        float or integer
    """
    columns = {'Test Time': (4, float),
               'Load (N)': (7, float),
               'Total Cycles': (11, int)}

    index, convert = columns[column_label]
    return convert(line.split('\t')[index])


# #####################################
# 03. PUBLIC FUNCTIONS
# #####################################


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
    file_name_with_extension = sf.extract_file_name(file_path, True)

    with open(file_name_with_extension) as source_file:
        sf.skip_lines(source_file, 'Test started at')

        data = pd.read_csv(source_file, sep='\t')
        real_number_of_columns = len(data.columns) - 2
        data.dropna(thresh=real_number_of_columns, inplace=True)
        data.dropna(axis=1, how='all', inplace=True)

    file_name = sf.extract_file_name(file_path, False)
    data.to_csv(f'{file_name}.csv', index=False)


def digest_HSD_test_files(file_path):
    """Reads all the test's high speed data (HSD) files from the information
    on the main test file (that is, the one that does not contain high speed
    data), and creates a new file that:
        - Removes text previous to the header.
        - Adds new data columns: cycle, load, and time.
        - Summarizes the data per cycle, and only with the values located
          around the center of the wear track.

    INPUT:
        file_path: string, an absolute or relative path to the main test file.
    """
    HSD_header = ','.join(HSD_FINAL_LABELS)
    file_name = sf.extract_file_name(file_path, False)
    file_name_with_extension = sf.extract_file_name(file_path, True)
    first_HSD_name = file_name_with_extension.replace('.', '-h001.')

    with open(first_HSD_name) as first_HSD_file:
        line = sf.skip_lines(first_HSD_file, 'High speed data')

    adquisition_rate = sf.extract_adquisition_rate(line)

    with open(file_name_with_extension) as source_file, \
        open(f'{file_name}_HSD.csv', 'w') as HSD_file:

        HSD_file.write(HSD_header + '\n')
        sf.skip_lines(source_file, 'Test started at')
        source_file.readline()
        concatenate_HSD_files(source_file, HSD_file, adquisition_rate)
