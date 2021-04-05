from . import *

import numpy as np
import logging
import re

try:
    from urllib.request import Request, urlopen  # Python 3
except ImportError:
    from urllib2 import Request, urlopen  # Python 2

logger = logging.getLogger('fairisk')

class CovidOWiD(Dataset):
    USE_COLS = {'total_cases': {'unit': 'Number', 'category': COVID_STR, 'type': TOTAL_STR},
                'new_cases': {'unit': 'Number', 'category': COVID_STR, 'type': NEW_STR},
                'total_deaths': {'unit': 'Number', 'category': COVID_STR, 'type': TOTAL_STR},
                'new_deaths': {'unit': 'Number', 'category': COVID_STR, 'type': NEW_STR},
                'icu_patients': {'unit': 'Number', 'category': COVID_STR, 'type': CURRENT_STR},
                'hosp_patients': {'unit': 'Number', 'category': COVID_STR, 'type': CURRENT_STR},
                'new_tests': {'unit': 'Number', 'category': COVID_STR, 'type': NEW_STR},
                'positive_rate': {'unit': '%', 'category': COVID_STR, 'type': CURRENT_STR},
                'total_tests': {'unit': 'Number', 'category': COVID_STR, 'type': TOTAL_STR},
                'new_vaccinations': {'unit': 'Number', 'category': COVID_STR, 'type': NEW_STR},
                'total_vaccinations': {'unit': 'Number', 'category': COVID_STR, 'type': TOTAL_STR},
                'people_fully_vaccinated': {'unit': 'Number', 'category': COVID_STR, 'type': TOTAL_STR},
                'people_vaccinated': {'unit': 'Number', 'category': COVID_STR, 'type': TOTAL_STR},
                'stringency_index': {'unit': 'Index', 'category': COVID_STR, 'type': CURRENT_STR},
                'reproduction_rate': {'unit': 'Index', 'category': COVID_STR, 'type': CURRENT_STR},
                'population': {'unit': 'Number', 'category': DEMOGRAPHIC_STR, 'type': NONAPPLICABLE_STR},
                'population_density': {'unit': 'Number per square kilometer', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'median_age': {'unit': 'Number', 'category': DEMOGRAPHIC_STR, 'type': NONAPPLICABLE_STR},
                'aged_65_older': {'unit': '%', 'category': DEMOGRAPHIC_STR, 'type': NONAPPLICABLE_STR},
                'aged_70_older': {'unit': '%', 'category': DEMOGRAPHIC_STR, 'type': NONAPPLICABLE_STR},
                'gdp_per_capita': {'unit': 'per capita', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'extreme_poverty': {'unit': '%', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'cardiovasc_death_rate': {'unit': 'Number per 100,000 people', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'diabetes_prevalence': {'unit': '%', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'female_smokers': {'unit': '%', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'male_smokers': {'unit': '%', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'handwashing_facilities': {'unit': '%', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'hospital_beds_per_thousand': {'unit': 'Number per thousand', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'life_expectancy': {'unit': 'Years', 'category': INDICATORS_STR, 'type': NONAPPLICABLE_STR},
                'human_development_index': {'unit': 'Index', 'category': SCORES_STR, 'type': NONAPPLICABLE_STR}}

    EXCLUDE_GROUPS = ['Africa', 'Asia', 'Europe', 'European Union', 'North America', 'Oceania', 'South America',
                      'World', 'International', 'Northern Cyprus']

    def __init__(self):
        self.metadata_host = 'https://covid.ourworldindata.org/data/owid-covid-codebook.csv'
        self.metadata = pd.DataFrame()
        super().__init__()

    def _fetch(self,
               host='https://covid.ourworldindata.org/data/owid-covid-data.csv',
               source_str='Data on COVID-19 (coronavirus) by Our World in Data'):

        success = False

        # FIXME: add date of fetch to source_str since it does not have version?
        self.source_str = source_str

        try:
            # Fake user agent added to avoid request blockage from server
            req = Request(host)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
            content = urlopen(req)

            # Load .csv to DataFrame
            self.data = pd.read_csv(content)

            # Load .csv metadata
            req = Request(self.metadata_host)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
            content = urlopen(req)

            self.metadata = pd.read_csv(content)

            success = True
        except Exception as e:
            logger.critical('[%s] Cannot fetch data due to exception: %s' % (self.source_str, e))

        return success

    def _structure(self, use_cols=USE_COLS, exclude_groups=EXCLUDE_GROUPS):

        success = False

        self.structured_data = dict()

        cc = coco.CountryConverter()

        try:
            # remove world data from table
            self.data.drop(self.data[self.data.location.isin(exclude_groups)].index, inplace=True)
            logger.info('[%s] Structure data | Removed aggregated data from fetched table' % self.source_str)

            # create converted list of countries
            self.data.location.replace({'Timor': 'Timor-Leste'}, inplace=True)
            new_countries = cc.convert(sorted(set(self.data['location'])), to=COUNTRY_CLASS_SCHEME, not_found=None)
            logger.info('[%s] Structure data | Converted countries from fetched table to %s' % (
            self.source_str, COUNTRY_CLASS_SCHEME))

            # 1st level: Countries
            for i, country in enumerate(sorted(set(self.data['location']))):

                self.structured_data[new_countries[i]] = dict()

                distribution = self.data[self.data.location == country].set_index(['date']).to_dict()

                if not use_cols:
                    use_cols = {col: {'unit': 'Number', 'category': COVID_STR} for col in
                                self.data[self.data.location == country].set_index(['date']).columns.tolist()}

                for col, info in use_cols.items():

                    # 2nd level: Categories
                    if info['category'] not in self.structured_data[new_countries[i]].keys():
                        self.structured_data[new_countries[i]][info['category']] = dict()

                    # replace constant indicators by a single entry with first appearance
                    # in this case, retrieve indicator date from metadata csv
                    values = pd.Series(sorted(set(distribution[col].values()))).dropna()
                    if (values.size == 1) and (info['category'] != COVID_STR):
                        desc_year = re.findall("\d{4}", self.metadata.loc[self.metadata['column'] == col]['description'].values[0])
                        desc_year = sorted(desc_year)[-1] if len(desc_year) > 0 else str(pd.Timestamp(list(distribution[col].keys())[
                                                                  np.argwhere(list(distribution[col].values()) ==
                                                                              values.values[0])[0][0]]).year)

                        distribution[col] = {desc_year: values.values[0]}

                    # remove all attributes that do not have meaningful information
                    elif values.size == 0:
                        continue

                    # introduce zeros before the first case for that year and replace nans with zeros or previous value
                    else:
                        dist_series = pd.Series(distribution[col]).dropna()

                        oldest_date = pd.to_datetime(dist_series.index).min()

                        input_dates = pd.date_range(pd.Timestamp(day=1, month=1, year=oldest_date.year),
                                                    oldest_date, freq='D', closed='left')

                        # define imputation value for missing entries
                        def imputation_value(d):
                            if info['type'] != NEW_STR:
                                last_values = dist_series[pd.to_datetime(dist_series.index) < pd.Timestamp(d)]
                                if last_values.size > 0:
                                    return distribution[col][last_values.index.max()]
                            return 0.

                        distribution[col].update({d.strftime('%Y-%m-%d'): 0. for d in input_dates})
                        distribution[col] = {d: (distribution[col][d] if not np.isnan(distribution[col][d]) else imputation_value(d)) for d in sorted(distribution[col])}

                    # 3rd level: Indicator/Variable
                    self.structured_data[new_countries[i]][info['category']][col] = {
                        ATTR_NAME_STR: self.metadata.loc[self.metadata['column'] == col]['description'].values[0],
                        SOURCE_STR: self.source_str + ' - ' + self.metadata.loc[self.metadata['column'] == col]['source'].values[0],
                        UNIT_STR: info['unit'],
                        VALUE_STR: distribution[col]}

                    # parameters only added if attribute is ts:
                    if info['category'] == COVID_STR:
                        self.structured_data[new_countries[i]][info['category']][col][FREQ_STR] = DAILY_STR
                        self.structured_data[new_countries[i]][info['category']][col][TSTYPE_STR] = info['type']

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot structure data due to exception: %s' % (self.source_str, e))

        return success
