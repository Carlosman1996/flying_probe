from os import path
from pathlib import Path
import pandas as pd
import json
import jsonschema
from jsonschema import validate


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


ROOT_PATH = str(Path(path.dirname(path.realpath(__file__))).parent)


class FileOperations:
    @staticmethod
    def check_file_exists(file_path):
        if path.isfile(file_path):
            return True
        else:
            raise Exception("File does not exist.")

    def read_text_file(self, file_path):
        self.check_file_exists(file_path)
        with open(file_path, 'r') as file_obj:
            file_content = file_obj.read()
        return file_content

    def write_text_file(self, file_path, string):
        self.check_file_exists(file_path)
        with open(file_path, 'w') as file_obj:
            file_content = file_obj.write(string)
        return file_content

    def append_text_file(self, file_path, string):
        self.check_file_exists(file_path)
        with open(file_path, 'a') as file_obj:
            file_content = file_obj.write(string)
        return file_content


class JSONFileOperations:
    @staticmethod
    def read_file(file_path):
        FileOperations.check_file_exists(file_path)
        with open(file_path, 'r') as json_obj:
            return json.loads(json_obj.read())

    @staticmethod
    def validate_data_schema_dict(json_data, data_schema):
        try:
            validate(instance=json_data, schema=data_schema)
        except jsonschema.exceptions.ValidationError:
            return False
        return True

    @staticmethod
    def validate_data_schema_dict_of_dicts(json_data, data_schema):
        if type(json_data) is dict:
            sub_json_data = json_data.values()
            if len(sub_json_data) == 0:
                return False
            else:
                for sub_data in sub_json_data:
                    if not JSONFileOperations.validate_data_schema_dict(sub_data, data_schema):
                        return False
                return True
        else:
            return False


class DataframeOperations:
    @staticmethod
    def save_csv(dataframe, file_path):
        dataframe.to_csv(file_path, sep=',', encoding='utf-8', index=False)

    @staticmethod
    def read_csv(file_path):
        FileOperations.check_file_exists(file_path)
        df = pd.read_csv(file_path, sep=',', encoding='utf-8')
        return df
