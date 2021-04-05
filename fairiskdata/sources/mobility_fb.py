from . import *

from hdx.hdx_configuration import Configuration
from hdx.data.dataset import Dataset as dataset_hdx
from io import BytesIO
from zipfile import ZipFile
import requests

import logging
logger = logging.getLogger('fairisk')

class MobilityFbDataset(Dataset):

    USE_COLS = ['all_day_bing_tiles_visited_relative_change', 'all_day_ratio_single_tile_users']

    AGG_METRICS = ['mean', 'std']

    def __init__(self):
        super().__init__()

    def _fetch(self, host='', source_str='Movement Range Maps from Facebook'):

        success = False

        # FIXME: add date of fetch to source_str since it does not have version?
        self.source_str = source_str

        try:
            Configuration.create(hdx_site='prod', user_agent='FAIRisk', hdx_read_only=True)
            resources = dataset_hdx.read_from_hdx("movement-range-maps").get_resources()
            Configuration.delete()
            for res in resources:

                if res['name'][-3:] == 'zip':
                    req = requests.get(res['url'])
                    file = ZipFile(BytesIO(req.content))

                    names = file.namelist()
                    names.remove('README.txt')

                    self.data = pd.read_csv(file.open(names[0]), sep='\t', low_memory=False)

                    success = True

        except Exception as e:
            logger.critical('[%s] Cannot fetch data due to exception: %s' % (self.source_str, e))

        return success

    def _structure(self, use_cols=USE_COLS, agg_metrics=AGG_METRICS):

        success = False

        self.structured_data = dict()

        cc = coco.CountryConverter()

        try:
            # create converted list of countries
            new_countries = cc.convert(sorted(set(self.data['country'])), to=COUNTRY_CLASS_SCHEME, not_found=None)

            # aggregate data from different regions with mean and std
            agg_data = self.data.groupby(['ds', 'country']).agg({col: agg_metrics for col in use_cols}).reset_index()

            # 1st level: Countries
            for i, country in enumerate(sorted(set(self.data['country']))):

                self.structured_data[new_countries[i]] = dict()

                # 2nd level: Categories
                self.structured_data[new_countries[i]][MOBILITY_STR] = dict()

                # UNIT_STR describes the baseline data (e.g. february 2020) and type (e.g. day of week)
                base_name, base_type = \
                    self.data[self.data.country == country][['baseline_name', 'baseline_type']].value_counts().index[0]

                for col in use_cols:
                    for metric in agg_metrics:
                        self.structured_data[new_countries[i]][MOBILITY_STR][col + '_' + metric] = \
                            {ATTR_NAME_STR: col + '_' + metric,
                             SOURCE_STR: self.source_str,
                             UNIT_STR: 'Relation to baseline (' + base_name + ' - ' + base_type + ')',
                             FREQ_STR: DAILY_STR,
                             TSTYPE_STR: CURRENT_STR,
                             VALUE_STR: agg_data[agg_data.country == country][[['ds', ''], [col, metric]]].fillna(0).
                                 set_index('ds').to_dict()[(col, metric)]}

            success = True

        except Exception as e:
            logger.critical('[%s] Cannot structure data due to exception: %s' % (self.source_str, e))

        return success
