# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os.path


def extract_file_name(file_path, extract_file_extension=True):
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
    return data_row.strip().replace('\t', ',')


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


def process_high_speed_data_file(data_file):
    
    # Read the tsv data file excluding the first rows
    high_speed_data = pd.read_csv(data_file, skiprows=4, sep='\t')
    
    # Center the stroke data so the max and min limits are equidistant to
    # zero
    limits_average = (high_speed_data.loc[:, 'HSD Stroke'].max() + 
                      high_speed_data.loc[:, 'HSD Stroke'].min()) / 2
    
    high_speed_data.loc[:, 'HSD Stroke'] -= limits_average
    
    # Calculate the movement direction for each data row
    HSD_stroke = high_speed_data.loc[:, 'HSD Stroke'].append(
                            pd.Series(np.nan, index=[high_speed_data.shape[0]]))

    HSD_stroke_minus_1 = pd.Series(np.nan, index=[-1]).append(
                            high_speed_data.loc[:, 'HSD Stroke'])
    
    HSD_stroke_minus_1.index += 1
    high_speed_data['HSD Direction'] = (HSD_stroke - HSD_stroke_minus_1).apply(np.sign)
    high_speed_data.dropna(inplace=True)
    high_speed_data.index -= 1

    # Calculate the cycle every data row belongs to
    class Tracker:
        cycle = 0
        initial_sign = high_speed_data.get_value(0, 'HSD Direction')
        former_sign = -initial_sign

    def assign_cycle(sign):
    
        if Tracker.initial_sign == sign and Tracker.former_sign != sign:
            Tracker.cycle += 1
    
        Tracker.former_sign = sign
        return Tracker.cycle
    
    high_speed_data['HSD Cycle'] = high_speed_data.loc[:, 'HSD Direction'].apply(assign_cycle)

    # Filter out data that isn't located around the centre 
    max_filter_limit = high_speed_data.loc[:, 'HSD Stroke'].max() * 0.05
    min_filter_limit = high_speed_data.loc[:, 'HSD Stroke'].min() * 0.05
    
    central_values = ((high_speed_data.loc[:, 'HSD Stroke'] <= max_filter_limit) & 
                      (high_speed_data.loc[:, 'HSD Stroke'] >= min_filter_limit))
    
    filtered_high_speed_data = high_speed_data.loc[central_values]
    
    # Forces in absolute value
    filtered_high_speed_data.loc[:, 'HSD Friction'].apply(np.abs)
    
    # Group data by cycle and average values for each group
    averaged_high_speed_data = filtered_high_speed_data.groupby('HSD Cycle').mean()

    # Save data
    averaged_high_speed_data.drop('HSD Direction', axis=1, inplace=True)
    averaged_high_speed_data.reset_index(inplace=True)
    data_file_name = data_file[:-4]
    averaged_high_speed_data.to_csv(f'{data_file_name}.csv', index=False)


def process_test_files(main_test_file_path):
    
    main_test_file_name = extract_file_name(main_test_file_path)
    with open(main_test_file_name) as origin_file:
        # Skip the initial rows until the real data begins
        for line in origin_file:
            if line.startswith('Test started at '):
                break
            else:
                continue
        
        file_name = extract_file_name(main_test_file_name, False)
        table_header = convert_data_row_to_csv_format(origin_file.readline())
        # Add the two new columns that will be extracted from the fast data
        # files
        table_header = ','.join([table_header, 
                                 'HSD Friction Force (N)',
                                 'HSD Friction Coeff\n'])

        with open(f'{file_name}.csv', 'w') as final_file:
            final_file.write(table_header)
            for line in origin_file:
                if line.startswith('\t'):
                    new_data_row = convert_data_row_to_csv_format(line)
                    # Commas mark the space for the two new columns, 
                    # followed by a new line char
                    final_file.write(''.join([new_data_row, ',,\n']))
                elif line.startswith('Fast data in'):
                    high_speed_file_name = extract_high_speed_file_name(line)
                    process_high_speed_data_file(high_speed_file_name)
                else:
                    break

