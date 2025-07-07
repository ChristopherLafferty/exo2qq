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

def display_preview(df):
    preview_lines_count = min(10, df.shape[0])
    st.write(f'Displaying {preview_lines_count} of {df.shape[0]:,d} rows')
    st.dataframe(df[0:preview_lines_count]) # Up to 10 rows in preview
    st.line_chart(df, x='DateTime', y=['EC(uS/cm)', 'Temp(oC)', 'EC.T(uS/cm)'],
                color=['#FF0000', '#00FF00', '#0000FF'])    


def main():
    # st.set_page_config(layout="wide")
    st.title(TITLE)
    st.write("")
    
    st.file_uploader(label='Select a QQ or EXO CSV File:',
                    on_change=file_changed,
                    key='upload_file',
                    type="csv")

    if 'csv_import' in st.session_state:
        csv_import: CSVImport = st.session_state['csv_import']

        st.write(f'{st.session_state.get('CSV Type', "")}, {csv_import.csv_type}')

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
                                "\n\nThe DateTime will be applied and ready when "
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
            
            if not csv_import.converted:
                csv_import.convert_to_qq()

            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    write_csv_summary()

                with col2:
                    st.caption("EXO CSV File Detected. Data  automatically being converted to QQ format and prepared for download.")
                    st.caption("Preview of converted Data below.")

        # Prepare Download(s)
        download_cols = st.columns(len(csv_import.dataframes))
        for i, export_df in enumerate(csv_import.dataframes):
            export_df = csv_import.dataframes[i]
            csv_out = csv_import.to_csv(export_df)

            if csv_import.csv_type == 'qq':
                label_text = 'Download QQ CSV'
                f_name = 'qq.csv'
            else:
                label_text = f'Download {csv_import.serials[i]} CSV'
                f_name = f'{csv_import.serials[i]}_to_qq.csv'

            with download_cols[i]:
                st.download_button(
                    label=label_text,
                    data=csv_out,
                    file_name=f_name,
                    mime="text/csv",
                    icon=':material/download:',
                    type='primary'
                )

        # Display Previews
        if csv_import.dataframe is not None:
            st.subheader("Previews:")

            # If Multiple Device Display
            if len(csv_import.dataframes) > 1:
                tabs = st.tabs([f'🗃 {s}:'for s in csv_import.serials])

                for i, tab in enumerate(tabs):
                    df = csv_import.dataframes[i]
                    with tab:
                        display_preview(df)
            else:
                display_preview(csv_import.dataframes[0])

    st.divider()
    st.markdown(
        f'<div style="text-align: right;">{TITLE} by Christopher Lafferty</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
