import streamlit as st
import pandas as pd
import datetime
from qqcsvtools import CSVImport

TITLE = 'QQ CSV Tools'

def file_changed(): 
    if 'upload_file' in st.session_state and st.session_state['upload_file'] is not None:
        st.session_state['csv_import'] = CSVImport(st.session_state['upload_file'])


        st.session_state['CSV Type'] = st.session_state['csv_import'].csv_type
        st.session_state['Encoding'] = st.session_state['csv_import'].encoding
        st.session_state['Shape'] = (f'{st.session_state['csv_import'].dataframe.shape[0]:,d} rows x '
                                    f'{st.session_state['csv_import'].dataframe.shape[1]} cols')

        for k in ['start_datetime', 'adjust_pending']:
            st.session_state.pop(k, None)
    else:
        # clear file session data if upload closed
        for k in ['upload_file', 'csv_import', 'start_datetime', 'adjust_pending',
                   'start_date', 'start_time', 'import_summary', 'CSV Type', 'Encoding', 'Shape']:
            st.session_state.pop(k, None)

def write_csv_summary():   
    write_lines = ['CSV File Summary:']
    for k in ['CSV Type', 'Encoding', 'Shape']:
        
        write_lines.append(f' * {k}:  :green[{st.session_state[k]}]')
    st.write('\n'.join(write_lines))


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
        if st.session_state.get('CSV Type', "") == "qq":
            # Initialize session-persistent start_datetime
            if 'start_datetime' not in st.session_state:
                st.session_state['start_datetime'] = pd.to_datetime(csv_import.dataframe['DateTime'][0])
            else:
                if 'start_date' in st.session_state and 'start_time' in st.session_state:
                    potential_new = datetime.datetime.combine(
                        st.session_state['start_date'], st.session_state['start_time']
                    )
                    if st.session_state.get('adjust_pending', False):
                        time_adjust = potential_new - st.session_state['start_datetime']
                        csv_import.dataframe['DateTime'] = (
                            pd.to_datetime(csv_import.dataframe['DateTime']) + time_adjust
                        ).dt.strftime('%Y-%m-%d %H:%M:%S')
                        st.session_state['start_datetime'] = potential_new
                        st.session_state['adjust_pending'] = False

            with st.container(border=True):
                col1, col2 = st.columns(2)

                with col1:
                    write_csv_summary()
                    st.write('**QQ CSV Detected**')
                    st.caption("You may adjust the DateTime values "
                                "by:"
                                "\n1. Select a new ***Start Date***, ***Start Time***."
                                "\n2. Press '***Adjust DateTime***' to apply the"
                                "DateTime adjustment"
                                "\n\nThe DateTime will be applied and ready when"
                                "Selecting '***Download QQ CSV***'")

                with col2:
                    start_datetime = st.session_state['start_datetime']
                    
                    with st.form(key='info_form'):
                        
                        st.write(f'Start DateTime:  :green[{start_datetime}]')

                        d = st.date_input("Start Date", value=start_datetime.date(), key='start_date')
                        t = st.time_input("Start Time", value=start_datetime.time(), key='start_time')
                        submit = st.form_submit_button('Adjust DateTime', type='secondary')

            # If QQ DateTime Adjustment Submitted
            if submit:
                st.session_state['adjust_pending'] = True
                st.rerun()

        # Draw EXO summary 
        elif st.session_state.get('CSV Type', "") == "exo":
            csv_import.convert_to_qq()
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    write_csv_summary()

                with col2:

                    st.caption("EXO CSV File Detected. Data  automatically being converted to QQ format and is ready for download.")
                    st.caption("Preview of converted Data below.")

        # Prepare Download
        csv_out = csv_import.to_csv()
        st.download_button(
            label="Download QQ CSV",
            data=csv_out,
            file_name="qq.csv",
            mime="text/csv",
            icon=':material/download:',
            type='primary'
        )

        # Display Previews
        if csv_import.csv_type == "qq":
            st.subheader("Previews:")
            tab_data_preview, tab_chart_preview = st.tabs(["🗃 Data", "📈 Chart"])
       
            preview_df = csv_import.dataframe
            with tab_data_preview:
                preview_lines_count = min(10, preview_df.shape[0])
                st.write(f'Previewing {preview_lines_count} of {preview_df.shape[0]:,d} rows')
                st.dataframe(preview_df[0:preview_lines_count]) # Up to 10 rows in preview

            with tab_chart_preview:
                st.line_chart(preview_df,
                              x='DateTime',
                              y=['EC(uS/cm)', 'Temp(oC)', 'EC.T(uS/cm)'],
                              color=['#FF0000', '#00FF00', '#0000FF'])

    st.divider()
    st.markdown(
        f'<div style="text-align: right;">{TITLE} by Christopher Lafferty</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
