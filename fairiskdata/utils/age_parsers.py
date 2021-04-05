import re

def safe_parse_age_group(attribute_key):
    # Demographics patterns
    match = re.match("from\s+(\d+)\s+to\s+(\d+)",
                     attribute_key, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    match = re.match("(\d+).*or over", attribute_key, re.IGNORECASE)
    if match:
        return (int(match.group(1)), None)
    match = re.match("less than.*(\d+)", attribute_key, re.IGNORECASE)
    if match:
        return (None, int(match.group(1)))

    # Mortality pattern
    match = re.match("d(\d+)(?:_(\d+))?", attribute_key, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2))) if match.group(2) is not None else (int(match.group(1)), None)

    # TODO if these matches work
    # Resampled ages pattern
    match = re.match("(\d+)(?:\-|_)(\d+)", attribute_key, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    match = re.match("\-(\d+)", attribute_key, re.IGNORECASE)
    if match:
        return (None, int(match.group(1)))

    match = re.match("(\d+)\+", attribute_key, re.IGNORECASE)
    if match:
        return (int(match.group(1)), None)

    return None


def do_ranges_overlap(a, b):
    (a1, a2) = a
    (b1, b2) = b
    return (a2 is None or b1 is None or b1 <= a2) and (a1 is None or b2 is None or a1 <= b2)