import json

from os import path
import logging
import logging.config

logging.config.fileConfig(path.join(path.dirname(__file__), '../../logging.conf'))
logger = logging.getLogger('fairisk.scripts')

DATASET_FILE_PATH = 'output/fairisk_dataset.json'
JSON_SCHEMA_OUTPUT_FILE = 'output/fairisk_dataset.schema.json'


class FAIRiskDatasetJsonSchemaCreator:

    def main():
        with open(DATASET_FILE_PATH) as json_file:
            source = json.load(json_file)

        schema = dict()
        schema['$schema'] = 'http://json-schema.org/draft-07/schema#'
        schema['type'] = 'object'
        schema['properties'] = {}
        schema['patternProperties'] = {}
        schema['patternProperties']['|'.join([country for country in source.keys()])] = {
            '$ref': '#/definitions/country'}
        schema['definitions'] = {}
        schema['definitions']['country'] = {
            'type': 'object',
            'properties': {}
        }

        for country, dataCategories in source.items():
            for dataCategory, datasetCategoryEntries in dataCategories.items():
                if dataCategory not in schema['definitions']['country']['properties']:
                    schema['definitions']['country']['properties'][dataCategory] = {
                        'countries_available': [],

                        'type': 'object',
                        'properties': {}
                    }
                schema['definitions']['country']['properties'][dataCategory]['countries_available'].append(country)
                for datasetCategoryEntry, datasetCategoryEntryAttributes in datasetCategoryEntries.items():
                    schema['definitions']['country']['properties'][dataCategory]['properties'][datasetCategoryEntry] = {
                        'type': 'object',
                        'properties': {
                                'VALUE': {
                                    'type': 'object',
                                    'properties': {},
                                    'patternProperties': {'^[0-9]*$': {'oneOf': [{'type': 'number'}, {'type': 'null'}]}},
                                    'additionalProperties': False
                                }
                        }
                    }
                    for datasetCategoryEntryAttribute, data_entry_values in datasetCategoryEntryAttributes.items():
                        if 'VALUE' != datasetCategoryEntryAttribute:
                            if datasetCategoryEntryAttribute not in schema['definitions']['country']['properties'][dataCategory]['properties'][datasetCategoryEntry]['properties']:
                                schema['definitions']['country']['properties'][dataCategory]['properties'][datasetCategoryEntry]['properties'][datasetCategoryEntryAttribute] = data_entry_values

        with open(JSON_SCHEMA_OUTPUT_FILE, 'w') as outfile:
            json.dump(schema, outfile)

        logger.info('Json schema saved at ' + JSON_SCHEMA_OUTPUT_FILE)

    if __name__ == '__main__':
        main()
