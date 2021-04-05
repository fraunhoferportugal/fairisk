from fairiskdata.sources import *
from typing import Union
import pandas as pd
import numpy as np
import numbers
import math

import logging
logger = logging.getLogger('fairisk')

from fairiskdata.utils.time_parsers import safe_date_parse


class ExcessMortality:

    def compute_and_add_to_mortality_dict(self, mortality_dict, time_interval: pd.Interval):
        """
        Estimate different types of excess mortality and add them to the original mortality dictionary.
        :param mortality_dict: dict
        :param time_interval: pandas.Interval
        :return: mortality_dict: dict
        """

        start_excess, end_excess = time_interval.left, time_interval.right

        start_baseline = pd.Timestamp(day=1, month=1, year=start_excess.year - 5)
        end_baseline = pd.Timestamp(day=31, month=12, year=end_excess.year - 1)

        for age, age_mortality in list(mortality_dict.items()):
            baseline_data = self._data_interval(age_mortality, pd.Interval(start_baseline, end_baseline))
            excess_data = self._data_interval(age_mortality, time_interval)
            baseline = self._create_mortality_baseline(age_mortality, baseline_data, excess_data, start_excess.year,
                                                       end_excess.year)

            if baseline is not None:
                metrics = {'Abs': self._estimate_absolute(baseline),
                           'PScore': self._estimate_p_score(baseline)}

                timestamps = baseline[:, 0]  # Timestamps estimated in baseline
                for name, values in metrics.items():
                    data = {time: m for time, m in zip(timestamps, values)}
                    new_key = 'Excess' + name + '_' + age
                    source_mortality = 'Computed using ' + age_mortality[SOURCE_STR]
                    mortality_dict[new_key] = {}
                    mortality_dict[new_key] = {ATTR_NAME_STR: new_key, SOURCE_STR: source_mortality, UNIT_STR: 'Number',
                                               FREQ_STR: WEEKLY_STR,
                                               TSTYPE_STR: NEW_STR if name == 'Abs' else CURRENT_STR,
                                               VALUE_STR: pd.Series(data=data)}

        return mortality_dict

    @staticmethod
    def _estimate_p_score(baseline):
        """
        Estimate excess mortality based on p-score.
        :param baselines: list
        :return: p_score: list
        """
        mortality_in_period = baseline[:, 2].astype(float)
        mortality_baseline = baseline[:, 1].astype(float)
        return (mortality_in_period - mortality_baseline) / mortality_baseline * 100

    @staticmethod
    def _estimate_absolute(baseline):
        """
        Estimate excess mortality absolute values.
        :param baseline: list ['time', 'baseline_mortality', 'target_mortality'
        :return: z_score: list
        """
        mortality_in_period = baseline[:, 2].astype(float)
        mortality_baseline = baseline[:, 1].astype(float)
        return mortality_in_period - mortality_baseline

    @staticmethod
    def _create_mortality_baseline(mortality_dict, baseline_data, target_data, start_excess_year, end_excess_year):
        """
        Create mortality baseline with previous two to five years (depending on the data available) and select mortality
        data from the year in study.
        :param mortality_dict: dict
        :param baseline_data: list
        :param target_data: list
        :return: baselines: list
        """

        def get_year(time):
            parsed = safe_date_parse(time)
            if isinstance(parsed, pd.Interval):
                return parsed.right.year
            else:
                return parsed.year

        frequency = mortality_dict[FREQ_STR]
        baseline_data = baseline_data.dropna()
        target_data = target_data.dropna()

        baseline = []
        for target_year in range(start_excess_year, end_excess_year + 1):
            # Select data to estimate a baseline for each year (5 previous years)
            # 2019 is the maximum baseline year since the pandemic started in 2020

            baseline_end = target_year - 1 if target_year < 2021 else 2019
            past_years = list(range(baseline_end - 4, baseline_end + 1))

            current_data = baseline_data[pd.Series(baseline_data.index).apply(get_year).isin(past_years).values]
            current_data_year = target_data[pd.Series(target_data.index).apply(get_year).values == target_year]

            if len(current_data_year) >= 0:  # if data available for the given year, estimate baseline
                if frequency == DAILY_STR:
                    if len(current_data) >= 2 * 365:
                        for deaths_day, d in zip(current_data_year, current_data_year.index):
                            # TODO is there a way to assert the weeks without looking for the string?
                            deaths = current_data[current_data.index.str.contains(str(d[-5:]))].mean()
                            baseline.append([d, deaths, deaths_day])
                    else:  # if no data available of at least 2 previous years
                        logger.warning('Not enough mortality data available from 2 previous years.')

                elif frequency == WEEKLY_STR:
                    if len(current_data) >= 2 * 52:  # if no data available of at least 2 previous years
                        for deaths_week, w in zip(current_data_year, current_data_year.index):
                            deaths = current_data[current_data.index.str.contains(str(w[-3:]))].mean()
                            baseline.append([w, deaths, deaths_week])
                    else:
                        logger.warning('Not enough mortality data available from 2 previous years.')

                elif frequency == MONTHLY_STR:
                    if len(current_data) >= 2 * 12:  # if no data available of at least 2 previous years
                        for deaths_month, m in zip(current_data_year, current_data_year.index):
                            deaths = current_data[current_data.index.str.contains(str(m[:3]))].mean()
                            baseline.append([m, deaths, deaths_month])
                    else:
                        logger.warning('Not enough mortality data available from 2 previous years.')

                elif frequency == YEARLY_STR:
                    if len(current_data) >= 2:  # if no data available of at least 2 previous years
                        for deaths_year, y in zip(current_data_year, current_data_year.index):
                            deaths = current_data.mean()
                            baseline.append([y, deaths, deaths_year])
                    else:
                        logger.warning('Not enough mortality data available from 2 previous years.')

            else:
                logger.warning('No mortality data available for %d.' % target_year)

        if not baseline:
            return None

        return np.array(baseline)

    @staticmethod
    def _data_interval(mortality_dict, time_interval: Union[pd.Interval, pd.Period]):

        # TODO redundant method replicated in fairisk_dataset - should be moved to utils?
        def time_interval_validation(parsed):
            if parsed is None or (isinstance(parsed, numbers.Number) and math.isnan(parsed)):
                return False
            if isinstance(parsed, pd.Interval):
                return time_interval.overlaps(parsed)
            return parsed in time_interval

        parsed = mortality_dict['VALUE'].index.to_series().map(safe_date_parse).map(time_interval_validation)

        return mortality_dict['VALUE'][parsed == True]
