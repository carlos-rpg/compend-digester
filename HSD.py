import numpy as np
import pandas as pd


def calculate_movement_directions(data):
    """Calculate the movement direction for each row in the data set based
    upon the stroke values. This calculation method has the side effect of
    losing the first and the last data rows.

    INPUTS:
        data: DataFrame
    """
    empty_end_value = pd.Series(np.nan, index=[len(data)])
    stroke = data.loc[:, 'HSD Stroke'].append(empty_end_value)

    empty_start_value = pd.Series(np.nan, index=[-1])
    stroke_minus_1 = empty_start_value.append(data.loc[:, 'HSD Stroke'])

    stroke_minus_1.index += 1
    data['HSD Direction'] = (stroke - stroke_minus_1).apply(np.sign)
    data.dropna(inplace=True)
    data.index -= 1


def filter_out_outer_values(data, length_factor):
    """Filters out from the data the values that don't belong inside the
    wear track's central region. That region is defined by length_factor as
    a fraction of the wear track's length.

    INPUT:
        data: DataFrame
        length_factor: float between 0.0 and 1.0

    OUTPUT:
        DataFrame

    EXAMPLE:
        A length factor of 0.1 applied on a stroke length of 10 mm will filter
        out all values outside of  0.1 * 10 mm / 2 = 0.5 mm around the
        weartrack's center.
    """
    max_filter_limit = data.loc[:, 'HSD Stroke'].max() * length_factor / 2
    min_filter_limit = data.loc[:, 'HSD Stroke'].min() * length_factor / 2

    central_values = ((data.loc[:, 'HSD Stroke'] <= max_filter_limit) &
                      (data.loc[:, 'HSD Stroke'] >= min_filter_limit))

    return data.loc[central_values].copy()


def calculate_cycle_values(data, cycle_initial):
    """From the data in the HSD Direction column, the cycle that
    every data row belongs to is calculated and added as a new data column.
    The cycle count starts at the value provided in cycle_initial.

    INPUT:
        data: DataFrame
        cycle_initial: int
    """
    class Tracker:
        """This class acts as a data container for the assign_cycle function,
        since it's needed to keep track of some variables out of its scope.
        """
        cycle = cycle_initial
        initial_sign = data.get_value(0, 'HSD Direction')
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

    data['HSD Cycle'] = data.loc[:, 'HSD Direction'].apply(assign_cycle)


def process_data(data_file,
                 cycle_initial,
                 time_initial,
                 load_initial,
                 frequency_adquisition):

    # Read the tsv data file excluding the first rows
    data = pd.read_csv(data_file, skiprows=4, sep='\t')

    # Center the stroke data so the max and min limits are equidistant to
    # zero
    limits_average = (data.loc[:, 'HSD Stroke'].max() +
                      data.loc[:, 'HSD Stroke'].min()) / 2

    data.loc[:, 'HSD Stroke'] -= limits_average

    # Calculate a time column
    time_final = time_initial + len(data) / frequency_adquisition
    data['HSD Time'] = np.linspace(time_initial, time_final, len(data))

    # Calculate a movement direction column
    directions = data.loc[:, 'HSD Friction'].apply(np.sign)

    if directions.isin([-1]).any():
        data['HSD Direction'] = directions
    else:
        calculate_movement_directions(data)

    # Calculate the cycle every data row belongs to
    calculate_cycle_values(data, cycle_initial)

    # Filter out data that isn't located around the centre
    filtered_data = filter_out_outer_values(data, 0.1)

    # Forces in absolute value
    HSD_abs_friction = filtered_data.loc[:, 'HSD Friction'].abs()
    filtered_data.loc[:, 'HSD Friction'] = HSD_abs_friction

    # Group data by cycle and average values for each group
    averaged_data = filtered_data.groupby('HSD Cycle').mean()

    # Add a load column
    averaged_data['HSD Load'] = load_initial

    # Calculate a coefficient of friction column
    HSD_Friction = averaged_data.loc[:, 'HSD Friction']
    HSD_Load = averaged_data.loc[:, 'HSD Load']
    averaged_data['HSD CoF'] = HSD_Friction / HSD_Load

    # Save data
    averaged_data.drop(['HSD Direction', 'HSD Force Input'],
                       axis=1,
                       inplace=True)
    averaged_data.reset_index(inplace=True)
    return averaged_data
