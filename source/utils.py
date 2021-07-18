import os
import pandas as pd


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


class FileOperations:
    @staticmethod
    def file_exists(file_path):
        pass


class DataframeOperations:
    @staticmethod
    def save_csv(dataframe, file_path):
        dataframe.to_csv(file_path, sep=';', encoding='utf-8', index=False)

    @staticmethod
    def read_csv(file_path):
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        return df
