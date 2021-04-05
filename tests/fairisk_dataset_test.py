import unittest
import random
import pandas as pd
import numpy as np

from fairiskdata import FAIRiskDataset
from fairiskdata.utils.time_parsers import safe_date_parse

import logging.config
from os import path
logging.config.fileConfig(path.join(path.dirname(__file__), '../logging.conf'))

class TestFAIRiskDataset(unittest.TestCase):

  def test_load(self):
    dataset = FAIRiskDataset.load()
    self.assertIsInstance(dataset, FAIRiskDataset)


  # GETTERS

  def test_get(self):
    loaded_dataset = FAIRiskDataset.load().get()
    self.assertIsInstance(loaded_dataset, dict)


  def test_get_interval(self):
      time_interval = FAIRiskDataset.load().get_interval()
      self.assertIsInstance(time_interval, pd.Interval)

  def test_data_getters(self):
    dataset = FAIRiskDataset.load()
    print(f"Countries: {dataset.get_countries()}")

    print(f"Categories (all): {dataset.get_categories()}")
    print(f"Categories (Portugal): {dataset.get_categories(['Portugal'])}")

    print(f"Attributes (all): {dataset.get_attributes()}")
    print(f"Attributes (Portugal): {dataset.get_attributes('Portugal')}")
    print(f"Attributes (Portugal+Spain, COVID+SCORES): {dataset.get_attributes(['Portugal', 'Spain'], ['COVID', 'SCORES'])}")

  # FILTERS

  def test_filter_single_country(self):
    dataset = FAIRiskDataset.load()

    random_country = random.choice(list(dataset.get()))

    country_data = dataset.get()[random_country]
    filtered_dataset = dataset.filter_countries([random_country])

    self.assertTrue(random_country in filtered_dataset.get())
    self.assertTrue(dict(filtered_dataset.get()[random_country], **country_data) == filtered_dataset.get()[random_country])
    self.assertTrue(len(filtered_dataset.get()) == 1)


  def test_filter_single_category(self):
    dataset = FAIRiskDataset.load()

    random_country = random.choice(list(dataset.get()))
    random_category = random.choice(list(dataset.get()[random_country]))

    category_data = dataset.get()[random_country][random_category]
    filtered_dataset = dataset.filter_categories([random_category])

    self.assertTrue(random_category in filtered_dataset.get()[random_country])
    self.assertTrue(dict(filtered_dataset.get()[random_country][random_category], **category_data) == filtered_dataset.get()[random_country][random_category])
    self.assertTrue(len(filtered_dataset.get()[random_country]) == 1)


  def test_filter_single_attribute(self):
    dataset = FAIRiskDataset.load()

    random_country = random.choice(list(dataset.get()))
    random_category = random.choice(list(dataset.get()[random_country]))
    random_attribute = random.choice(list(dataset.get()[random_country][random_category]))

    attribute_data = dataset.get()[random_country][random_category][random_attribute]
    filtered_dataset = dataset.filter_attributes([(random_category, random_attribute)])

    self.assertTrue(random_attribute in filtered_dataset.get()[random_country][random_category])
    self.assertTrue(dict(filtered_dataset.get()[random_country][random_category][random_attribute], **attribute_data) == filtered_dataset.get()[random_country][random_category][random_attribute])
    self.assertTrue(len(filtered_dataset.get()[random_country][random_category]) == 1)


  def test_filter_time_interval(self):
    dataset = FAIRiskDataset.load()

    pd_interval = pd.Interval(pd.Timestamp('2020'), pd.Timestamp('2021'), closed='neither')
    country = 'Portugal'
    category = 'COVID'
    attribute = 'total_deaths'

    # filter_countries filter_categories filter_attributes filter applied for performance purposes
    filtered_dataset = dataset\
      .filter_countries([country])\
      .filter_categories([category])\
      .filter_attributes([(category, attribute)])\
      .filter_time_interval(pd_interval)

    dates = filtered_dataset.get()[country][category][attribute]['VALUE'].keys()
    converted_dates = [pd.Timestamp(d) for d in dates]
    max_date = max(converted_dates)
    min_date = min(converted_dates)

    self.assertGreaterEqual(min_date, pd_interval.left)
    self.assertLessEqual(max_date, pd_interval.right)


  def test_filter_age_group(self):
    dataset = FAIRiskDataset.load()

    country = 'Portugal'
    category = 'DEMOGRAPHIC'

    filtered_dataset = dataset.filter_countries(country).filter_age_group(age_group=(40,80))
    self.assertFalse('85 years or over_Females' in filtered_dataset.get()[country][category].keys())
    self.assertFalse('From 40 to 44 years_Females' not in filtered_dataset.get()[country][category].keys())


  def test_filter_countries_with_missing_values_on_attributes(self):
    dataset = FAIRiskDataset.load()

    category = 'MORTALITY'
    attribute = 'D0_14_b'

    filtered_dataset = dataset.filter_countries_with_missing_values_on_attributes([(category, attribute)])
    random_country = random.choice(list(filtered_dataset.get()))

    filtered_dataset.get()[random_country][category][attribute]["VALUE"]["testmissingvalue"] = None
    filtered_dataset2 = dataset.filter_countries_with_missing_values_on_attributes([(category, attribute)])

    self.assertTrue(random_country not in filtered_dataset2.get().keys())


  def filter_countries_missing_value_attributes_below(self):
    dataset = FAIRiskDataset.load()

    attr_count_missing_values_country_filter = 200

    filtered_dataset = dataset.filter_countries_missing_value_attributes_below(attr_count_missing_values_country_filter)
    country2 = list(filtered_dataset.get())[1]
    country_with_added_values = list(filtered_dataset.get())[0]
    random_category = random.choice(list(filtered_dataset.get()[country_with_added_values]))

    for i in range(attr_count_missing_values_country_filter + 1):
      filtered_dataset.get()[country_with_added_values][random_category]["testmissingvalue_{}".format(i)] = { "VALUE": { 'test': 'test' } }

    filtered_dataset2 = filtered_dataset.filter_countries_missing_value_attributes_below(attr_count_missing_values_country_filter)

    self.assertTrue(country_with_added_values in filtered_dataset2.get().keys())
    self.assertTrue(country2 not in filtered_dataset2.get().keys())


  # RESAMPLERS

  def test_resample(self):
    dataset = FAIRiskDataset.load()
    dataset.filter_countries('Portugal').resample('MONTHLY')

    for country_val in dataset.get().values():
      for category_val in country_val.values():
        for attribute_val in category_val.values():
          if 'FREQUENCY' in attribute_val:
            prev_date = None
            for date in attribute_val['VALUE'].keys():
              safe_date = safe_date_parse(date)
              if prev_date != None:
                dif = (safe_date.left - prev_date.left) // np.timedelta64(1, 'D')
                self.assertGreaterEqual(dif, 28)
                self.assertLessEqual(dif, 31)

  def test_resample_age_groups(self):
    country = 'Portugal'
    category_m = 'MORTALITY'
    category_d = 'DEMOGRAPHIC'

    dataset = FAIRiskDataset.load()
    dataset.filter_countries(country).resample_age_groups('LOW')
    self.assertEqual(len(dataset.get()[country][category_m].keys()), 3)
    self.assertEqual(len(dataset.get()[country][category_d].keys()), 3)

    dataset = FAIRiskDataset.load()
    dataset.filter_countries(country).resample_age_groups('MEDIUM')
    self.assertEqual(len(dataset.get()[country][category_m].keys()), 9)
    self.assertEqual(len(dataset.get()[country][category_d].keys()), 9)

    dataset = FAIRiskDataset.load()
    dataset.filter_countries(country).resample_age_groups('HIGH')
    self.assertEqual(len(dataset.get()[country][category_m].keys()), 15)
    self.assertEqual(len(dataset.get()[country][category_d].keys()), 15)


  def test_normalize_scores(self):
    dataset = FAIRiskDataset.load()
    normalized_dataset = dataset.normalize_scores()

    for _, country in normalized_dataset.get().items():
      if 'SCORES' in country:
        for _, category in country['SCORES'].items():
          for _, value in category['VALUE'].items():
            if value is not None:
              self.assertLessEqual(value, 1)
              self.assertGreaterEqual(value, 0)


  def test_normalize_indicators(self):
    dataset = FAIRiskDataset.load()
    normalized_dataset = dataset.normalize_indicators()

    for _, country in normalized_dataset.get().items():
      if 'INDICATORS' in country:
        for _, category in country['INDICATORS'].items():
          for _, value in category['VALUE'].items():
            if value is not None:
              self.assertLessEqual(value, 1)
              self.assertGreaterEqual(value, 0)


  # EXCESS MORTALITY

  def test_add_excess_mortality_estimation(self):
    country = 'Portugal'
    category_m = 'MORTALITY'

    dataset = FAIRiskDataset.load()
    dataset.filter_countries(country).add_excess_mortality_estimation('LOW')
    self.assertEqual(len(dataset.get()[country][category_m].keys()), 9)

    dataset = FAIRiskDataset.load()
    dataset.filter_countries(country).add_excess_mortality_estimation('MEDIUM')
    self.assertEqual(len(dataset.get()[country][category_m].keys()), 27)

    dataset = FAIRiskDataset.load()
    dataset.filter_countries(country).add_excess_mortality_estimation('HIGH')
    self.assertEqual(len(dataset.get()[country][category_m].keys()), 45)

    return


  # EXPORTERS

  def test_export(self):
    dataset = FAIRiskDataset.load()

    countries = ['Portugal']
    categories = ['INDICATORS', 'SCORES', 'DEMOGRAPHIC']
    parameter_attributes = [('INDICATORS', 'gdp_per_capita'), ('INDICATORS', 'extreme_poverty'), ('SCORES', 'CPI')]
    timeseries_attributes = [('DEMOGRAPHIC', 'Total_Total')]
    dataset\
        .filter_countries(countries)\
        .filter_categories(categories)\
        .filter_attributes(parameter_attributes + timeseries_attributes)

    e_all = dataset.export(type='all')
    self.assertEqual(list(e_all.columns), ['country', 'category', 'attribute',
                                           'ATTR_NAME', 'SOURCE', 'UNIT', 'FREQUENCY', 'SERIES_TYPE', 'key', 'value'])

    e_parameters = dataset.export(type='parameters')
    self.assertEqual(len(e_parameters.columns), len(parameter_attributes) + 1) # ['country', gdp_per_capita', 'extreme_poverty', 'CPI']

    e_timeseries = dataset.export(type='timeseries')
    self.assertEqual(len(e_timeseries.columns), len(timeseries_attributes) + 3) # ['country', 'timestamp', 'parsed_timestamp', 'DEMOGRAPHIC:Total_Total']


if __name__ == '__main__':
    unittest.main()
