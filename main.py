import streamlit as st
import pandas as pd
from io import StringIO
import altair as alt

QQ_HEADERS = ['QQSN,Ch0SN,Ch1SN,Ch2SN,Ch0Cal,Ch1Cal,Ch2Cal,FWVers,VolInj(ml),CalVol(l),[NaCl](g/l),StnName,StnID,PrjName,PrjID',
              'QM0.00,TM0.000,TM0.000,TM0.000,0.0,0.0,0.0,QQF0.0.00,0.000,0.000,0.000,00000000 - NA,0,NONE,0',
              '',
              '']

def find_header(file, marker):
    #Skip header data and find header row of main data
    for i, line in enumerate(file):
        if line.startswith(marker):
            return i
    return 0

def exo_to_qq(df):
    try:
        # Remap Exo to QQ Names
        df.rename(columns={'Cond µS/cm':'EC(uS/cm)',
                        'Temp °C':'Temp(oC)',
                        'SpCond µS/cm': 'EC.T(uS/cm)'},
                inplace=True)
        df['DateTime'] = df['Date (MM/DD/YYYY)'] + ' ' + df['Time (HH:mm:ss)'] 

        # Create new df using just the fields needed for QQ
        df_out = df[['DateTime', 'EC(uS/cm)', 'Temp(oC)','EC.T(uS/cm)']]

        # Add Placeholder Columns for QQ
        for col in ['Mass(kg)', 'CF.T(mg/L)/(uS/cm)', 'BGEC.T(uS/cm)',
                    'Q(cms/cfs)', 'Grade', 'S_BGEC.T(uS/cm)', '2sUnc_Q(%)',
                    'preBG_index', 'dt(s)', 'Area(s*uS/cm)', '3rd_U/S',
                    'QUnit', 'QComp', 'VBatt(V)' ]:
            df_out[col] = ''

        return df_out
    
    except:
        st.write("Error: A problem was encountered in conversion. EXO was not in expected format.")
        return None


def read_exo(file):
    try:
        decoded_file = StringIO(file.getvalue().decode('utf-16'))       
        header_row = find_header(decoded_file, 'Date')
        decoded_file.seek(0)
        df = pd.read_csv(decoded_file, skiprows=header_row, encoding='utf-16')
        return df
    except:
        st.write(":red[Error]: There was a problem reading EXO CSV file")
        return None

def display_qq_preview(df):
    row_count, col_count = df.shape
    st.write(f'Preview of {row_count:,d} rows of data: ')
    df[0:min(10, row_count)] # Preview up to first 10
    st.line_chart(df,
                    x= 'DateTime',
                    y=['EC(uS/cm)', 'Temp(oC)', 'EC.T(uS/cm)' ],
                    color=['#FF0000', '#00FF00', '#0000FF']
                    )

def main():
    st.title("EXO CSV to QQ CSV Converter")
    uploaded_file = st.file_uploader('Select your EXO CSV File:', type="csv")
    st.divider()
    
    if uploaded_file:        
        exo_df = read_exo(uploaded_file)

        if exo_df is not None:
            
            qq_df = exo_to_qq(exo_df)

            if qq_df is not None:                
                csv_out = '\r\n'.join(QQ_HEADERS) + qq_df.to_csv(index=False, lineterminator = '\r\n', encoding='utf-8')
                st.download_button(
                    label="Download QQ CSV",
                    data=csv_out,
                    file_name="qq.csv",
                    mime="text/csv",
                    icon=':material/download:',
                    type='primary'
                )
                st.divider()
                st.subheader("Previews:")
                display_qq_preview(qq_df)            

    st.divider()
    st.markdown(
        '<div style="text-align: right;">EXO2QQ by Christopher Lafferty</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

