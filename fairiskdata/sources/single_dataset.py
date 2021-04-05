import os
from mergedeep import merge
import simplejson as json

from .inform import INFORMDataset
from .eurostat import MortalityEurostatDataset, DemographicEurostatDataset
from .covid_owid import CovidOWiD
from .gho import GHODataset
from .mobility_fb import MobilityFbDataset
from .mortality_hmd import MortalityHMDDataset
from . import *

PREVALENCE_DICT = {MORTALITY_STR: [MORT_EUROSTAT, MORTALITY],
                   DEMOGRAPHIC_STR: [DEMO_EUROSTAT, COVID, INFORM],
                   SCORES_STR: [INFORM, COVID]}

import logging
logger = logging.getLogger('fairisk')

def fetch_data(datasets_list=ALL_DATASETS_LIST):

    datasets = dict()

    for dataset_name in datasets_list:

        logger.info('Fetching %s data' % dataset_name)

        # COVID dataset
        if dataset_name == COVID:
            datasets[COVID] = CovidOWiD()

        # DEMOGRAPHIC EUROSTAT dataset
        elif dataset_name == DEMO_EUROSTAT:
            datasets[DEMO_EUROSTAT] = DemographicEurostatDataset()

        # MORTALITY EUROSTAT dataset
        elif dataset_name == MORT_EUROSTAT:
            datasets[MORT_EUROSTAT] = MortalityEurostatDataset()

        # GHO dataset
        elif dataset_name == GHO:
            datasets[GHO] = GHODataset()

        # INFORM dataset
        elif dataset_name == INFORM:
            datasets[INFORM] = INFORMDataset()

        # MOBILITY dataset
        elif dataset_name == MOBILITY:
            datasets[MOBILITY] = MobilityFbDataset()

        # MORTALITY dataset
        elif dataset_name == MORTALITY:
            datasets[MORTALITY] = MortalityHMDDataset()

        else:
            logger.warning('Skipping unknown dataset: %s' % dataset_name)
            continue

        success = datasets[dataset_name].fetch()
        if not success:
            del datasets[dataset_name]

    return datasets


def structure_data(datasets_dict):

    datasets_list = list(datasets_dict.keys())
    for dataset_name in datasets_list:

        if dataset_name not in ALL_DATASETS_LIST:
            logger.warning('Skipping unknown dataset: %s' % dataset_name)
            continue

        logger.info('Structuring %s data' % dataset_name)

        success = datasets_dict[dataset_name].structure()
        if not success:
            del datasets_dict[dataset_name]

    return datasets_dict


def merge_datasets(datasets_dict):

    single_dataset = dict()
    sources = dict()

    for dataset_name in datasets_dict.keys():

        if dataset_name not in ALL_DATASETS_LIST:
            logger.warning('Skipping unknown dataset: %s' % dataset_name)
            continue

        sources[dataset_name] = datasets_dict[dataset_name].get_source_str()

        logger.info('Merging %s data' % dataset_name)
        merge(single_dataset, datasets_dict[dataset_name].get_structured_data())

    return single_dataset, sources


def set_prevalence(datasets_dict, sources_list):

    # Define prevalence of sources for DEMOGRAPHIC, MORTALITY and SCORES data
    # Note: if there are SCORES from INFORM dataset, then no SCORES from COVID dataset will be kept
    # (only human development index exists, which is overlapped but presents uncertain values)
    for entity_name, prevalence_list in PREVALENCE_DICT.items():
        logger.info('Setting prevalence for %s entity group' % entity_name)

        for country in datasets_dict.keys():
            if entity_name in datasets_dict[country].keys():

                # Replace data for each entity by the first source in PREVALENCE_DICT
                for source in prevalence_list:
                    if source in sources_list and any([sources_list[source] in att_dict[SOURCE_STR] for att_dict in datasets_dict[country][entity_name].values()]):
                        datasets_dict[country][entity_name] = {att: att_dict for att, att_dict in datasets_dict[country][entity_name].items() if sources_list[source] in att_dict[SOURCE_STR]}

                        if source == COVID and entity_name == SCORES_STR:
                            datasets_dict[country][entity_name]['HDI'] = datasets_dict[country][entity_name].pop('human_development_index')

                        break

    return datasets_dict


def export_dataset(dataset, json_file_path='output/fairisk_dataset.json'):

    # Create output directory (if it doesn't exist)
    directory = os.path.abspath(os.path.join(json_file_path, os.pardir))
    os.makedirs(directory, exist_ok=True)

    # Save data in json
    with open(json_file_path, 'w+') as f:
        json.dump(dataset, f, ignore_nan=True)

    logger.info('Exported FAIRISK_DATASET in %s' % json_file_path)

    return


def fetch_and_export(
        json_file_path="output/fairisk_dataset.json",
        datasets_list=ALL_DATASETS_LIST):
    # Fetch data from sources
    logger.info('Fetching data from sources')
    datasets = fetch_data(datasets_list=datasets_list)  # Without GHO (for speed)

    # Structure all data according to FAIRisk data model
    logger.info('Structure all data according to FAIRisk data model')
    datasets = structure_data(datasets)

    # Merge all data in single dataset
    logger.info('Merge all data in single dataset')
    fairisk_dataset, sources_list = merge_datasets(datasets)

    # Set prevalence between datasets
    logger.info('Set prevalence between overlapping datasets')
    fairisk_dataset = set_prevalence(fairisk_dataset, sources_list)

    # Export FAIRisk dataset as .pkl
    logger.info('Exporting data')
    export_dataset(fairisk_dataset, json_file_path=json_file_path)


if __name__ == '__main__':
    fetch_and_export()

