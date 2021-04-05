
import pandas as pd
import logging

logger = logging.getLogger('fairisk')

class Dataset:

    def __init__(self):

        self.source_str = ''
        self.data = pd.DataFrame()
        self.structured_data = dict()

    def _fetch(self, host='', source_str=''):
        '''To be implemented by each subclass'''
        return bool

    # TODO: implement data integrity verification for each dataset (after fetch)
    def _verify_data_integrity(self):
        '''To be implemented by each subclass'''
        return True

    def _structure(self):
        '''To be implemented by each subclass'''
        return bool

    def fetch(self, host='', source_str=''):
        success = False
        if self.data.empty:
            if host and source_str:
                success = self._fetch(host=host, source_str=source_str)
            elif host:
                success = self._fetch(host=host)
            elif source_str:
                success = self._fetch(source_str=source_str)
            else:
                success = self._fetch()

            if success:
                success = self._verify_data_integrity()
        logger.info('[%s] Fetch data | Success: %s' % (self.source_str, success))

        return success

    def structure(self):
        success = False
        if not self.structured_data:
            if isinstance(self.data, dict):
                if self.data:
                    success = self._structure()
                else:
                    raise AssertionError('No data was found to structure.')
            elif isinstance(self.data, pd.DataFrame):
                if not self.data.empty:
                    success = self._structure()
                else:
                    raise AssertionError('No data was found to structure.')
            else:
                raise AssertionError('Unknown data type: %s' % type(self.data))
        logger.info('[%s] Structure data | Success: %s' % (self.source_str, success))

        return success

    def get_data(self):
        return self.data

    def get_structured_data(self):
        return self.structured_data

    def get_source_str(self):
        return self.source_str


