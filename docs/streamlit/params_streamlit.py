import plotly.express as px
import streamlit as st
from utils import get_df_download_link


def render_params(dataset):
    st.title('FAIRisk - Parameters')

    st.write('The FAIRiskDataset parameter data may be loaded and exported using the following code:')
    st.code('''
    from fairiskdata import FAIRiskDataset
    dataset = FAIRiskDataset.load()
    print(dataset.export()) # Note the 'type=all' parameter is not used, not all metada will be exported (sources, unit, etc.)
    ''')

    # Filters
    st.sidebar.subheader('Filters')

    countries_filter = st.sidebar.multiselect('Countries', dataset.get_countries())
    if countries_filter:
        dataset.filter_countries(countries_filter)

    PARAMS_CATEGORIES = ['INDICATORS', 'DEMOGRAPHIC', 'SCORES']
    categories_filter = st.sidebar.multiselect('Categories', PARAMS_CATEGORIES)
    if categories_filter:
        dataset.filter_categories(categories_filter)

    attributes_filter = st.sidebar.multiselect('Attributes', list({(cat, attr) for _, cat, attr in dataset.get_attributes() if cat in PARAMS_CATEGORIES}),
                                            format_func=(
                                                lambda elem: f'{elem[0]}:{elem[1]}')
                                            )
    if attributes_filter:
        dataset.filter_attributes(attributes_filter)

    # Normalization
    st.sidebar.subheader('Normalization')

    normalize_scores = st.sidebar.checkbox('Scores')
    normalize_indicators = st.sidebar.checkbox('Indicators')

    if normalize_scores:
        dataset.normalize_scores()

    if normalize_indicators:
        dataset.normalize_indicators()

    df = dataset.export()



    st.subheader('Resulting dataset')
    st.dataframe(df)
    st.markdown(get_df_download_link(df, 'FAIRisk_parameters_data_export.csv'), unsafe_allow_html=True)

    st.subheader('Descriptive statistics')
    df_describe = df.describe()
    st.dataframe(df_describe)
    st.markdown(get_df_download_link(df_describe, 'FAIRisk_parameters_data_statistics_export.csv'), unsafe_allow_html=True)

    # Scatter plot for indicators
    st.subheader('Scatter plot')

    all_attrs = [attr for attr in df.columns if attr != 'country']
    y_axis = st.multiselect("Attributes to plot", all_attrs)
    select_all = st.checkbox('Select all?')

    chart_df = df.melt(
        id_vars=['country'],
        value_vars=all_attrs if select_all else y_axis,
        value_name="Value",
        var_name="Attribute")

    if y_axis or select_all:
        fig = px.scatter(chart_df, x="country", y="Value", color="Attribute")
        st.plotly_chart(fig)
