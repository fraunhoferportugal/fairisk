from . import *

import requests
import json
import logging
from requests_futures.sessions import FuturesSession

logger = logging.getLogger('fairisk')

class GHODataset(Dataset):

    URL_API = 'https://ghoapi.azureedge.net/api/'

    def __init__(self):
        super().__init__()
        self._indicators = pd.DataFrame()

    def _fetch(self, host=URL_API, source_str='GHO'):

        success = False

        self.source_str = source_str

        try:
            # List all indicators
            indicators_df = self.get_indicators()

            # Get indicators' values per country
            indicator_gets = []
            session = FuturesSession()  # Asynchronous requests
            for indicator_code in indicators_df['IndicatorCode'].values:
                # logger.info('Parsing indicator %s' % indicator_code)
                url_indicator = host + indicator_code + '?$filter=SpatialDimType eq \'COUNTRY\' and Dim1 eq null and ' \
                                                        'Dim2 eq null and Dim3 eq null and date(TimeDimensionBegin) ' \
                                                        'ge 2015-01-01 and TimeDimType eq \'YEAR\' and' \
                                                        ' NumericValue ne null'
                indicator_get = session.get(url_indicator)
                indicator_gets.append(indicator_get)

            for indicator_get in indicator_gets:
                response = indicator_get.result()
                content = response.content
                data = json.loads(content)
                if len(data['value']):
                    data_df = pd.DataFrame(data['value'])
                    self.data = self.data.append(data_df, ignore_index=True)

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot fetch data due to exception: %s' % (self.source_str, e))

        return success

    def _structure(self):

        success = False

        self.structured_data = dict()

        cc = coco.CountryConverter()

        try:
            # Create 1st and 2nd dict levels
            spatial_dim = self.data['SpatialDim']
            country_codes = list()
            [country_codes.append(country_code) for country_code in spatial_dim if country_code not in country_codes]
            countries = dict()
            for country_code in country_codes:
                countries[country_code] = cc.convert(country_code, to=COUNTRY_CLASS_SCHEME)

                # 1st level: countries
                self.structured_data[countries[country_code]] = dict()

                # 2nd level: categories
                self.structured_data[countries[country_code]][INDICATORS_STR] = dict()
                self.structured_data[countries[country_code]][SCORES_STR] = dict()

            for i in list(self.data.index):
                # logger.info('Parsing entry %i / %i' % (i, len(self.data.index)))
                entry = self.data.loc[i, :]

                if countries[entry['SpatialDim']] == 'not found':
                    continue

                indicator_code = entry['IndicatorCode']
                # Define indicator category
                indicator_name = self._indicators.loc[self._indicators.IndicatorCode == indicator_code, 'IndicatorName'].values[0]
                if 'index' in indicator_name:
                    category = SCORES_STR
                else:
                    category = INDICATORS_STR
                # Add dimensions to indicator code
                if entry['Dim1']:
                    indicator_code += '_' + entry['Dim1']
                if entry['Dim2']:
                    indicator_code += '_' + entry['Dim2']
                if entry['Dim3']:
                    indicator_code += '_' + entry['Dim3']
                # Define unit
                if 'index' in indicator_name:
                    unit = 'Index'
                elif '%' in indicator_name:
                    unit = 'Percentage'
                elif (' per ' in indicator_name) or ('(per ' in indicator_name):
                    unit = 'Standardized'
                else:
                    unit = 'Number'

                # 3rd level: attribute
                if indicator_code in list(self.structured_data[countries[entry['SpatialDim']]][category].keys()):

                    # Only keep most recent value for each indicator
                    current_entry_year = list(self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][VALUE_STR].keys())[0]
                    if int(entry['TimeDim']) > int(current_entry_year):
                        self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][VALUE_STR][str(entry['TimeDim'])] = \
                            entry['NumericValue']
                        del self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][VALUE_STR][current_entry_year]

                else:
                    self.structured_data[countries[entry['SpatialDim']]][category][indicator_code] = dict()

                    self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][
                        ATTR_NAME_STR] = indicator_name
                    self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][SOURCE_STR] = \
                        self.source_str
                    self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][VALUE_STR] = \
                        {str(entry['TimeDim']): entry['NumericValue']}
                    self.structured_data[countries[entry['SpatialDim']]][category][indicator_code][UNIT_STR] = unit

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot structure data due to exception: %s' % (self.source_str, e))

        return success

    def get_indicators(self, url_api=URL_API):
        if self._indicators.empty:
            url_indicators = url_api + 'Indicator'
            request_indicators = requests.get(url_indicators)
            indicators = json.loads(request_indicators.content)
            self._indicators = pd.DataFrame(indicators['value'])
        return self._indicators


# def get_gho_dimension_values():
#
#     url_countries = URL_API + 'DIMENSION/COUNTRY/DimensionValues'
#     request_countries = requests.get(url_countries)
#     countries = json.loads(request_countries.content)
#     countries_df = pd.DataFrame(countries['value'])
#     return list(countries_df['Code'])
