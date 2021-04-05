import datetime
import re
import pandas as pd


def safe_date_parse(date):
    # Weeks
    match = re.match("\d\d\d\dW\d(?:\d)?$", date)
    if match:
        end = datetime.datetime.strptime(
            date + '-1', "%YW%W-%w")
        start = end - datetime.timedelta(days=7)

        return pd.Interval(
            pd.Timestamp(start),
            pd.Timestamp(end) - pd.Timedelta(nanoseconds=1),
            closed='both')

    # Years range (e.g. '2010-2015')
    match = re.match("(\d\d\d\d)-(\d\d\d\d)$", date)
    if match:
        return pd.Interval(
            pd.Timestamp(match.group(1)),
            pd.Period(match.group(2)).end_time,
            closed='both')

    try:
        timestamp = pd.Timestamp(date)

        # Months
        match = re.match("(\d\d)-(\d\d\d\d)$", date)
        if match:
            period = timestamp.to_period(freq='M')
            return pd.Interval(
                period.start_time,
                period.end_time,
                closed='both')

        match = re.match("(\d\d)/(\d\d\d\d)$", date)
        if match:
            period = timestamp.to_period(freq='M')
            return pd.Interval(
                period.start_time,
                period.end_time,
                closed='both')

        # Year
        match = re.match("(\d\d\d\d)$", date)
        if match:
            period = timestamp.to_period(freq='Y')
            return pd.Interval(
                period.start_time,
                period.end_time,
                closed='both')

        return pd.Timestamp(date)

    except:
        # raise RuntimeError("Unknown format for date: '{}'".format(date))
        return None


def safe_sortable_date_parse(date):
    parsed = safe_date_parse(date)
    if isinstance(parsed, pd.Interval):
        return parsed.left
    return parsed


def safe_interval_parse(interval):
    if not (isinstance(interval.left, pd.Timestamp) and isinstance(interval.right, pd.Timestamp)):
        start = safe_date_parse(interval.left)
        end = safe_date_parse(interval.right)
        interval.left = start if isinstance(start, pd.Timestamp) else start.left
        interval.right = end if isinstance(end, pd.Timestamp) else end.right

    if interval.right > interval.left:
        return interval
    elif interval.left == interval.right:
        return pd.Interval(interval.left, interval.right + pd.Timedelta(days=1), closed='left')
    else:
        if interval.open_start and interval.open_end:
            closed_str = 'neither'
        elif interval.open_start:
            closed_str = 'left'
        elif interval.open_end:
            closed_str = 'right'
        else:
            closed_str = 'both'
        return pd.Interval(interval.right, interval.left, closed=closed_str)
