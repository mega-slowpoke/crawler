from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import os
import shutil
import config

def reload_page_and_select_crop_type(driver, crop_type, crop_type_map):
        # Navigate to a website
        driver.get("https://biruni.tuik.gov.tr/medas/?kn=92&locale=en")

        # Perform actions on the page (e.g., clicking buttons, filling forms)
        # For example, let's search for "example" on the website
        crop_type_element = driver.find_element(By.XPATH, crop_type_map[crop_type])
        crop_type_element.click()
        
        # ok_button is disabled in the first place, we have to wait until it is available
        ok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[1]/div/div[3]/div[2]/div[1]/div/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr/td[3]/div/div[2]/table/tbody/tr/td/table/tbody/tr[3]/td/div/table/tbody/tr/td/table/tbody/tr/td[5]/div/button[1]"))
        )

        if ok_button.is_enabled():
            ok_button.click()
        else:
            print("button is not available!")
        
        time.sleep(0.5)


def save_missing_crop_data( level, content):
    file = open("missing_data.txt", "a", encoding="utf-8")
    file.write(f"{level},{content}\n")
    file.close()


def rename_and_move_file(level, crop_type):
    """This function renames and moves the downloaded file to the specified folder"""
    src_dir = os.path.join("C:","Users", "wucha", "Downloads")
    for file in os.listdir(src_dir):
        if file.endswith(".xls"):
            df = pd.read_excel(os.path.join(src_dir,file), header= None)
            text = df.iloc[4,1].split(" and ")

            data_type = text[0].replace('\xa0', ' ')

            crop_name_text = text[1]
            start_idx = crop_name_text.find('(') + 1
            end_idx = crop_name_text.rfind(')')

            crop_name = crop_name_text[start_idx:end_idx].replace("/","_")
            
            print(f"rename file, orginal text {text[1]}, get crop name: {crop_name}")

            file_name = f"{data_type}_{crop_name}.xls"
            
            target_dir = os.path.join("raw", level, crop_type, crop_name)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            if os.path.exists(os.path.join(target_dir, file_name)):
                print(f"{text} already exists")

            shutil.move(os.path.join(src_dir, file), os.path.join(target_dir, file_name))


def merge(level, crop_type):
    path = os.path.join(os.getcwd(), "raw", level, crop_type)

    for item in os.listdir(path):
        merge_all_files(os.path.join(path,item), crop_type, level)

def merge_all_files(target_dir, crop_type, level):
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir,item)

        if os.path.isfile(item_path):
            generate_final_file(target_dir, crop_type, level)
            return

        elif os.path.isdir(item_path):
            merge_all_files(item_path, crop_type, level)


def custom_sort(file_name, sequence):
    for index, item in enumerate(sequence):
        if item in file_name:
            return index
    return len(sequence)


def generate_final_file(target_dir,crop_type ,level):

    if crop_type == "fruits":
        generate_final_file_fruits(target_dir, crop_type, level)
        return 


    file_names = os.listdir(target_dir)

    # 定义排序顺序
    sequence_order = ["Sown Area", "Harvest Area", "Production", "Yield"]

    # 按照自定义顺序对文件进行排序
    sorted_files = sorted(file_names, key=lambda x: custom_sort(x, sequence_order))
    
    column_header =['Region Code', 'State',  'Year', 'Cropnm', 'Sown Area(Decare)', 'Harvest Area(Decare)', 'Prodution(Tonne)', 'Yield(Kilogramme/Decare)']

    res = None
    
    for i in range(len(sorted_files)):
        file = sorted_files[i]
        # 先读取sown area的file
        if i == 0:
            lines = []
            crop_name = file.split("_")[1].split(".")[0]

            print(os.path.join(target_dir, file))    

            df = pd.read_excel(os.path.join(target_dir, file), header = None)

            # add values to the final result one by one
            col_num = df.shape[1]
            row_num = df.shape[0]

            # first round, we need sown_area
            for col in range(3, col_num):
                for row in range(4, row_num):
                    new_line = [("", df.iloc[1, col], df.iloc[row, 2], crop_name, df.iloc[row,col], "", "", "")]
                    lines.append(pd.DataFrame(new_line, columns=column_header))
            
            res = pd.concat(lines, axis = 0)

        else:
            df = pd.read_excel(os.path.join(target_dir, file), header = None)

            # add values to the final result one by one
            col_num = df.shape[1]
            row_num = df.shape[0]

            # first round, we need sown_area
            for col in range(3, col_num):
                for row in range(4, row_num):
                    if i == 1:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Prodution(Tonne)"] = df.iloc[row,col]
                    elif i == 2:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Yield(Kilogramme/Decare)"] = df.iloc[row,col]
                    elif i == 3:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Harvest Area(Decare)"] = df.iloc[row,col]
    output_path = f".\\processed\\{level}\\{crop_type}"
    if not os.path.exists(output_path):
        os.makedirs(output_path)            

    res.to_csv(f"{output_path}\\{crop_name}.csv", index = False, encoding="utf-8-sig")

field_xpath_map = config.field_xpath_map

def generate_final_file_fruits(target_dir, crop_type, level):
    file_names = os.listdir(target_dir)

    # 定义排序顺序
    sequence_order = ["Area Of Compact", "Number Of Bearing", "Number Of Non Bearing", 'Production', "Yield"]

    # 按照自定义顺序对文件进行排序
    sorted_files = sorted(file_names, key=lambda x: custom_sort(x, sequence_order))
    
    column_header =['Region Code', 'State',  'Year', 'Cropnm', 'Area of Compact(Decare)', "Number of Bearing Trees(Number)", "Number of Non Bearing Trees(Number)", 'Prodution(Tonne)', 'Yield(Kilogramme/Decare)']

    res = None
    
    for i in range(len(sorted_files)):
        file = sorted_files[i]
        # 先读取sown area的file
        if i == 0:
            lines = []
            crop_name = file.split("_")[1].split(".")[0]

            print(os.path.join(target_dir, file))    

            df = pd.read_excel(os.path.join(target_dir, file), header = None)

            # add values to the final result one by one
            col_num = df.shape[1]
            row_num = df.shape[0]

            # first round, we need sown_area
            for col in range(3, col_num):
                for row in range(4, row_num):
                    new_line = [("", df.iloc[1, col], df.iloc[row, 2], crop_name, df.iloc[row,col],"", "", "", "")]
                    lines.append(pd.DataFrame(new_line, columns=column_header))
            
            res = pd.concat(lines, axis = 0)

        else:
            df = pd.read_excel(os.path.join(target_dir, file), header = None)

            # add values to the final result one by one
            col_num = df.shape[1]
            row_num = df.shape[0]

            # first round, we need sown_area
            for col in range(3, col_num):
                for row in range(4, row_num):
                    if i == 1:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Number of Bearing Trees(Number)"] = df.iloc[row,col]
                    elif i == 2:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Number of Non Bearing Trees(Number)"] = df.iloc[row,col]
                    elif i == 3:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Prodution(Tonne)"] = df.iloc[row,col]
                    elif i == 4:
                        res.loc[(res['Year'] == df.iloc[row,2]) & (res['State'] == df.iloc[1,col]), "Yield(Kilogramme/Decare)"] = df.iloc[row,col]
    
    output_path = f".\\processed\\{level}\\{crop_type}"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    res.to_csv(f"{output_path}\\{crop_name}.csv", index = False, encoding="utf-8-sig")

# rename_and_move_file("Turkey", "fruits")