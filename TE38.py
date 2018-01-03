# -*- coding: utf-8 -*-

import os.path
import HSD


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


def process_test_files(main_test_file_path):

    main_test_file_name = extract_file_name(main_test_file_path, True)
    with open(main_test_file_name) as origin_file:
        skip_initial_rows(origin_file, 'Test started at')
        table_header = convert_data_row_to_csv_format(origin_file.readline())
        # Add the two new columns that will be extracted from the fast data
        # files
        table_header = ','.join([table_header,
                                 'HSD Friction Force (N)',
                                 'HSD Friction Coeff\n'])

        file_name = extract_file_name(main_test_file_name, False)
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
                    HSD.process_high_speed_data_file(high_speed_file_name)
                else:
                    break
