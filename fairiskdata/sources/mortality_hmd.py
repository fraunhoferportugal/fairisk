from . import *

import logging
logger = logging.getLogger('fairisk')

class MortalityHMDDataset(Dataset):

    def __init__(self):
        super().__init__()

    def _fetch(self,
               host='https://www.mortality.org/Public/STMF/Outputs/stmf.csv',
               source_str='Human Mortality Database'):

        success = False

        # FIXME: add date of fetch to source_str since it does not have version?
        self.source_str = source_str

        try:
            # Load .csv to DataFrame
            self.data = pd.read_csv(host, comment='#')
            success = True
        except Exception as e:
            logger.critical('[%s] Cannot fetch data due to exception: %s' % (self.source_str, e))

        return success

    def _structure(self):

        success = False

        self.structured_data = dict()

        cc = coco.CountryConverter()

        try:

            # create new column with concatenation of year and week
            self.data['timestamp'] = self.data.Year.astype(str) + 'W' + self.data.Week.astype(str).str.zfill(2)
            logger.info('[%s] Structure data | Created new column with concatenation of year and week in fetched table'
                         % self.source_str)

            # aggregate Scotland + Northern Ireland + England/Wales data into UK
            uk_agg = self.data[(self.data['CountryCode'] == 'GBRTENW') | (self.data['CountryCode'] == 'GBR_NIR') | (
                        self.data['CountryCode'] == 'GBR_SCO')]. \
                groupby(['timestamp', 'Sex']).agg({'D0_14': 'sum', 'D15_64': 'sum', 'D65_74': 'sum', 'D75_84': 'sum',
                                                   'D85p': 'sum', 'DTotal': 'sum'})
            new = pd.DataFrame(data=None, columns=self.data.columns, index=uk_agg.reset_index().index)
            new[uk_agg.reset_index().columns.tolist()] = uk_agg.reset_index()
            new['CountryCode'] = 'United Kingdom'
            self.data = pd.concat([self.data, new])
            self.data.drop(self.data[(self.data.CountryCode == 'GBRTENW') | (self.data.CountryCode == 'GBR_NIR') | (
                        self.data.CountryCode == 'GBR_SCO')].index, inplace=True)

            # create converted list of countries
            self.data.CountryCode.replace({'AUS2': 'AUS', 'DEUTNP': 'DEU', 'FRATNP': 'FRA', 'NZL_NP': 'NZL'}, inplace=True)
            new_countries = cc.convert(sorted(set(self.data['CountryCode'])), to=COUNTRY_CLASS_SCHEME, not_found=None)
            logger.info('[%s] Structure data | Converted countries from fetched table to %s'
                         % (self.source_str, COUNTRY_CLASS_SCHEME))

            # 1st level: Countries
            for i, country in enumerate(sorted(set(self.data['CountryCode']))):
                self.structured_data[new_countries[i]] = dict()

                # 2nd level: Category
                self.structured_data[new_countries[i]][MORTALITY_STR] = dict()

                # 3rd level: Indicator
                for gender in ['m', 'f', 'b']:
                    distribution = self.data[(self.data.CountryCode == country) & (self.data.Sex == gender)].set_index(
                        'timestamp').to_dict()

                    for stratification in ['D0_14', 'D15_64', 'D65_74', 'D75_84', 'D85p', 'DTotal']:
                        self.structured_data[new_countries[i]][MORTALITY_STR][stratification + '_' + gender] = {
                            ATTR_NAME_STR: stratification + '_' + gender,
                            SOURCE_STR: self.source_str,
                            UNIT_STR: 'Number',
                            FREQ_STR: WEEKLY_STR,
                            TSTYPE_STR: NEW_STR,
                            VALUE_STR: distribution[stratification]}

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot structure data due to exception: %s' % (self.source_str, e))

        return success
