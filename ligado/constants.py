from enum import Enum

class DataSource(Enum):
    # Read data from .csv in the data directory (must first be retrieved from DB and the import-*.csv files copied from
    # the output to the data directory)
    CSV = 'csv'
    # Read data from local DB (development)
    LOCAL_DB = 'local_db'
    # Read data from remote DB (production or staging) via SSH tunnel
    REMOTE_DB = 'remote_db'
