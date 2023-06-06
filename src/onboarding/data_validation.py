
import argparse
import os
import pandas as pd
from ydata_profiling import ProfileReport
from difflib import get_close_matches
# setup the logging
import logging
logging.basicConfig(level=logging.INFO)
# save the logs to a file in the logging directory
logger = logging.getLogger(__name__)

# Function to match the simillar or nearlly simillar keys in the dataset and the dictionary and log them
def validate_match_keys(dataframe, dataframe_name, data_key_map_list, option, Data_key_map):
    """
    This function matches the simillar or nearly simillar keys in the dataset and the dictionary and log them
    """
    for i in range(len(dataframe.columns)):
        if dataframe.columns[i].lower() not in data_key_map_list:
            if option in [0, 1]:
                logger.info(f"{dataframe_name}: Columns which are not present - {dataframe.columns[i]}")
            if option in [0, 1, 2]:
                logger.info(f"{dataframe_name}: Close matches - {get_close_matches(str(dataframe.columns[i]), str(data_key_map_list), n=1, cutoff=0.7)}")
        elif option in [0]:
                logger.info(f"{dataframe_name}: Columns which are present - {dataframe.columns[i]}")

    return None

# Function to generate a pandas-profiling report for the initial EDA
def generateReport(dataframe, name):
    profile= ProfileReport(dataframe, explorative=True)
    profile.to_file(f'{name}_report.html')

def main():
    # write the logs to a file
    file_handler = logging.FileHandler('./logs/data_validation.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('--newdata', type=str, help='File name of the new data')
    parser.add_argument('--keymap', type=str, help='File name of the key map')
    parser.add_argument('--loglevel', type=int, help='Logging level (0 - log everything, 1 - log close mathches and not present, 2 - log only close matches, 3 - log nothing))', default=0)
    args = parser.parse_args()

    # Access the file paths using the argument names
    data_filename = args.newdata
    keymap_filename = args.keymap
    loglevel = args.loglevel

    # Get the current working directory
    current_directory = os.getcwd()
    
    # Get the path to the file
    # data_path = os.path.join(current_directory, f'data/raw/{data_filename}')
    data_path = os.path.join(current_directory, f'{data_filename}')
    Data_key_map = os.path.join(current_directory, f'{keymap_filename}')

    # Read the data
    Data_finalized = pd.read_excel(data_path)
    logger.info(f"{data_filename} read successfully")
    Data_key_map = pd.read_excel(Data_key_map)
    logger.info(f"{keymap_filename} read successfully")

    # Option for the user to change the file name by displaying the current file name and the example format
    print(f"Current file name: {data_filename}")
    print("Example format: [study_name]-[data_type]-[suffix].csv")
    # Read the new file name from the user or press enter to continue with the same file name
    data_filenewname = input("Enter the new name for the file: ")
    if data_filenewname == "":
        data_filenewname = data_filename
        logger.info(f"File name of {data_filename} is not changed")
    else:
        logger.info(f"New file name of {data_filename} is : {data_filenewname}")

    data_key_map_list = []
    data_key_map_dict = {}
    for i in range(len(Data_key_map)):
        data_key_map_list.append(Data_key_map['Column Name'][i].lower())
        if type(Data_key_map['Alternate Name'][i]) == str:
            if ',' in Data_key_map['Alternate Name'][i]:
                # print(Data_key_map['Alternate Name'][i].lower().split(','))
                data_key_map_dict[Data_key_map['Column Name'][i]] = Data_key_map['Alternate Name'][i].lower().split(',')
                data_key_map_list.extend(Data_key_map['Alternate Name'][i].lower().split(','))
            else:
                data_key_map_list.append(Data_key_map['Alternate Name'][i].lower())
                data_key_map_dict[Data_key_map['Column Name'][i]] = Data_key_map['Alternate Name'][i].lower()

    # Standardise column feature which will standardise the column names from alternate names to the column name
    data_columns_list = list(Data_finalized.columns)

    for i in range(len(data_columns_list)):
        if data_columns_list[i].lower() in data_key_map_dict.values():
            # Get the key for the value in the dictionary corresponding to the column name
            replace_key = list(data_key_map_dict.keys())[list(data_key_map_dict.values()).index(data_columns_list[i].lower())]
            Data_finalized.rename(columns={f"{Data_finalized.columns[i]}": f"{replace_key}"}, inplace=True)
            logger.info(f"{Data_finalized.columns[i]} renamed to {replace_key}")
    
    # Save the file with the new name and the standardized column names in the onboarding folder
    Data_finalized.to_csv(f"../../data/onboarded/{data_filenewname}", index=False)
    logger.info(f"data/onboarded/{data_filenewname} saved successfully")

    validate_match_keys(Data_finalized, "Data_finalized", data_key_map_list, loglevel, Data_key_map)

    #TODO: Add the code to validate the data types

if __name__ == "__main__":
    main()
