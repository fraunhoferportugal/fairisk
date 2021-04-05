from . import *

import webbrowser
from pyjstat import pyjstat

import logging
logger = logging.getLogger('fairisk')

class EurostatDataset(Dataset):

    def __init__(self):
        super().__init__()

    def _fetch(self,
               host='',
               source_str='',
               filters=list(),
               db_code=''):

        success = False

        # FIXME: add date of fetch to source_str since it does not have version?
        self.source_str = source_str

        try:

            # Eurostat does not allow to retrieve an huge amount of data at once
            # splitting the data fetch by participants gender
            for index, gender in enumerate([('sex', 'M'), ('sex', 'F'), ('sex', 'T')]):
                filters.append(gender)
                # prepare json string
                query = self.query_builder(filters)
                filters.remove(gender)
                # create final host
                fhost = "/".join([host, db_code + query])

                if index == 0:
                    # Load data to DataFrame
                    self.data = pyjstat.Dataset.read(fhost).write('dataframe').dropna()
                else:
                    # add DataFrame to existing DataFrame
                    self.data = self.data.append(pyjstat.Dataset.read(fhost).write('dataframe')).dropna()

            self.data = self.data.reset_index(drop=True)

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot fetch data due to exception: %s' % (self.source_str, e))

        return success

    def _structure(self):

        success = False

        cc = coco.CountryConverter()

        try:

            # assert frequency of dataset
            frequency = WEEKLY_STR if self.source_str == 'Eurostat: Deaths by week, sex, 5-year age group' else YEARLY_STR

            # assert entity sub-groups of dataset
            entity = MORTALITY_STR if self.source_str == 'Eurostat: Deaths by week, sex, 5-year age group' else DEMOGRAPHIC_STR

            # assert type of time series - current values for demographic and new deaths for mortality
            ts_type = NEW_STR if self.source_str == 'Eurostat: Deaths by week, sex, 5-year age group' else CURRENT_STR

            # create new column with concatenation of age and sex
            self.data['age_sex'] = self.data.age + '_' + self.data.sex
            logger.info('[%s] Structure data | Added age_sex column to fetched table' % self.source_str)

            new_countries = cc.convert(sorted(set(self.data['geo'])), to=COUNTRY_CLASS_SCHEME, not_found=None)

            # remove mortality entries that have time set as 'Unknown week'
            self.data.drop(self.data[self.data['time'] == 'Unknown week'].index, inplace=True)

            self.structured_data = dict()

            # 1st level: Countries
            for i, country in enumerate(sorted(set(self.data['geo']))):

                self.structured_data[new_countries[i]] = dict()

                # 2nd level: Categories
                self.structured_data[new_countries[i]][entity] = dict()

                # 3rd level: Indicator/Variable
                for stratification in sorted(set(self.data[self.data.geo == country]['age_sex'])):
                    self.structured_data[new_countries[i]][entity][stratification] = \
                        {ATTR_NAME_STR: stratification,
                         SOURCE_STR: self.source_str,
                         UNIT_STR: 'Number',
                         FREQ_STR: frequency,
                         TSTYPE_STR: ts_type,
                         VALUE_STR:
                             self.data[(self.data.geo == country) & (self.data.age_sex == stratification)][['time', 'value']].set_index(
                                 ['time']).to_dict()['value']}

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot structure data due to exception: %s' % (self.source_str, e))

        return success

    @staticmethod
    def query_builder_helper():
        # auxiliary method to help user in query construction
        helper_url = "https://ec.europa.eu/eurostat/web/json-and-unicode-web-services/getting-started/query-builder"
        webbrowser.open(helper_url)

    @staticmethod
    def query_builder(filters):
        # build query
        return "?" + "&".join(sf for sf in ['='.join(k) for k in filters])


class DemographicEurostatDataset(EurostatDataset):

    FILTERS = [('sinceTimePeriod', '2010'),
               ('geoLevel', 'country'),
               ('precision', '1'),
               ('unit', 'NR'),
               ('age', 'TOTAL'),
               ('age', 'Y_LT5'),
               ('age', 'Y5-9'),
               ('age', 'Y10-14'),
               ('age', 'Y15-19'),
               ('age', 'Y20-24'),
               ('age', 'Y25-29'),
               ('age', 'Y30-34'),
               ('age', 'Y35-39'),
               ('age', 'Y40-44'),
               ('age', 'Y45-49'),
               ('age', 'Y50-54'),
               ('age', 'Y55-59'),
               ('age', 'Y60-64'),
               ('age', 'Y65-69'),
               ('age', 'Y70-74'),
               ('age', 'Y75-79'),
               ('age', 'Y80-84'),
               ('age', 'Y_GE85')]

    DB_CODE = "demo_pjangroup"

    def __init__(self):
        super().__init__()

    def _fetch(self,
               host='http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en',
               source_str='Eurostat: Population on 1 January by age group and sex',
               filters=FILTERS,
               db_code=DB_CODE):

        return super()._fetch(host=host,
                              source_str=source_str,
                              filters=filters,
                              db_code=db_code)

    def _structure(self):

        # remove EU aggregations
        self.data.drop(self.data[(self.data.geo == 'Euro area - 18 countries (2014)') |
                       (self.data.geo == 'Euro area - 19 countries  (from 2015)') |
                       (self.data.geo == 'European Economic Area (EU27 - 2007-2013 and IS, LI, NO)') |
                       (self.data.geo == 'European Economic Area (EU28 - 2013-2020 and IS, LI, NO)') |
                       (self.data.geo == 'European Free Trade Association') |
                       (self.data.geo == 'European Union - 27 countries (2007-2013)') |
                       (self.data.geo == 'European Union - 27 countries (from 2020)') |
                       (self.data.geo == 'European Union - 28 countries (2013-2020)') |
                       (self.data.geo == 'France (metropolitan)')].index, inplace=True)
        logger.info('[%s] Structure data | Removed EU aggregations from fetched table' % self.source_str)

        return super()._structure()


class MortalityEurostatDataset(EurostatDataset):

    FILTERS = [('sinceTimePeriod', '2010W01'),
               ('geoLevel', 'country'),
               ('precision', '1'),
               ('age', 'TOTAL'),
               ('age', 'Y_LT5'),
               ('age', 'Y5-9'),
               ('age', 'Y10-14'),
               ('age', 'Y15-19'),
               ('age', 'Y20-24'),
               ('age', 'Y25-29'),
               ('age', 'Y30-34'),
               ('age', 'Y35-39'),
               ('age', 'Y40-44'),
               ('age', 'Y45-49'),
               ('age', 'Y50-54'),
               ('age', 'Y55-59'),
               ('age', 'Y60-64'),
               ('age', 'Y65-69'),
               ('age', 'Y70-74'),
               ('age', 'Y75-79'),
               ('age', 'Y80-84'),
               ('age', 'Y85-89'),
               ('age', 'Y_GE90')]

    DB_CODE = 'demo_r_mwk_05'

    def __init__(self):
        super().__init__()

    def _fetch(self,
               host='http://ec.europa.eu/eurostat/wdds/rest/data/v2.1/json/en',
               source_str='Eurostat: Deaths by week, sex, 5-year age group',
               filters=FILTERS,
               db_code=DB_CODE):
        return super()._fetch(host=host,
                              source_str=source_str,
                              filters=filters,
                              db_code=db_code)

