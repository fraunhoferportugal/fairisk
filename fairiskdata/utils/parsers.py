import re


def safe_parse_sex(attribute_key: str):

    # TODO: change these verification to use regex?
    if '_f' in attribute_key.lower():
        return 'Female'
    if '_m' in attribute_key.lower():
        return 'Male'
    if '_t' in attribute_key.lower():
        return 'Total'
    if '_b' in attribute_key.lower():
        return 'Total'

    return None