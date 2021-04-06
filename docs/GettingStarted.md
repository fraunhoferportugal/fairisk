# Getting started

### Installation

You can install our python package using pip:

```bash
pip install fairiskdata
```

### How to use

We have compiled a sample notebook to demonstrate the use of the library and its methods.
You can access it [here](../sample.ipynb).

[These are the instructions to configure the logging level](./Logging.md)

### Streamlit

A [streamlit](https://streamlit.io/) web app is included in this project with a demonstrator for parameters and time-series data.

The web app allows the user to do operations on the dataset, visualize it, and export to a CSV. To run the application, its dependencies need to be installed before running the application.

Install the requirements:
```bash
pip install -r docs/streamlit/requirements.txt
```

Run the web app:
```bash
streamlit run docs/streamlit/home_streamlit.py
```
 By default, the web app will be accessible from http://localhost:8501/
