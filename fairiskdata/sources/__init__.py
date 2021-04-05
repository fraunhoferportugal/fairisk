
import country_converter as coco

from .dataset import *


# Structured dictionary
# Country classification scheme
COUNTRY_CLASS_SCHEME = 'name_short'

# Countries' entity sub-groups
INDICATORS_STR = 'INDICATORS'
SCORES_STR = 'SCORES'
COVID_STR = 'COVID'
MORTALITY_STR = 'MORTALITY'
DEMOGRAPHIC_STR = 'DEMOGRAPHIC'
MOBILITY_STR = 'MOBILITY'

# TypeAttr keys
ATTR_NAME_STR = 'ATTR_NAME'
SOURCE_STR = 'SOURCE'

# FloatAttr keys
VALUE_STR = 'VALUE'
UNIT_STR = 'UNIT'

# TimeSeriesAttr keys
FREQ_STR = 'FREQUENCY'
TSTYPE_STR = 'SERIES_TYPE'

# Frequency keys
DAILY_STR = 'DAILY'
WEEKLY_STR = 'WEEKLY'
MONTHLY_STR = 'MONTHLY'
YEARLY_STR = 'YEARLY'

# Time series type keys
TOTAL_STR = 'TOTAL'
NEW_STR = 'NEW'
CURRENT_STR = 'CURRENT'
NONAPPLICABLE_STR = 'NA'

# Available Datasets
COVID = 'COVID'
DEMO_EUROSTAT = 'EUROSTAT_DEMOGRAPHIC'
MORT_EUROSTAT = 'EUROSTAT_MORTALITY'
GHO = 'GHO'
INFORM = 'INFORM'
MOBILITY = 'MOBILITY'
MORTALITY = 'MORTALITY'

ALL_DATASETS_LIST = [COVID, DEMO_EUROSTAT, MORT_EUROSTAT, GHO, INFORM, MOBILITY, MORTALITY]
""" The list of all suported datasets that may be downloaded (used by default). """
