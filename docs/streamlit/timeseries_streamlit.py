import streamlit as st
import pandas as pd
import plotly.express as px
from utils import get_df_download_link


def render_timeseries(dataset):
  st.title('FAIRisk - timeseries')

  st.write('The FAIRiskDataset timeseries data may be loaded and exported using the following code:')
  st.code('''
  from fairiskdata import FAIRiskDataset
  dataset = FAIRiskDataset.load()
  print(dataset.export(type='timeseries')) # Note the 'type=all' parameter is not used, not all metada will be exported (sources, unit, etc.)
  ''')

  ##################################
  # Data selection
  st.sidebar.subheader('Filters')

  # Countries
  all_contries_list = dataset.get_countries()
  chosen_countries = st.sidebar.multiselect("Countries",
                                    all_contries_list,
                                    ['Portugal', 'Spain'])
  if chosen_countries:
    dataset.filter_countries(chosen_countries)

  # Categories
  timeseries_categories = []
  for dataCategories in dataset.get().values():
    for dataCategory, datasetCategoryEntries in dataCategories.items():
      # Only with timeseries attrs
      if dataCategory not in timeseries_categories\
              and any('FREQUENCY' in datasetCategoryEntries[parameter] for parameter in datasetCategoryEntries.keys()):
          timeseries_categories.append(dataCategory)

  if not timeseries_categories:
    st.write("No timeseries data for the selected countries")
    st.stop()

  chosen_categories = st.sidebar.multiselect(
      "Categories", timeseries_categories, timeseries_categories[:1])

  # Filters
  st.sidebar.subheader('Filters')
  enable_filter_age_group = st.sidebar.checkbox('Filter age group')
  filter_age_group_values = st.sidebar.slider('Age group filter', 0, 130, (25, 75))
  if enable_filter_age_group:
    dataset.filter_age_group(filter_age_group_values)

  # Resampling
  st.sidebar.subheader('Resampling')
  resample_option = st.sidebar.selectbox(
      'Resample dates', (None, 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'), 0)
  if resample_option:
      dataset.resample(resample_option)

  resample_age_groups_option = st.sidebar.selectbox(
      'Resample age groups', (None, 'LOW', 'MEDIUM', 'HIGH'), 0)
  if resample_age_groups_option:
    dataset.resample_age_groups(resample_age_groups_option)

  # Excess mortality
  if 'MORTALITY' in chosen_categories or not chosen_categories:
    st.sidebar.subheader('Excess mortality')
    add_excess_mortality_estimation = st.sidebar.checkbox(
        'Add excess mortality estimation')
    if add_excess_mortality_estimation:
      dataset.add_excess_mortality_estimation(resample_age_groups_option) if resample_age_groups_option else dataset.add_excess_mortality_estimation()

  # Attributes
  timeseries_attrs_ = []
  for country, dataCategories in dataset.get().items():
    if not chosen_countries or country in chosen_countries:
      for dataCategory, datasetCategoryEntries in dataCategories.items():
        if not chosen_categories or dataCategory in chosen_categories:
          for parameter in datasetCategoryEntries.keys():
            # Only timeseries attrs
            if 'FREQUENCY' in datasetCategoryEntries[parameter] and (dataCategory, parameter) not in timeseries_attrs_:
              timeseries_attrs_.append((dataCategory, parameter))

  chosen_attributes = st.sidebar.multiselect("Attributes",
                                    timeseries_attrs_,
                                    timeseries_attrs_[:2],
                                    format_func=(lambda el: f'{el[0]}:{el[1]}'))
  if chosen_attributes:
    dataset.filter_attributes(chosen_attributes)
  if not chosen_attributes:  # Will remove non timeseries attrs, seperated from previous 'if' for echo purposes
    dataset.filter_attributes(timeseries_attrs_)

  if not timeseries_attrs_:
    st.write("No attributes available")
    st.stop()

  ##################################
  # Show
  st.subheader('Resulting dataset')

  # Export
  e_timeseries = dataset.export(type='timeseries')

  # Table
  st.dataframe(e_timeseries)

  # Download link
  st.markdown(get_df_download_link(e_timeseries, 'FAIRisk_timeseries_data_export.csv'), unsafe_allow_html=True)

  # Chart
  st.subheader('Line plot')

  dfs_by_country = []  # country * cols for charting purposes
  for df_country_name in e_timeseries.country.unique():
    country_df = e_timeseries[e_timeseries['country'] == df_country_name]
    new_columns = {item: f'{df_country_name}:{item}' for item in list(e_timeseries.columns) if item not in [
        'country', 'timestamp', 'parsed_timestamp']}
    country_df = country_df.rename(columns=new_columns)
    dfs_by_country.append(country_df)
  new_pd = pd.concat(dfs_by_country).groupby('parsed_timestamp').first().reset_index()

  chart_columns = [item for item in list(new_pd.columns) if item not in [
      'country', 'timestamp', 'parsed_timestamp']]
  chart = px.line(new_pd, x="parsed_timestamp", y=chart_columns)
  st.plotly_chart(chart)
