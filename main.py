import streamlit as st
import pandas as pd
from io import StringIO
import datetime
import codecs
from enum import StrEnum
from qqcsvtools import CSVImport

TITLE = 'QQ CSV Tools'

def file_changed(): 
    if 'upload_file' in st.session_state and st.session_state['upload_file'] is not None:
        st.session_state['csv_import'] = CSVImport(st.session_state['upload_file'])
        # Clear QQ-specific session values
        st.session_state.pop('start_datetime', None)

    else:
        # clear file session data if upload closed
        for k in ['upload_file', 'csv_import', 'start_datetime']:
            if k in st.session_state:
                del st.session_state[k]

def write_csv_summary(csv_import: CSVImport):
    cols, rows = csv_import.dataframe.shape

    st.write(f'CSV Type:  :green[{csv_import.csv_type}]')
    st.write(f'Encoding:  :green[{csv_import.encoding}]')    
    st.write(f'Shape:  :green[{cols:,d} x {rows}]')


def main():
    st.title(TITLE)
    st.write("")
    
    uploaded_file = st.file_uploader(label='Select a QQ or EXO CSV File:',
                                     on_change=file_changed,
                                     key='upload_file',
                                     type="csv")

    if 'csv_import' in st.session_state:
        csv_import: CSVImport = st.session_state['csv_import']

        # Draw QQ summary and Date Adjustment Tools
        if csv_import.csv_type == CSVImport.CSV_TYPE.QQ:
            # Initialize session-persistent start_datetime
            if 'start_datetime' not in st.session_state:
                st.session_state['start_datetime'] = pd.to_datetime(csv_import.dataframe['DateTime'][0])

            with st.container(border=True):
                col1, col2 = st.columns(2)

                with col1:
                    cols, rows = csv_import.dataframe.shape

                    st.write(f'CSV Type:  :green[{csv_import.csv_type}]')
                    st.write(f'Encoding:  :green[{csv_import.encoding}]')
                    st.write(f'Shape:  :green[{cols:,d} x {rows}]')

                with col2:
                    start_datetime = st.session_state['start_datetime']
                    
                    with st.form(key='info_form'):
                        st.write(f'Start DateTime:  :green[{start_datetime}]')
                        st.caption(f'Optionally select a new Date and Time in order to correct '
                                    'the first DateTime (if needed).')

                        st.write(f'Select a new Start Date and Time to shift ')
                        d = st.date_input("Start Date", value=start_datetime.date(), key='start_date')
                        t = st.time_input("Start Time", value=start_datetime.time(), key='start_time')
                        submit = st.form_submit_button('Adjust DateTime', type='secondary')

            # If QQ DateTime Adjustment Submitted
            if submit:
                form_datetime = datetime.datetime.combine(st.session_state['start_date'], st.session_state['start_time'])
                time_adjust = form_datetime - st.session_state['start_datetime']
                csv_import.dataframe['DateTime'] = (
                    pd.to_datetime(csv_import.dataframe['DateTime']) + time_adjust
                ).dt.strftime('%Y-%m-%d %H:%M:%S')

                # Update session state value
                st.session_state['start_datetime'] = form_datetime

        # Draw EXO summary and Date Adjustment Tools
        elif csv_import.csv_type == CSVImport.CSV_TYPE.EXO:
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    write_csv_summary(csv_import)
                with col2:
                    "Column 2"


        # Display Previews
        if csv_import.csv_type == CSVImport.CSV_TYPE.QQ:
            st.subheader("Previews:")
            tab_data_preview, tab_chart_preview = st.tabs(["🗃 Data", "📈 Chart"])
       
            preview_df = csv_import.dataframe
            with tab_data_preview:
                preview_lines_count = min(10, preview_df.shape[0])
                st.write(f'Previewing {preview_lines_count} of {preview_df.shape[0]:,d} rows')
                st.dataframe(preview_df[0:preview_lines_count]) # Up to 10 rows in preview

            with tab_chart_preview:
                st.line_chart(preview_df,
                                x= 'DateTime',
                                y=['EC(uS/cm)', 'Temp(oC)', 'EC.T(uS/cm)' ],
                                color=['#FF0000', '#00FF00', '#0000FF']
                                )


    st.session_state

    st.divider()
    st.markdown(
        f'<div style="text-align: right;">{TITLE} by Christopher Lafferty</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
