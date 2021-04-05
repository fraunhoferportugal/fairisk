import pandas as pd
import datetime
import numpy as np
import math

from fairiskdata.utils.time_parsers import safe_date_parse


class Resampler:

    FREQUENCY = {
        'YEARLY': 0,
        'MONTHLY': 1,
        'WEEKLY': 2,
        'DAILY': 3
    }

    def __init__(self,
                 time_interval: pd.Interval,
                 frequency: str):
        self.time_interval = time_interval
        self.frequency = frequency

        self.frequency_alias = self._get_frequency_alias(frequency)
        self.timestamp_strformat = self._get_timestamp_strformat(frequency)

        self.interval_index = pd.interval_range(time_interval.left, time_interval.right,
                                                freq=self.frequency_alias, closed='left')

    def resample(self,
                 time_series: pd.Series,
                 current_frequency: str,
                 series_type: str):

        def validate_series_type():
            if series_type in ['NEW', 'TOTAL', 'CURRENT']:
                return
            else:
                raise ValueError('Unknown series type %s' % series_type)

        if self.FREQUENCY[current_frequency] >= self.FREQUENCY[self.frequency]:
            validate_series_type()
            return self._undersample(time_series, series_type)
        elif self.FREQUENCY[current_frequency] < self.FREQUENCY[self.frequency]:
            validate_series_type()
            return self._oversample(time_series, series_type)
        else:
            raise ValueError('Unknown current frequency %s' % current_frequency)

    def _undersample(self, time_series, series_type):

        new_time_series = pd.Series(index=[datetime.datetime.strftime(i.left, self.timestamp_strformat)
                                           for i in self.interval_index])

        parsed = list(map(safe_date_parse, time_series.index.tolist()))

        for i in self.interval_index:

            def time_interval_validation(p):
                if isinstance(p, pd.Interval):
                    return i.overlaps(p)
                return p in i

            val = list(map(time_interval_validation, parsed))
            if any(val):

                # Get time delta of i
                i_time_delta = i.right - i.left
                # Get time delta of overlap with i
                overlap = np.array(parsed)[val]
                if isinstance(overlap[-1], pd.Interval):
                    overlap_time_delta = overlap[-1].right - overlap[0].left + pd.Timedelta(days=1)
                else:
                    overlap_time_delta = overlap[-1] - overlap[0] + pd.Timedelta(days=1)

                # Only perform operations if overlap has the expected size (otherwise, there is missing data)
                if i_time_delta.days <= overlap_time_delta.days:
                    if series_type == 'NEW':
                        x = time_series.values[val]
                        value = x.sum()
                    elif series_type == 'TOTAL':
                        value = time_series.values[val][-1]
                    else:  # 'CURRENT'
                        x = time_series.values[val]
                        value = x.mean()
                else:
                    value = np.nan

                new_time_series[datetime.datetime.strftime(i.left, self.timestamp_strformat)] = value

        return new_time_series

    def _oversample(self, time_series, series_type):
        new_time_series = pd.Series(index=[datetime.datetime.strftime(i.left, self.timestamp_strformat)
                                           for i in self.interval_index])

        big_intervals = list(map(safe_date_parse, time_series.index.tolist()))

        for idx_big_i, big_i in enumerate(big_intervals):

            def time_interval_validation(small_i):
                if isinstance(small_i, pd.Interval):
                    return small_i.overlaps(big_i)
                return small_i in big_i

            idx_bool_overlap_small_i = list(map(time_interval_validation, self.interval_index))

            if series_type == 'CURRENT':
                if any(idx_bool_overlap_small_i):
                    new_time_series[idx_bool_overlap_small_i] = time_series.values[idx_big_i]

            elif series_type == 'NEW':
                if any(idx_bool_overlap_small_i):
                    total_new = time_series.values[idx_big_i]

                    if not math.isnan(total_new):

                        # Get number of days of current big interval
                        n_days_big_i = (big_i.right - big_i.left).round('d').days

                        # Get number of NEW / day
                        new_per_day = int(total_new / n_days_big_i)

                        # Add number of NEW * n days of small interval in current big interval
                        def number_of_overlapping_days(i):
                            return min(i.right - big_i.left, big_i.right - i.left, i.right - i.left).round('d').days

                        overlapping_days = list(map(number_of_overlapping_days,
                                                    self.interval_index[idx_bool_overlap_small_i]))
                        array_new = np.array(overlapping_days) * new_per_day

                        for i in range(array_new.shape[0]):
                            if not math.isnan(new_time_series[idx_bool_overlap_small_i][i]):
                                array_new[i] += new_time_series[idx_bool_overlap_small_i][i]

                        new_time_series[idx_bool_overlap_small_i] = array_new

            elif series_type == 'TOTAL':  # Cumulative time series

                if any(idx_bool_overlap_small_i):

                    current_total = time_series.values[idx_big_i]

                    if not math.isnan(current_total):

                        if idx_big_i - 1 >= 0:
                            last_total = 0 if math.isnan(time_series.values[idx_big_i - 1]) \
                                else time_series.values[idx_big_i - 1]
                        else:
                            last_total = 0

                        total_in_period = current_total - last_total

                        # Get number of days of current big interval
                        n_days_big_i = (big_i.right - big_i.left).round('d').days

                        # Get number of NEW / day
                        new_per_day = int(total_in_period / n_days_big_i)

                        # Add number of NEW * n days + last_total of small interval in current big interval
                        def number_of_overlapping_days(i):
                            return min(i.right - big_i.left, big_i.right - i.left, i.right - i.left).round('d').days

                        overlapping_days = list(map(number_of_overlapping_days,
                                                    self.interval_index[idx_bool_overlap_small_i]))
                        array_new = np.cumsum(np.array(overlapping_days) * new_per_day)

                        for i in range(array_new.shape[0]):
                            if not math.isnan(new_time_series[idx_bool_overlap_small_i][i]):
                                array_new[i] += new_time_series[idx_bool_overlap_small_i][i]
                            else:
                                array_new[i] += last_total

                        new_time_series[idx_bool_overlap_small_i] = array_new

        return new_time_series

    @staticmethod
    def _get_frequency_alias(frequency):
        if frequency == 'DAILY':
            return 'D'
        elif frequency == 'WEEKLY':
            return 'W'
        elif frequency == 'MONTHLY':
            return 'MS'
        elif frequency == 'YEARLY':
            return 'YS'
        else:
            raise ValueError('Unknown resampling frequency', frequency)

    @staticmethod
    def _get_timestamp_strformat(frequency):
        if frequency == 'DAILY':
            return '%d-%m-%Y'
        elif frequency == 'WEEKLY':
            return '%YW%W'
        elif frequency == 'MONTHLY':
            return '%m-%Y'
        elif frequency == 'YEARLY':
            return '%Y'
        else:
            raise ValueError('Unknown resampling frequency', frequency)
