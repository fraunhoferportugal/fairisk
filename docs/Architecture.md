# Architecture
FAIRisk's architecture consists of two main parts: 1) a data fetching layer which contains all the necessary fetching 
and parsing steps, generating a single JSON file; 2) a set of methods that will provide the user the possibility to 
query, transform and export the data.

All parts are available using the methods of a single exposed class (*FAIRiskDataset*).


### Data fetching layer

This layer consists of multiple data fetchers (sources package), one for each external data source. These are 
responsible for converting external data into a single JSON file that can be persisted locally. Thus, the first 
utilization requires fetching all data from sources. This process can take several minutes. After the generation of the
local JSON file, data from that file will always be loaded by default.

```python
from fairiskdata import FAIRiskDataset
dataset = FAIRiskDataset.load()
```

### Data query, transformation and export methods

To simplify the use of data, a set of methods were implemented to provide the user the possibility to query the local 
JSON data file, perform data transformations, and export the final dataset in a standard format.

There are some methods available to modify the data to export:
- **Data query** - Filtering data by country, category, attributes, time intervals, age groups and removing entries 
with N missing values.
- **Data harmonization** - Allows time-series sampling rate conversion to specific time-frames (DAILY, WEEKLY, MONTHLY, 
YEARLY) and standardization of age groups granularity (LOW, MEDIUM, HIGH).
- **Data normalization** - Enables the normalization of scores and indicators to a 0 to 1 range using Min-Max scaling.
- **Excess mortality** - Computes and adds excess mortality estimation (P-score, Absolute) to the MORTALITY category of
the dataset.

After all modifications, data can be exported as a *pandas.DataFrame* object.
