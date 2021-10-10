import os
import glob
from pathlib import Path
import pandas as pd
import json
import jsonschema
from jsonschema import validate


__author__ = "Carlos Manuel Molina Sotoca"
__email__ = "cmmolinas01@gmail.com"


ROOT_PATH = str(Path(os.path.dirname(os.path.realpath(__file__))).parent)


class DirectoryOperations:
    @staticmethod
    def check_dir_exists(dir_path):
        if os.path.isdir(dir_path):
            return True
        else:
            raise Exception("Directory does not exist.")

    @staticmethod
    def create_dir(dir_path):
        try:
            os.mkdir(dir_path)
        except OSError:
            print(f"Creation of the directory {dir_path} failed")

    @staticmethod
    def search_last_dir(dir_path):
        DirectoryOperations.check_dir_exists(dir_path)
        return max(glob.glob(os.path.join(dir_path, '*/')), key=os.path.getmtime)


class FileOperations:
    @staticmethod
    def check_file_exists(file_path):
        if os.path.isfile(file_path):
            return True
        else:
            raise Exception("File does not exist.")

    @staticmethod
    def get_file_name(file_path):
        return os.path.basename(file_path)

    @staticmethod
    def read_file(file_path):
        FileOperations.check_file_exists(file_path)
        with open(file_path, 'r') as file_obj:
            file_content = file_obj.read()
        return file_content

    @staticmethod
    def read_file_lines(file_path):
        FileOperations.check_file_exists(file_path)
        with open(file_path, 'r') as file_obj:
            file_content = file_obj.readlines()
        return file_content

    @staticmethod
    def write_file(file_path, string):
        with open(file_path, 'w') as file_obj:
            file_obj.write(string)

    @staticmethod
    def append_text_file(file_path, string):
        FileOperations.check_file_exists(file_path)
        with open(file_path, 'a') as file_obj:
            file_obj.write(string)


class JSONFileOperations:
    @staticmethod
    def read_file(file_path):
        FileOperations.check_file_exists(file_path)
        with open(file_path, 'r') as json_obj:
            return json.loads(json_obj.read())

    @staticmethod
    def write_file(file_path, string):
        with open(file_path, 'w') as json_obj:
            json.dump(string, json_obj, indent=4)

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
    def save_csv(file_path, dataframe):
        dataframe.to_csv(file_path, sep=',', encoding='utf-8', index=False)

    @staticmethod
    def read_csv(file_path):
        FileOperations.check_file_exists(file_path)
        df = pd.read_csv(file_path, sep=',', encoding='utf-8')
        return df
