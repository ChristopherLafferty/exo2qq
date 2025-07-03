from io import StringIO
import pandas as pd
import datetime
import codecs
import streamlit as st
from typing import List

import os
def log(s):
    """Utility function to log to console instead of on HTML document"""
    os.write(1, f"{s}\n".encode())

QQ_DEFAULT_HEADERS = [
    'QQSN,Ch0SN,Ch1SN,Ch2SN,Ch0Cal,Ch1Cal,Ch2Cal,FWVers,VolInj(ml),CalVol(l),[NaCl](g/l),StnName,StnID,PrjName,PrjID',
    'QM0.00,TM0.000,TM0.000,TM0.000,0.0,0.0,0.0,QQF0.0.00,0.000,0.000,0.000,00000000 - NA,0,NONE,0',
    '',
    '']

class CSVImport:

    def __init__(self, upload_file=None):
        self.file: StringIO = None
        self.encoding: str = None
        self.header: str = None
        self.csv_type: str = None
        self.dataframe: pd.DataFrame = None
        self.dataframes: List[pd.DataFrame] = []

        if upload_file:
            self.file = self._import_file(upload_file)
            if self.file:
                self._separate_data()

    def __repr__(self):
        # To be able to verify basics when viewing object in session data
        csv_type = getattr(self, 'csv_type', 'Unknown CSV Type')
        encoding = getattr(self, 'encoding', 'Unknown Encoding')         
        df = getattr(self, 'dataframe', None)
        if df is None:
            df_info = 'No Dataframe'
        else:
            x, y = df.shape
            df_info = f'{x} rows x {y} columns'
        return f'{csv_type}, {encoding}, {df_info}'    

    def _import_file (self, upload_file): 
        """Populate importer with data from the file"""
        decoded = None
        bom = self._read_bom(upload_file)        
        if bom:
            decoded = StringIO(upload_file.getvalue().decode(bom))
            self.encoding = bom
        else:            
            try:
                # If no BOM try as UTF-8, assume UTF-16 if failed
                decoded = StringIO(upload_file.getvalue().decode('utf-8'))
                self.encoding = 'utf-8'
            except UnicodeDecodeError:
                try:
                    decoded = StringIO(upload_file.getvalue().decode('utf-16'))
                    self.encoding = 'utf-16'
                except Exception as e:
                    st.write(f'Error: :red[Unable to read file]\n{e}\n{type(e)}')
        return decoded


    def convert_to_qq(self):
        """Remap compatible EXO Data to QQ data"""
        try:
            if self.csv_type == "exo":

                # Remap Exo to QQ Names            
                self.dataframe.rename(columns={'Cond µS/cm':'EC(uS/cm)',
                                'Temp °C':'Temp(oC)',
                                'SpCond µS/cm': 'EC.T(uS/cm)'},
                        inplace=True)
                
                # Combine Date and Time, and change format to: %Y-%m-%d %H:%M:%S
                self.dataframe['DateTime'] = (pd.to_datetime(self.dataframe['Date (MM/DD/YYYY)'] + ' ' + self.dataframe['Time (HH:mm:ss)'])).dt.strftime('%Y-%m-%d %H:%M:%S')

                # Create new df using just the fields needed for QQ
                df_out = self.dataframe[['DateTime', 'EC(uS/cm)', 'Temp(oC)','EC.T(uS/cm)']]        

                # Add Placeholder Columns for QQ
                cols = ['Mass(kg)', 'CF.T(mg/L)/(uS/cm)', 'BGEC.T(uS/cm)',
                        'Q(cms/cfs)', 'Grade', 'S_BGEC.T(uS/cm)', '2sUnc_Q(%)',
                        'preBG_index', 'dt(s)', 'Area(s*uS/cm)', '3rd_U/S',
                        'QUnit', 'QComp', 'VBatt(V)' ]
                df_out.loc[:, cols] = ''
                
                # Update object
                self.dataframe = df_out
                self.csv_type = "qq"
                self.header = '\r\n'.join(QQ_DEFAULT_HEADERS)
                self.encoding = 'utf-8'
        except Exception as e:
            st.write("Error: A problem was encountered in conversion. EXO was not in expected format.", e)

    def to_csv(self):
        """Return dataframe as utf-8 encoded QQ CSV with File Header"""
        return self.header + self.dataframe.to_csv(index=False, lineterminator='\r\n', encoding='utf-8')

    def _read_bom(self, file):
        """Internal helper method to set encoding type of file"""
        byte_order_marker = file.read(4)
        decoder = None
        if byte_order_marker.startswith(codecs.BOM_UTF8):
            decoder = 'utf-8'
        elif byte_order_marker.startswith(codecs.BOM_UTF16_BE):
            decoder = 'utf-16-be'
        elif byte_order_marker.startswith(codecs.BOM_UTF16_LE):
            decoder = 'utf-16-le'
        else:
            decoder = None        
        file.seek(0)
        return decoder

    def _separate_data(self):
        """Separate self.file's file headers from actual CSV Data"""
        
        f = self.file
        headers_lines = []
        f.seek(0)
        file_pos = 0
        csv_found = False

        for i, line in enumerate(f):

            match line.split(sep=','):
                # EXO Data Headers
                case ['Date (MM/DD/YYYY)', *headers_remaining]:
                    # log(f'Headers remaining: {headers_remaining}')
                    self.csv_type = "exo"
                    csv_found = True
                    break

                # QQ Data Headers
                case ['DateTime', *_ ]:
                    self.csv_type = "qq"
                    csv_found = True
                    break

                # Capture EXO Serial Numbers... Not Needed?
                # case [_, _, _, 'SENSOR SERIAL NUMBER:', *serials]:
                #     headers_lines.append(line)
                #     file_pos = f.tell()

                case _:
                    headers_lines.append(line)
                    file_pos = f.tell()
            if i > 20:
                # No file found by 20
                self.csv_type = None
                break

        if csv_found:
            f.seek(file_pos)
            df = pd.read_csv(f, encoding=self.encoding)

            # EXO Files can contain data for multiple devices in same file
            if self.csv_type == "exo":

                # Start with all headers
                data_headers = df.columns.tolist()

                additional_device_count = 0
                duplicate_headers = set()
                base_headers = []

                # separate standard device data cols from additional device cols
                for col in data_headers:

                    # Determine duplicate columns by pattern ColumnName.[digit] from pandas suffixing duplicate column names
                    col_check = col.split('.')
                    if col_check[-1].isdigit():
                        duplicate_headers.add(col_check[0])
                        additional_device_count = max(int(col_check[-1]), additional_device_count)
                    # not a duplicate column
                    else:
                        base_headers.append(col)

                dfs = []
                dfs.append( df[base_headers] )

                for i in range(1, additional_device_count+1):
                    device_cols = [h if h not in duplicate_headers
                                   else ''.join((h, '.', str(i)))
                                   for h in base_headers ]
                    additional_df = df[device_cols]
                    additional_df.columns = device_cols
                    dfs.append(additional_df)

                for d in dfs:
                    log(f'{d.shape=}')
                    log(f'{d.head}')
                    # log(f'{1}')



            # Old Single Out DF, which will be refactored out eventually
            self.dataframe = df
            
            if headers_lines:
                self.header = ''.join(headers_lines)




