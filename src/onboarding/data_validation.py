
import argparse
import os
import pandas as pd
from ydata_profiling import ProfileReport
from difflib import get_close_matches


log_dir="./logs"
default_log_name="data_validation.log"
onboarded_dir="./data/onboarded"

# setup the logging
import logging
logging.basicConfig(level=logging.INFO)
# save the logs to a file in the logging directory
logger = logging.getLogger(__name__)

def remove_extension(file_name):
    base_name, extension = os.path.splitext(file_name)
    if extension.lower() in ['.csv', '.xlsx']:
        return base_name
    else:
        return file_name
    
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
    file_handler = logging.FileHandler(f'{log_dir}/{default_log_name}')
    
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
    if "data/raw/" not in data_filename:
        data_filename = f"data/raw/{data_filename}"
    if "src/onboarding/" not in keymap_filename:
        keymap_filename = f"src/onboarding/{keymap_filename}"
    data_path = os.path.join(current_directory, f'{data_filename}')
    Data_key_map = os.path.join(current_directory, f'{keymap_filename}')

    # Read the multiple sheets if present in the excel file
    worksheet_dict = {}
    onboard_data = pd.ExcelFile(data_path)
    onboard_data_sheets = onboard_data.sheet_names

    # Excel Sheet selection and log those sheets which are not present in the data
    if len(onboard_data_sheets) > 1:
        for sheet in onboard_data_sheets:
            worksheet_dict[sheet] = pd.read_excel(data_path, sheet_name=sheet).shape

        result_dict = {}    
        # Give the list of sheets in the onboard_data_sheets find the difference between the two sheets and update the worksheet_dict
        for sheet1, value1 in worksheet_dict.items():
            for sheet2, value2 in worksheet_dict.items():
                if sheet1 != sheet2:
                    if value1 != value2:
                        result_dict[sheet1 + '-' + sheet2] = 'different'
                    else:
                        result_dict[sheet1 + '-' + sheet2] = 'same'

        worksheet_dict.update(result_dict)

        # Read the sheet name from the user
        logger.info(f" Worksheet Dictionary: {worksheet_dict}")
        print(f" Sheets present in the file {data_filename}:{onboard_data_sheets}")
        sheet_name = input(f"Enter the sheet name which you want to select from the above list:")
        # Read the data from the sheet which is not a duplicate
        Data_finalized = pd.read_excel(data_path, sheet_name=sheet_name)
        logger.info(f"{data_filename} read successfully with the sheet name {sheet_name}")
    else:
        # Read the data
        Data_finalized = pd.read_excel(data_path)
        logger.info(f"{data_filename} read successfully")

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
        data_filenewname = remove_extension(data_filenewname)
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
    Data_finalized.to_csv(f"{onboarded_dir}/{data_filenewname}.csv", index=False)
    logger.info(f"{onboarded_dir}/{data_filenewname} saved successfully")

    validate_match_keys(Data_finalized, "Data_finalized", data_key_map_list, loglevel, Data_key_map)

    #Validate the data types
    data_types_dict = dict(zip(Data_key_map['Column Name'], Data_key_map['Expected_Data_type']))
    for i in range (len(Data_key_map)):
        if type(Data_key_map['Alternate Name'][i]) == str:
            if ',' in Data_key_map['Alternate Name'][i]:
                for j in range(len(Data_key_map['Alternate Name'][i].split(','))):
                    data_types_dict.update(dict(zip([f"{Data_key_map['Alternate Name'][i].split(',')[j]}"], [Data_key_map['Expected_Data_type'][i]])))
            else:
                data_types_dict.update(dict(zip([f"{Data_key_map['Alternate Name'][i]}"], [f"{Data_key_map['Expected_Data_type'][i]}"])))

    logger.info(f"Dataset schema checks")
    for col, dtype in data_types_dict.items():
        try:
            if Data_finalized[col].dtype != dtype:
                logger.info(f"{col} has data type {Data_finalized[col].dtype} but should be {dtype}")
        except KeyError:
            pass

    for col in Data_finalized.columns:
        if col not in data_types_dict.keys():
            logger.info(f"{col} is not present in the dataset")   
    
    # Close logger and rename log file
    file_handler.close()
    new_log_filename = f'data_validation-{data_filenewname}.log'
    new_log_file_path = os.path.join(log_dir, new_log_filename)
    os.rename(f"{log_dir}/{default_log_name}", new_log_file_path)

if __name__ == "__main__":
    main()
