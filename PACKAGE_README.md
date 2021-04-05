# FAIRisk | Improving risk estimation with open resources

FAIRisk combines open-source globally available data related with risk scales and country preparedness for epidemic 
crisis with post-COVID-19 data. It aims to facilitate the creation of preventive insights at country-level and the 
suggestion of improvements to current risk modelling strategies, and assist the work of the scientific community and 
decision-makers dealing with COVID-19 (or related) crisis.

This repository addresses data interoperability challenges of fetching and combining several openly available sources 
of multimodal data, so these can be coherently used from a centralized data model. This model was designed bearing 
FAIR principles and EU's open data guidelines in mind to promote an adequate, well-documented and simplified use of 
the combined data.
 

### Approach

A semantic data model was defined, following the analysis of several relevant sources, in order to typify and indentify 
the most relevant concepts, while attempting to maximize its generalization. Data from 6 different sources was 
organized and merged in a single data model, where each country entity is represented by up to 6 categories:

- Demographics: population by age group.
- Indicators: raw indicators' data measured for each country.
- Scores: indexes, scales, or scores that assist the comparison of qualitative or estimated parameters across 
countries.
- Mortality: count of deaths by age group.
- COVID-19: number of cases, deaths, tests, ICU patients, hospitalizations, vaccinations, and stringency index due to 
the COVID-19 pandemic.
- Mobility: statistics of citizens movement estimations.

Check out our [architecture documentation](https://github.com/fraunhoferportugal/fairisk/blob/main/docs/index.md) for more details.  


### Getting started

Jump to our [getting started guide](https://github.com/fraunhoferportugal/fairisk/blob/main/docs/GettingStarted.md). 
Data exploration, visualization, and export is also possible using [our simple streamlit application](https://github.com/fraunhoferportugal/fairisk/blob/main/docs/Streamlit.md).
Also, you may read our [full documentation](https://github.com/fraunhoferportugal/fairisk/blob/main/docs/index.md).


### License

All visualizations and code available in this repository are licensed under the [Creative Commons BY-NC-SA 4.0 
license](https://creativecommons.org/licenses/by-nc-sa/4.0/).

All data fetched by the methods available in this repository was produced by third-parties and is subject to the license 
terms from the original third-party authors. The sources from which data was fetched are kept and made available as 
metadata at all stages. Sources are also detailed [here](https://github.com/fraunhoferportugal/fairisk/blob/main/docs/SourceDatasets.md). You should always check the license of all third-party data before use.


### Funding

The authors would like to acknowledge the financial support obtained from EOSCsecretariat.eu. EOSCsecretariat.eu has 
received funding from the European Union's Horizon Programme call H2020-INFRAEOSC-05-2018-2019, grant Agreement 
number 831644.


### Authors

These resources were developed by [Fraunhofer AICOS](https://www.aicos.fraunhofer.pt/en/home.html).

**Development team**: Diana Gomes (diana.gomes@fraunhofer.pt), Catarina Pires (catarina.pires@fraunhofer.pt), 
David Ribeiro (david.ribeiro@fraunhofer.pt), Duarte Folgado (duarte.folgado@fraunhofer.pt), 
Ricardo Santos (ricardo.santos@fraunhofer.pt), Telmo Barbosa (telmo.barbosa@fraunhofer.pt).
