
from fairiskdata.utils.age_parsers import safe_parse_age_group, do_ranges_overlap
from fairiskdata.utils.parsers import safe_parse_sex


class AgeResampler:

    GRANULARITY = {
        'LOW': [(None, None)],
        'MEDIUM': [(None, 14), (15, 64), (65, None)],
        'HIGH': [(None, 14), (15, 64), (65, 74), (75, 84), (85, None)]
    }

    def __init__(self,
                 granularity: str):
        self.granularity = granularity

    def resample(self,
                 attrs_dict: dict):

        """
        Resamples the ages for attr_dict of category
        :param attrs_dict:
        :return:
        """

        resampled = dict()

        for attr_key, attr in attrs_dict.items():

            sex = safe_parse_sex(attr_key)
            age = safe_parse_age_group(attr_key)

            # Case of demographic data from COVID which only has total population
            if self.granularity == 'LOW' and attr_key == 'population':
                resampled['Total_Total'] = attr
                resampled['Total_Total']['ATTR_NAME'] = 'Total_Total'

            if age is None:
                continue

            for group in self.GRANULARITY[self.granularity]:
                if do_ranges_overlap(group, age):

                    if group[0] is None and group[1] is None:
                        age_group = 'Total'
                    elif group[0] is None:
                        age_group = '-' + str(group[1])
                    elif group[1] is None:
                        age_group = str(group[0]) + '+'
                    else:
                        age_group = str(group[0]) + '-' + str(group[1])

                    if age_group + '_' + sex not in resampled:
                        resampled[age_group + '_' + sex] = attr
                        resampled[age_group + '_' + sex]['ATTR_NAME'] = age_group + '_' + sex

                    else:
                        resampled[age_group + '_' + sex]['VALUE'] += attr['VALUE']

        return resampled