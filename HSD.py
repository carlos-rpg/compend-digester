import numpy as np
import pandas as pd


def calculate_movement_directions(high_speed_data):
    """Calculate the movement direction for each row in the data set based
    upon the stroke values. This calculation method has the side effect of
    losing the first and the last data rows.

    INPUTS:
        high_speed_data: DataFrame 
    """
    stroke = high_speed_data.loc[:, 'HSD Stroke'].append(
                 pd.Series(np.nan, index=[high_speed_data.shape[0]]))

    stroke_minus_1 = pd.Series(np.nan, index=[-1]).append(
                         high_speed_data.loc[:, 'HSD Stroke'])

    stroke_minus_1.index += 1
    high_speed_data['HSD Direction'] = (stroke - stroke_minus_1).apply(np.sign)
    high_speed_data.dropna(inplace=True)
    high_speed_data.index -= 1


def process_high_speed_data_file(data_file):

    # Read the tsv data file excluding the first rows
    high_speed_data = pd.read_csv(data_file, skiprows=4, sep='\t')

    # Center the stroke data so the max and min limits are equidistant to
    # zero
    limits_average = (high_speed_data.loc[:, 'HSD Stroke'].max() +
                      high_speed_data.loc[:, 'HSD Stroke'].min()) / 2

    high_speed_data.loc[:, 'HSD Stroke'] -= limits_average

    # Calculate a movement direction column
    directions = high_speed_data.loc[:, 'HSD Friction'].apply(np.sign)

    if directions.isin([-1]).any():
        high_speed_data['HSD Direction'] = directions
    else:
        calculate_movement_directions(high_speed_data)

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
