# Source datasets

In this document, the source datasets will be described, including their format, how they are accessed and the 
structure of the data therein.

### INFORM Risk Index

The [INFORM Risk Index](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk) is a risk assessment tool created to support 
decisions about prevention, preparedness and response to humanitarian crises and disasters. It convenes global and 
open-source data, which is then modelled following a well-described methodology in a 0-10 ranged scale to enable 
country-level comparison of risk. 

Due to the COVID-19 pandemic, INFORM has build upon this work to derive conclusions more dedicated to the specifics of 
this crisis (see [INFORM Epidemic Risk Index](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/INFORM-Epidemic-Risk-Index), 
[INFORM COVID-19 Risk Index](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Covid-19)).


**Dataset source**: [INFORM Epidemic Risk Index 2020 v0.4.1](https://drmkc.jrc.ec.europa.eu/inform-index/Portals/0/InfoRM/Epidemic/INFORM%20Epidemic%20Risk%202020%20v.041.xlsx?ver=2020-04-03-171941-160)

**Dataset format**: XLSX (excel file with multiple sheets)

**Dataset documentation**: available at the source file ('Home', 'Indicator Metadata' sheets)

**Categories in FAIRisk data model**: INDICATORS, SCORES

**Other information**: FAIRisk data model only considers the raw indicators used to model INFORM indexes ('Indicator 
Data' sheet of source file), and keeps their id, name/description, unit of measurement and survey year. 


### COVID-19 Dataset

The [COVID-19 Dataset](https://covid.ourworldindata.org) is a repository created and maintained by [Our World in Data](https://ourworldindata.org/coronavirus).
It gathers daily information on the COVID-19 pandemic for any country in the world that publishes such data. 

This dataset provides an up-to-date valuable tool to evaluate the COVID-19 pandemic progress, including information on:
- Confirmed cases and deaths
- Hospitalizations
- Testing
- Vaccination 
- Other country-related scores and indicators

To build this dataset, Our World in Data collects information from numerous sources, such as the [COVID-19 Data Repository from John Hopkins University](https://github.com/CSSEGISandData/COVID-19),
the [Data on hospitalizations from the European Centre for Disease Prevention and Control](https://www.ecdc.europa.eu/en/publications-data/download-data-hospital-and-icu-admission-rates-and-current-occupancy-covid-19),
scores and indicators from the United Nations and the World Bank, government reports, among others.

**Dataset source**: [Our World in Data COVID-19 dataset](https://covid.ourworldindata.org/data/owid-covid-data.csv)

**Dataset format**: CSV

**Dataset documentation**: available at the dataset's [homepage](https://covid.ourworldindata.org). 
A [metadata file](https://covid.ourworldindata.org/data/owid-covid-codebook.csv) is also available with the description and source of each variable.

**Categories in FAIRisk data model**: COVID, DEMOGRAPHIC, INDICATORS, SCORES

**Other information**: FAIRisk data model only retrieves from this source a subset of the available variables and only for individual countries (continent aggregations are excluded). 
Their name, description and source are maintained, except for the *human_development_index*, which has its id replaced by *HDI* for uniformization between sources.


### EUROSTAT Population Data

The [EUROSTAT Population on 1 January by age group and sex](https://ec.europa.eu/eurostat/databrowser/view/demo_pjangroup/default/table?lang=en) (*DEMO_PJANGROUP*) dataset aggregates population statistics for all European countries.
The available data are stratified by age groups (between every 5 years) and sex. 

As the European Union's official and most accurate demographic database, it is used as the primary source for population information.

**Dataset source**: [Population on 1 January by age group and sex (*DEMO_PJANGROUP*)](https://ec.europa.eu/eurostat/databrowser/view/demo_pjangroup/default/table?lang=en)

**Dataset format**: JSON (retrieved with [pyjstat](https://pypi.org/project/pyjstat/) module).

**Dataset documentation**: available at the dataset's [metadata page](https://ec.europa.eu/eurostat/cache/metadata/en/demo_pop_esms.htm). 

**Categories in FAIRisk data model**: DEMOGRAPHIC

**Other information**: FAIRisk data model retrieves demographic data from individual countries and explicitly ignores European Union aggregations.


### EUROSTAT Mortality Data

The [EUROSTAT Deaths by week, sex, 5-year age group](https://ec.europa.eu/eurostat/databrowser/view/demo_r_mweek3/default/table?lang=en) (*DEMO_R_MWK_05*) dataset aggregates weekly mortality statistics for all European countries.
The available data are stratified by age groups (between every 5 years) and sex. 

As the European Union's official and most accurate mortality database, it is used as the primary source for this type of information.

**Dataset source**: [Deaths by week, sex, 5-year age group (*DEMO_R_MWK_05*)](https://ec.europa.eu/eurostat/databrowser/view/demo_r_mweek3/default/table?lang=en)

**Dataset format**: JSON (retrieved with [pyjstat](https://pypi.org/project/pyjstat/) module).

**Dataset documentation**: available at the dataset's [metadata page](https://ec.europa.eu/eurostat/cache/metadata/en/demomwk_esms.htm). 

**Categories in FAIRisk data model**: MORTALITY

**Other information**: FAIRisk data model only retrieves mortality data from individual countries.


### Mobility

The [Movement Range Maps](https://data.humdata.org/dataset/movement-range-maps) dataset contains information about how populations are responding to physical distancing measures. In particular, there are two metrics, Change in Movement and Stay Put, that provide a slightly different perspective on movement trends. Change in Movement looks at how much people are moving around and compares it with a baseline period that predates most social distancing measures, while Stay Put looks at the fraction of the population that appear to stay within a small area during an entire day.

**Dataset source**: [Movement Range Maps](https://data.humdata.org/dataset/movement-range-maps)

**Dataset format**: CSV.

**Dataset documentation**: available at the dataset's [metadata page](https://data.humdata.org/dataset/movement-range-maps). 

**Categories in FAIRisk data model**: MOBILITY

**Other information**: The baseline used reports of February 2020. The data from different regions were aggregated by calculating the mean and standard deviation of all polygons belonging to a given country.


### HMD Mortality Data

The Human Mortality Database's [Short-term Mortality Fluctuations (STMF)](https://www.mortality.org/) data series aggregates weekly mortality information from currently 38 countries.
Created in response to the COVID-19 pandemic, this database provides an objective tool for the evaluation of different countries.

The database is stratified by sex and five age groups (0-14 years, 15-64 years, 65-74 years, 75-84 years, and 85 years or more).

**Dataset source**: [Short-term Mortality Fluctuations (STMF) Database](https://www.mortality.org/Public/STMF/Outputs/stmf.csv)

**Dataset format**: CSV

**Dataset documentation**: data formats and methods are described in the [STMFNote](https://www.mortality.org/Public/STMF_DOC/STMFNote.pdf) file. 
A [metadata document](https://www.mortality.org/Public/STMF_DOC/STMFmetadata.pdf) is also available.

**Categories in FAIRisk data model**: MORTALITY

**Other information**: STMF database presents data for the United Kingdom divided by their countries, but the FAIRisk data model aggregates all data into one entry to uniformize with remaining datasets.


### The Global Health Observatory (GHO) data repository

The GHO data repository is maintained by the World Health Organization (WHO) and provides an interface to access 
numerous health-related statistics for its member states. The indicators relate to several priority health topics, 
namely mortality, diseases, health systems, and others. 

**Dataset source**: [Main API URL](https://ghoapi.azureedge.net/api/)

**Dataset format**: OData Protocol

**Dataset documentation**: [API documentation](https://www.who.int/data/gho/info/gho-odata-api)

**Categories in FAIRisk data model**: INDICATORS, SCORES

**Other information**: FAIRisk fetchers consider the following parameters for data query: only country-level information,
aggregated data (i.e. null dimensions), of numerical value, available per year after 2015. Indicators' id, 
name/description, and year/value information are preserved in the FAIRisk data model. Only the most recent value 
available for each indicator is considered. Unit of measurement is extrapolated from indicators' name and may be one 
of: index, standardized (refers to some type of normalization, usually by population), percentage, and number. Due to 
the high volume of indicators, and the inference of category and unit from the attribute name, some assignment errors 
may occur, so we recommend their thorough analysis upon use.
