from io import StringIO
import pandas as pd
import datetime
import codecs
from enum import StrEnum
import streamlit as st

class CSVImport:
    QQ_DEFAULT_HEADERS = [
        'QQSN,Ch0SN,Ch1SN,Ch2SN,Ch0Cal,Ch1Cal,Ch2Cal,FWVers,VolInj(ml),CalVol(l),[NaCl](g/l),StnName,StnID,PrjName,PrjID',
        'QM0.00,TM0.000,TM0.000,TM0.000,0.0,0.0,0.0,QQF0.0.00,0.000,0.000,0.000,00000000 - NA,0,NONE,0',
        '',
        '']

    class FIRST_COL(StrEnum):
        EXO = 'Date (MM/DD/YYYY)'
        QQ = 'DateTime'

    class CSV_TYPE(StrEnum):
        QQ = "QQ"
        EXO = "EXO"
        UNKNOWN = "Unknown"

    def __init__(self, upload_file=None):
        _file: StringIO = None
        _encoding: str = None
        _csv_type: CSVImport.CSV_TYPE = None
        _header: str = None
        dataframe: pd.DataFrame = None

        self.file = upload_file
        if self.file:
            self._separate_data()
            # if self._csv_type == CSVImport.CSV_TYPE.EXO:
            #     self.to_qq()


    def __repr__(self):
        csv_type = getattr(self, '_csv_type', 'Unknown CSV Type')
        encoding = getattr(self, '_encoding', 'Unknown Encoding')         
        df = getattr(self, 'dataframe', None)
        if df is None:
            df_info = 'No Dataframe'
        else:
            x, y = df.shape
            df_info = f'{x} rows x {y} columns'
        return f'{csv_type}, {encoding}, {df_info}'

    @property
    def csv_type(self) -> CSV_TYPE:
        return self._csv_type
    
    @csv_type.setter
    def csv_type(self, csv_type: CSV_TYPE):
        self._csv_type = csv_type

    @property
    def header(self) -> str:
        if self._header:
            return self._header

    @header.setter
    def header(self, header) -> str:
        self._header = header

    @property
    def encoding(self) -> str:
        return self._encoding
    
    @encoding.setter
    def encoding(self, encoding:str):
        self._encoding = encoding
    
    @property
    def file(self) -> StringIO:
        return self._file
    
    @file.setter
    def file(self, upload_file):
        decoded = None
        bom = self._read_bom(upload_file)        
        if bom:
            decoded = StringIO(upload_file.getvalue().decode(bom))
            self._encoding = bom
        else:            
            try:
                # If no BOM try as UTF-8, assume UTF-16 if failed
                decoded = StringIO(upload_file.getvalue().decode('utf-8'))
                self._encoding = 'utf-8'
            except UnicodeDecodeError:
                try:
                    decoded = StringIO(upload_file.getvalue().decode('utf-16'))
                    self._encoding = 'utf-16'
                except Exception as e:
                    st.write(f'Error: :red[Unable to read file]\n{e}\n{type(e)}')
        self._file = decoded


    def fix_qq_datetime(self):
        if self.csv_type == CSVImport.CSV_TYPE.QQ:
            pass


    def to_qq(self):
        try:
            if self.csv_type == CSVImport.CSV_TYPE.EXO:

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
                self.csv_type = CSVImport.CSV_TYPE.QQ
                self.header = CSVImport.QQ_DEFAULT_HEADERS
                self.encoding = 'utf-8'
        except Exception as e:
            st.write("Error: A problem was encountered in conversion. EXO was not in expected format.", e)




    # Helper to try to get encoding type
    def _read_bom(self, file):
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
        f = self.file
        headers_lines = []
        f.seek(0)
        file_pos = 0
        csv_found = False

        for i, line in enumerate(f):
            match line.split(sep=',')[0]:
                case CSVImport.FIRST_COL.EXO:
                    self._csv_type = CSVImport.CSV_TYPE.EXO
                    csv_found = True
                    break

                case CSVImport.FIRST_COL.QQ:
                    self._csv_type = CSVImport.CSV_TYPE.QQ
                    csv_found = True
                    break
                case _:
                    headers_lines.append(line.strip())
                    file_pos = f.tell()
            if i > 20:
                # No file found by 20
                self.csv_type = CSVImport.CSV_TYPE.UNKNOWN
                break

        if csv_found:
            f.seek(file_pos)
            self.dataframe = pd.read_csv(f, encoding=self.encoding)

            if headers_lines:
                self._header = '\n'.join(headers_lines)




