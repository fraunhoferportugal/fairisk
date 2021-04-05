import json
from fairiskdata.sources.single_dataset import ALL_DATASETS_LIST, fetch_and_export
from typing import List, Tuple, Union
import datetime
import pandas as pd
from os import path
import numbers
import math
from collections.abc import Iterable

from fairiskdata.utils.age_parsers import safe_parse_age_group, do_ranges_overlap
from fairiskdata.utils.time_parsers import safe_date_parse, safe_sortable_date_parse, safe_interval_parse
from fairiskdata.preprocessing.resampling import Resampler
from fairiskdata.preprocessing.age_resampling import AgeResampler
from fairiskdata.preprocessing.normalizers import Normalizers
from fairiskdata.modelling.excess_mortality import ExcessMortality

import logging
logging.getLogger('fairisk').addHandler(logging.NullHandler())
logger = logging.getLogger('fairisk')

class FAIRiskDataset:
    """
    The main class of this package. It should be created by invoking the `fairisk_dataset.FAIRiskDataset.load` static
    method.
    """

    def __init__(self, dataset=None) -> None:
        super().__init__()
        self.dataset = dataset
        self._age_groups_granularity = None
        self.indicatorsNormalized = False
        self.scoresNormalized = False

    @staticmethod
    def load(json_file_path="output/fairisk_dataset.json", datasets_list=ALL_DATASETS_LIST, force_fetch=False):
        """
        Load the dataset. If json file does not exist locally, all datasets will be downloaded.

        Arguments:
                    json_file_path {`str`} -- specifies the location to store the cached json file including the datasets
                    that were fetched. (default: "output/fairisk_dataset.json")

                    datasets_list {`List[str]`} -- there is a list of all datasets which are downloaded by default.
                    A different list may be selected (see sources.single_dataset). Only used if fetch from sources occurs.

                    force_fetch {'bool'} -- if True, forces fetch from sources and overwrites json file if it exists.
                    (default: False)

        Returns:
            `FAIRiskDataset` -- an instance of the FAIRiskDataset with loaded information
        """
        if (not path.exists(json_file_path)) or force_fetch:
            fetch_and_export(json_file_path=json_file_path, datasets_list=datasets_list)

        with open(json_file_path) as f:
            dataset = json.load(f)
            for categories in dataset.values():
                for attributes in categories.values():
                    for attribute in attributes.values():
                        if 'VALUE' in attribute and isinstance(attribute['VALUE'], dict):
                            attribute['VALUE'] = pd.Series(attribute['VALUE'])

            return FAIRiskDataset(dataset)

    # GETTERS
    def get(self):
        return self.dataset

    def get_interval(self):
        """
        Defines the current interval represented in the dataset (considering all time series).

        Returns:
            `pandas.Interval` -- a pandas interval limited by the oldest and most recent dates available in the dataset.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return None

        start, end = datetime.datetime.max, datetime.datetime.min
        open_start, open_end = False, False

        for country_val in self.dataset.values():
            for category_val in country_val.values():
                for attribute_val in category_val.values():
                    if 'FREQUENCY' in attribute_val:  # indicates it is a timeseries
                        t0 = safe_date_parse(attribute_val['VALUE'].index[0])
                        tf = safe_date_parse(attribute_val['VALUE'].index[-1])
                        open_t0 = False
                        open_tf = False

                        if isinstance(t0, pd.Interval):
                            open_t0 = t0.open_left
                            open_tf = tf.open_right
                            t0 = t0.left
                            tf = tf.right

                        open_start = open_t0 if t0 < start else open_start
                        start = t0 if t0 < start else start

                        open_end = open_tf if tf > end else open_end
                        end = tf if tf > end else end

        if open_start and open_end:
            closed_str = 'neither'
        elif open_start:
            closed_str = 'right'
        elif open_end:
            closed_str = 'left'
        else:
            closed_str = 'both'

        return pd.Interval(start, end, closed=closed_str)

    def get_countries(self):
        """
        Returns the list of countries available on the loaded dataset

        Returns:
            `list` -- the list of countries
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return None

        return list(self.dataset.keys())

    def get_categories(self, countries: Union[str, List[str], None] = None):
        """
        Returns the list of categories by country

        Arguments:
            countries {str | List[str]} -- specifies a country or list of countries that will be filtered.

        Returns:
            `list[tuple]` -- a list of tuples with (country, category)
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return None

        if countries is not None and not isinstance(countries, list):
            countries = [countries]

        cat_list = []
        for country, dataCategories in self.dataset.items():
            if countries is None or country in countries:
                for dataCategory in dataCategories.keys():
                    cat_list.append((country, dataCategory))
        return cat_list

    def get_attributes(self, countries: Union[str, List[str], None] = None, categories: Union[str, List[str], None] = None):
        """
        Returns a list of attributes by country and category

        Arguments:
            countries {str | List[str]} -- specifies a country or list of countries that will be filtered.
            categories {str | List[str]} -- specifies a category or list of category that will be filtered.

        Returns:
            `list[tuple]` -- a list of tuples of (country, category, attribute)
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return None

        if countries is not None and not isinstance(countries, list):
            countries = [countries]
        if categories is not None and not isinstance(categories, list):
            categories = [categories]

        attrs_list = []
        for country, dataCategories in self.dataset.items():
            if countries is None or country in countries:
                for dataCategory, datasetCategoryEntries in dataCategories.items():
                    if categories is None or dataCategory in categories:
                        for parameter in datasetCategoryEntries.keys():
                            attrs_list.append((country, dataCategory, parameter))
        return attrs_list

    # FILTERS
    def filter_countries(self, countries: Union[str, List[str]]):
        """
        Filters the data of the specified countries. The method changes the underlying data.

        Arguments:
                    countries {str | List[str]} -- specifies the country or list of countries that will be filtered.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        # filter normalization and sanity check
        if not isinstance(countries, list):
            countries = [countries]

        del_countries = []
        for country in list(self.dataset.keys()):
            if country not in countries:
                del self.dataset[country]
                del_countries.append(country)

        logger.debug(f'{del_countries} countries erased from the dataset.')
        logger.info(f'{len(del_countries)} countries erased from the dataset.')

        return self

    def filter_categories(self, categories: Union[str, List[str]]):
        """
        Filters the specified categories. The method changes the underlying data.

        Arguments:
                    categories {str | List[str]} -- specifies the category or list of categories that will be filtered.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        # filter normalization and sanity check
        if not isinstance(categories, list):
            categories = [categories]

        for country_val in self.dataset.values():

            for category in list(country_val.keys()):
                if category not in categories:
                    country_val[category] = dict()

        self.dataset = self._clean_empty_entries(self.dataset)

        return self

    def filter_attributes(self, attributes: Union[Tuple[str, str], List[Tuple[str, str]]]):
        """
        Filters the data of the specified attributes. The method changes the underlying data.

        Arguments:
                    attributes {Tuple[str,str] | List[Tuple[str,str]]} -- specifies the attribute or list of attributes that will be filtered.
                    Each attribute is a tuple of a category and the attribute name.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        # filter normalization and sanity check
        if not isinstance(attributes, list):
            attributes = [attributes]

        for country_val in self.dataset.values():
            for category_key, category_val in country_val.items():
                for attribute in list(category_val.keys()):
                    if not any(attr for cat, attr in attributes if cat == category_key and attribute == attr):
                        del category_val[attribute]

        self.dataset = self._clean_empty_entries(self.dataset)

        return self

    def filter_time_interval(self, time_interval: Union[pd.Interval, pd.Period]):
        """
        Filters the data by time interval. Non time-like data is maintained. The method changes the underlying data.

        Arguments:
                    time_interval {pd.Interval | pd.Period} -- specifies the interval or period for which data will be filtered.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        # filter normalization and sanity check
        if isinstance(time_interval, pd.Period):
            time_interval = pd.Interval(
                time_interval.start_time, time_interval.end_time, closed='both')
        time_interval = safe_interval_parse(time_interval)

        def time_interval_validation(parsed):
            if parsed is None or (isinstance(parsed, numbers.Number) and math.isnan(parsed)):
                return False

            # year range like: 1984-2018
            if isinstance(parsed, pd.Interval):
                return time_interval.overlaps(parsed)

            return parsed in time_interval

        for country_val in self.dataset.values():
            for category_val in country_val.values():
                for attribute_val in category_val.values():
                    if 'FREQUENCY' in attribute_val:  # indicates it is a timeseries
                        parsed = attribute_val['VALUE'].index.to_series().map(
                            safe_date_parse).map(time_interval_validation)
                        attribute_val['VALUE'] = attribute_val['VALUE'][parsed == True]

        self.dataset = self._clean_empty_entries(self.dataset)

        return self

    def filter_age_group(self, age_group: Tuple[Union[int, None], Union[int, None]]):
        """
        Filters the data of the specified age group. Data not pertaining age related information is maintained. The method changes the underlying data.

        Arguments:
                    age_group {Tuple[int | None, int | None]} -- specifies the age group for which data will be filtered. The None value represents an open interval.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        for country_val in self.dataset.values():
            for category_val in country_val.values():
                for attribute_key in list(category_val.keys()):
                    parsed = safe_parse_age_group(attribute_key)
                    if parsed is not None and not do_ranges_overlap(parsed, age_group):
                        del category_val[attribute_key]

        self.dataset = self._clean_empty_entries(self.dataset)

        return self

    def filter_countries_with_missing_values_on_attributes(self, attr_missing_values_country_filter: Union[Tuple[str, str], List[Tuple[str, str]]]):
        """
        Filters the data for countries that have missing values on any of the specified attributes. The method changes the underlying data.

        Arguments:
                    attr_missing_values_country_filter {Tuple[str,str] | List[Tuple[str,str]]} -- specifies the list of attributes for which countries will be filtered. Each tuple represents a pair of category and attribute.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """

        # filter normalization and sanity check
        if not isinstance(attr_missing_values_country_filter, list):
            attr_missing_values_country_filter = [attr_missing_values_country_filter]

        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        for country_key, country_val in list(self.dataset.items()):
            if not all(category in country_val and
                       attr in country_val[category] and not
                       self._attr_has_missing_values(
                           country_val[category][attr])
                       for category, attr in attr_missing_values_country_filter):
                logger.warning('%s has been erased as it contained missing values on at least one of the selected '
                                'attributes.' % country_key)
                del self.dataset[country_key]

        return self

    def filter_countries_missing_value_attributes_below(self, attr_count_missing_values_country_filter: int):
        """
        Filters the data for countries that have missing values for a number attributes below the specified value. The method changes the underlying data.

        Arguments:
                    attr_count_missing_values_country_filter {int} -- specifies a number of attributes for which all country data will be removed whose number of attributes with missing values is above this value (countries with values below this number are maintained).

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        all_attrs = {(category, attribute) for categories in self.dataset.values(
        ) for category, category_vals in categories.items() for attribute in category_vals.keys()}

        def country_surpasses_missing_values_attributes(country_val):
            count = 0
            for category, attr in all_attrs:
                if category not in country_val or (
                    not attr in country_val[category]) or (
                        self._attr_has_missing_values(country_val[category][attr])):
                    count += 1
                    if count > attr_count_missing_values_country_filter:
                        return True

            return False

        for country_key, country_val in list(self.dataset.items()):
            if country_surpasses_missing_values_attributes(country_val):
                logger.warning('%s has be erased as it contained more than %d missing attributes.' % (
                    country_key, attr_count_missing_values_country_filter))
                del self.dataset[country_key]

        return self

    def filter_attributes_with_countries_nan_below(self, country_count_missing_values_attribute_filter: int):
        """
        Filters the attributes whose number of countries with missing values is below the specified value. The method changes the underlying data.

        Arguments:
                    country_count_missing_values_attribute_filter {int} -- specifies the number of countries for which attributes will be removed if the number of countries with missing values for that attribute is above (attributes with values below this number are maintained).

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning(
                'Dataset is empty. Please load and redo this operation.')
            return self

        all_attrs = {(category, attribute) for categories in self.dataset.values(
        ) for category, category_vals in categories.items() for attribute in category_vals.keys()}

        def number_of_countries_with_missing_values(attribute):
            category, attr = attribute
            count = 0

            for country_val in self.dataset.values():
                if category not in country_val or (
                    not attr in country_val[category]) or (
                        self._attr_has_missing_values(country_val[category][attr])):
                    count += 1

            return count

        attributes_to_remove = [attribute for attribute in all_attrs if number_of_countries_with_missing_values(
            attribute) > country_count_missing_values_attribute_filter]

        logger.debug(
            f'Removing {len(attributes_to_remove)} for having a number of countries with missing values above {country_count_missing_values_attribute_filter}')

        for country_val in self.dataset.values():
            for category, attr in attributes_to_remove:
                if category in country_val and attr in country_val[category]:
                    del country_val[category][attr]

        return self

    # RESAMPLERS
    def resample(self,
                 frequency: str = 'WEEKLY'):
        """
        Resamples all time series of categories Mortality, COVID and Mobility in a consistent way. The method changes the underlying data.

        Arguments:
                    frequency {str} -- specifies the target frequency for all time series. Should be one of:

                    * 'DAILY': time series data organized in days (dd-mm-yyyy)
                    * 'WEEKLY': time series data organized in weeks (yyyyWww)
                    * 'MONTHLY': time series data organized in months (mm-yyyy)
                    * 'YEARLY': time series data organized in years (yyyy)

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        time_interval = self.get_interval()

        resampler = Resampler(time_interval, frequency)

        for country_val in self.dataset.values():
            for category_val in country_val.values():
                for attribute_val in category_val.values():
                    if 'FREQUENCY' in attribute_val:  # indicates it is a timeseries
                        if attribute_val['FREQUENCY'] != 'UNDEFINED':
                            attribute_val['VALUE'] = resampler.resample(attribute_val['VALUE'],
                                                                        attribute_val['FREQUENCY'],
                                                                        attribute_val['SERIES_TYPE'])
                            attribute_val['FREQUENCY'] = frequency

        return self

    def resample_age_groups(self,
                            granularity: str = 'HIGH'):
        """
        Resamples all time series of categories Demographic and Mortality into new age groups. The method changes the underlying data.

        Arguments:
                    granularity {str} -- specifies the target age granularity for all time series. Should be one of:

                    * 'LOW': time series data organized into a single age group (Total)
                    * 'MEDIUM': time series data organized into three age groups (-14, 15-64, 65+)
                    * 'HIGH': time series data organized into five age groups (-14, 15-64, 65-74, 75-84, 85+)

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        if self._age_groups_granularity == granularity:
            return self

        if (self._age_groups_granularity is None) or (self._age_groups_granularity == 'HIGH') or \
                (self._age_groups_granularity == 'MEDIUM' and granularity == 'LOW'):

            for country_val in self.dataset.values():

                for category_name, category_val in country_val.items():
                    if category_name in ['DEMOGRAPHIC', 'MORTALITY']:
                        # Each resampler will deal with one category
                        age_resampler = AgeResampler(granularity)
                        country_val[category_name] = age_resampler.resample(category_val)

            self.dataset = self._clean_empty_entries(self.dataset)
            self._age_groups_granularity = granularity

        else:
            logger.warning("Cannot increase age groups granularity (CURRENT: %s | RESAMPLING TO: %s). "
                            "Please consider reloading the dataset and redoing this operation."
                            % (self._age_groups_granularity, granularity))

        return self

    def normalize_scores(self):
        """
        Normalizes all values of the "SCORES" subgroup using the MinMax strategy.

        Returns:
            `FAIRiskDataset`.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        if not self.scoresNormalized:
            self.dataset = Normalizers().min_max_scaler_scores(self.dataset)
            self.scoresNormalized = True

        else:
            logging.warning('SCORES were already normalized. No action performed.')
            return self

        return self

    def normalize_indicators(self):
        """
        Normalizes all values of the "INDICATORS" subgroup using the MinMax strategy.

        Returns:
            `FAIRiskDataset`.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        if not self.indicatorsNormalized:
            self.dataset = Normalizers().min_max_scaler_indicators(self.dataset)
            self.indicatorsNormalized = True

        else:
            logging.warning('INDICATORS were already normalized. No action performed.')
            return self

        return self

    # EXCESS MORTALITY
    def add_excess_mortality_estimation(self,
                                        age_resampling_granularity: str = 'HIGH',
                                        time_interval: Union[pd.Interval, pd.Period] =
                                        pd.Interval(pd.Timestamp('01-01-2020'), pd.Timestamp('31-12-2021'))):

        """
        Compute and add excess mortality estimation (P-score, Absolute) to MORTALITY category of FAIRiskDataset.
        This step requires resampling of DEMOGRAPHICS and MORTALITY age groups to a fixed granularity (see
        FAIRiskDataset.resample_age_groups).

        Arguments:
                    age_resampling_granularity {str} -- specifies target granularity for age groups resampling. Should
                    be one of:

                    * 'LOW': Total
                    * 'MEDIUM': 0-14y, 15-64y, 65+y
                    * 'HIGH': 0-14y, 15-64y, 65-74y, 75-84y, 85+y (default)

                    time_interval {pd.Interval | pd.Period} -- specifies the time interval for which excess mortality
                    should be calculated.

        Returns:
            `FAIRiskDataset` -- returns self to allow multiple calls in chain.

        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return self

        # filter normalization and sanity check
        if isinstance(time_interval, pd.Period):
            time_interval = pd.Interval(
                time_interval.start_time, time_interval.end_time, closed='both')
        time_interval = safe_interval_parse(time_interval)

        self.resample_age_groups(age_resampling_granularity)

        e = ExcessMortality()
        for country_name, country_val in self.dataset.items():
            if 'MORTALITY' in country_val.keys():
                country_val['MORTALITY'] = e.compute_and_add_to_mortality_dict(country_val['MORTALITY'],
                                                                               time_interval=time_interval)
            else:
                logger.warning(
                    'Not possible to compute excess mortality for %s. Missing MORTALITY category.' % country_name)

        return self

    # EXPORTERS
    def export(self, type: str = 'parameters', column_separator=':'):
        """
        Exports the dataset as a dataframe.

        Arguments:
                type {`str`} -- Specifies the type of data that should be exported. A different format will be used for each type,
                these are the possible values:

                * 'parameters': excludes timeseries data (default)
                * 'timeseries': exports timeseries data
                * 'all': exports all data

        Returns:
            `pandas.DataFrame` -- a pandas Dataframe with selected information.
        """
        if not self.dataset:
            logger.warning('Dataset is empty. Please load and redo this operation.')
            return None

        if type == 'parameters':
            return pd.DataFrame([
                {
                    'country': country,
                    **{
                        column_separator.join(
                            [category, attribute, attribute_key])
                        if len(attribute_val['VALUE']) > 1
                        else column_separator.join([category, attribute]): value
                        for category, category_val in country_val.items()
                        for attribute, attribute_val in category_val.items()
                        if 'FREQUENCY' not in attribute_val
                        for attribute_key, value in attribute_val['VALUE'].items()
                    }
                }
                for country, country_val in self.dataset.items()
            ])
        elif type == "all":
            return pd.DataFrame([
                {
                    'country': country,
                    'category': category,
                    'attribute': attribute,
                    **{k: v for k, v in attribute_val.items() if k != 'VALUE'},
                    'key': attribute_key,
                    'value': value
                }
                for country, country_val in self.dataset.items()
                for category, category_val in country_val.items()
                for attribute, attribute_val in category_val.items()
                for attribute_key, value in attribute_val['VALUE'].items()
            ])
        elif type == "timeseries":
            # get all different timestamp keys
            all_timestamps = {attribute_key
                              for country_val in self.dataset.values()
                              for category_val in country_val.values()
                              for attribute_val in category_val.values()
                              if 'FREQUENCY' in attribute_val
                              for attribute_key in attribute_val['VALUE'].keys()}
            return pd.DataFrame([
                {
                    'country': country,
                    'timestamp': timestamp,
                    'parsed_timestamp': safe_sortable_date_parse(timestamp),
                    **{
                        column_separator.join(
                            [category, attribute]): attribute_val['VALUE'][timestamp]
                        for category, category_val in country_val.items()
                        for attribute, attribute_val in category_val.items()
                        if 'FREQUENCY' in attribute_val and timestamp in attribute_val['VALUE'].keys()
                    }
                }
                for timestamp in all_timestamps
                for country, country_val in self.dataset.items()
            ]).sort_values('parsed_timestamp')

    # HELPERS
    @staticmethod
    def _attr_has_missing_values(attribute):
        if attribute is None or not 'VALUE' in attribute or attribute['VALUE'] is None:
            return True

        if isinstance(attribute['VALUE'], pd.Series):
            return attribute['VALUE'].isna().values.any()

        if isinstance(attribute['VALUE'], dict):
            return not all(v is not None and (
                not isinstance(v, numbers.Number) or
                not math.isnan(v)
            ) for _, v in attribute['VALUE'].items())

        if isinstance(attribute['VALUE'], Iterable):
            return not all(x is not None and (
                not isinstance(x, numbers.Number) or
                not math.isnan(x)
            ) for x in attribute['VALUE'])

        return False

    @staticmethod
    def _clean_empty_entries(dataset: dict):
        country_empty = []
        for country, country_dict in dataset.items():
            empty = []

            for category, category_dict in country_dict.items():

                # Check if attribute exists but is empty (None is there for safety)
                empty_att = []
                for att, att_dict in category_dict.items():
                    if att_dict['VALUE'] is None or len(att_dict['VALUE']) == 0:
                        empty_att += [att]
                category_dict = {
                    att: val for att, val in category_dict.items() if att not in empty_att}

                if not category_dict:
                    empty += [category]

            if empty:
                dataset[country] = {
                    cat: val for cat, val in country_dict.items() if cat not in empty}
                if dataset[country]:
                    logger.warning('%s no longer has %s data.' %
                                  (country, ", ".join(empty)))
                else:
                    country_empty += [country]
                    logger.warning(
                        '%s has been erased as it no longer had data.' % country)

        return {country: val for country, val in dataset.items() if country not in country_empty}
