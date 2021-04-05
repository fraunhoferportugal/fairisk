from . import *

import numpy as np

import logging
logger = logging.getLogger('fairisk')

class INFORMDataset(Dataset):

    def __init__(self):
        super().__init__()

    def _fetch(self,
               host='https://drmkc.jrc.ec.europa.eu/inform-index/Portals/0/InfoRM/Epidemic/INFORM%20Epidemic%20Risk%202020%20v.041.xlsx?ver=2020-04-03-171941-160',
               source_str=''):

        success = False

        if source_str == '':
            try:
                self.source_str = host.split('/')[-1]
                self.source_str = self.source_str.replace('%20', ' ')
            except Exception as e:
                self.source_str = host
                logger.info('[%s] Defined host as name of source due to exception: %s' % (self.source_str, e))

        try:
            # Load .xlsx to DataFrame
            self.data = pd.read_excel(host, sheet_name=None)
            success = True
        except Exception as e:
            logger.critical('[%s] Cannot fetch data due to exception: %s' % (self.source_str, e))

        return success

    def _structure(self):

        success = False

        self.structured_data = dict()

        cc = coco.CountryConverter()

        try:
            # -----------------------------------
            # Parse Indicator Data sheet
            # logger.info('Parsing Indicator Data sheet')
            indicator_data = self.data['Indicator Data']
            indicator_data = indicator_data.dropna(axis='columns', how='all')

            # 1st level: Countries
            for i_country, country in enumerate(indicator_data.iloc[4:, 0]):
                # Convert country name to uniform country classification scheme
                country = cc.convert(country, to=COUNTRY_CLASS_SCHEME) if country != 'Korea DPR' \
                    else 'North Korea'  # Handle incorrect North Korea parse
                indicator_data.iloc[4 + i_country, 0] = country

                self.structured_data[country] = dict()

                # 2nd level: Categories
                self.structured_data[country][INDICATORS_STR] = dict()
                self.structured_data[country][SCORES_STR] = dict()

            # List all indicators' IDs
            list_indicator_ids = list()
            for i in range(2, indicator_data.shape[1]):
                indicator_id = indicator_data.iloc[2, i]
                attr_name = indicator_data.iloc[0, i]

                # Create an ID from first letters of indicator name, if no ID is available
                if str(indicator_id) == 'nan':
                    words_attr_name = attr_name.split(' ')
                    indicator_id = ''
                    for word in words_attr_name:
                        indicator_id += word[0]

                    indicator_data.iloc[2, i] = indicator_id

                list_indicator_ids.append(indicator_id)

            # Fill new data structure with available data
            discard_indicator_ids = list()  # Auxiliary variable
            for i_col in range(2, indicator_data.shape[1]):

                # Get indicator ID
                indicator_id = list_indicator_ids[i_col - 2]
                # Get indicator name
                attr_name = indicator_data.iloc[0, i_col]

                # logger.info('Parsing', attr_name)

                # Handle repeated indicators (only keep most recent data)
                if indicator_id in discard_indicator_ids:
                    continue
                else:
                    n_occurrences = list_indicator_ids.count(indicator_id)
                    if n_occurrences > 1:
                        # Get all columns with same indicator ID
                        indicator_columns = indicator_data.loc[:, indicator_data.iloc[2, :] == indicator_id]
                        # Find most recent data (using 'Year' row)
                        most_recent = 0
                        i_most_recent = 0
                        for i_date, date in enumerate(indicator_columns.iloc[1, :]):
                            if isinstance(date, int):
                                if date > most_recent:
                                    most_recent = date
                                    i_most_recent = i_date
                            elif isinstance(date, str):
                                year_range = date.split('-')
                                if int(year_range[1]) > most_recent:
                                    most_recent = int(year_range[1])
                                    i_most_recent = i_date
                        # Only use column with most recent data
                        indicator_column = indicator_columns.iloc[:, i_most_recent]
                        # Add indicator_ids to discard_indicator_ids to avoid repetitions of this process
                        discard_indicator_ids.append(indicator_id)

                    else:
                        indicator_column = indicator_data.iloc[:, i_col]

                # Get date
                date = indicator_column.iloc[1]
                # Get unit
                unit = indicator_column.iloc[3]

                # Process indicator for each country
                for i_country, country in enumerate(indicator_data.iloc[4:, 0]):

                    # Parse value (handle NaN)
                    value = indicator_column.iloc[i_country + 4]
                    try:
                        value = float(value)
                    except ValueError:
                        if value == 'No data':
                            value = np.nan

                    # Define category (Indicator vs. Score)
                    if unit == 'Index':
                        category = SCORES_STR
                    else:
                        category = INDICATORS_STR

                    # 3rd level: Categories' attributes
                    self.structured_data[country][category][indicator_id] = dict()

                    # Attributes
                    self.structured_data[country][category][indicator_id][ATTR_NAME_STR] = attr_name
                    self.structured_data[country][category][indicator_id][SOURCE_STR] = self.source_str
                    self.structured_data[country][category][indicator_id][VALUE_STR] = {str(date): value}
                    self.structured_data[country][category][indicator_id][UNIT_STR] = unit

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot structure data due to exception: %s' % (self.source_str, e))

        return success
