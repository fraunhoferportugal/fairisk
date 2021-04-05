import base64


def get_df_download_link(df, file_name='data.csv', title='Download csv file'):
  csv = df.to_csv(index=False)
  b64 = base64.b64encode(csv.encode()).decode()
  href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">{title}</a>'
  return href
