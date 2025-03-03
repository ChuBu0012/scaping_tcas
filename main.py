from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def setup_driver():
    chrome_options = Options()
    # Uncomment for headless mode: chrome_options.add_argument('--headless')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_universities(driver):
    url = "https://course.mytcas.com/universities"
    driver.get(url)
    time.sleep(3)
    universities = []
    elements = driver.find_elements(By.CSS_SELECTOR, 'a.brand')
    for idx, element in enumerate(elements, start=1):
        university_name = element.text.strip()
        sub_path = element.get_attribute('href')
        universities.append({"uni_id": idx, "university_name": university_name, "sub_path": sub_path})
    return universities

def get_faculties(driver, universities):
    faculties = []
    for uni in universities:
        driver.get(uni['sub_path'])
        time.sleep(3)
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/faculties/"]')
        for idx, element in enumerate(elements, start=1):
            faculty_name = element.text.strip()
            faculty_path = element.get_attribute('href')
            faculties.append({
                "fac_id": idx,
                "faculty_name": faculty_name,
                "uni_id": uni['uni_id'],
                "faculty_path": faculty_path
            })
    return faculties

def get_fields(driver, faculties):
    fields = []
    for faculty in faculties:
        driver.get(faculty['faculty_path'])
        time.sleep(3)
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/fields/"]')
        for idx, element in enumerate(elements, start=1):
            field_name = element.text.strip()
            field_path = element.get_attribute('href')
            fields.append({
                "field_id": idx,
                "field_name": field_name,
                "uni_id": faculty['uni_id'],
                "fac_id": faculty['fac_id'],
                "field_path": field_path
            })
    return fields

def get_programs(driver, fields):
    programs = []
    for field in fields:
        driver.get(field['field_path'])
        time.sleep(3)
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/programs/"]')
        for idx, element in enumerate(elements, start=1):
            try:
                program_name = element.find_element(By.CSS_SELECTOR, '.program').text.strip()
                programs.append({
                    "program_id": idx,
                    "program_name": program_name,
                    "uni_id": field['uni_id'],
                    "fac_id": field['fac_id'],
                    "field_id": field['field_id']
                })
            except Exception as e:
                print(f"Error extracting program data: {e}")
                continue
    return programs

def get_programs_from_last_10_fields(driver):
    # อ่านข้อมูล fields จากไฟล์
    with open('fields.json', 'r', encoding='utf-8') as f:
        fields = json.load(f)
    
    # เลือก 10 field สุดท้าย
    last_10_fields = fields[-10:]
    programs = []
    program_id_counter = 1  # ตัวนับ ID ของ program
    
    for field in fields:
        print(f"Fetching programs from field: {field['field_name']}")
        driver.get(field['field_path'])
        time.sleep(3)  # รอให้หน้าเว็บโหลด
        
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/programs/"]')
        for element in elements:
            try:
                program_name = element.find_element(By.CSS_SELECTOR, '.program').text.strip()
                program_type = element.find_element(By.CSS_SELECTOR, '.program-type').text.strip() if element.find_element(By.CSS_SELECTOR, '.program-type') else ""
                campus = element.find_element(By.CSS_SELECTOR, '.campus').text.strip() if element.find_element(By.CSS_SELECTOR, '.campus') else ""
                full_program_info = f"{program_name} {program_type} {campus}".strip()

                if full_program_info:  # เช็คว่ามีชื่อโปรแกรมไหม
                    programs.append({
                        "program_id": program_id_counter,
                        "program_name": full_program_info,
                        "uni_id": field['uni_id'],
                        "fac_id": field['fac_id'],
                        "field_id": field['field_id']
                    })
                    program_id_counter += 1
            except Exception as e:
                print(f"Error extracting program data: {e}")
                continue
        
        print(f"Found {len(programs)} programs so far...")
    
    return programs

if __name__ == "__main__":
    driver = setup_driver()
    try:
        # 1. ดึงข้อมูลมหาวิทยาลัย
        print("Fetching universities...")
        universities = get_universities(driver)
        with open('universities.json', 'w', encoding='utf-8') as f:
            json.dump(universities, f, ensure_ascii=False, indent=4)

        input("Press Enter to continue to faculties...")

        # 2. ดึงข้อมูลคณะ
        print("Fetching faculties...")
        faculties = get_faculties(driver, universities)
        with open('faculties.json', 'w', encoding='utf-8') as f:
            json.dump(faculties, f, ensure_ascii=False, indent=4)

        input("Press Enter to continue to fields...")

        # 3. ดึงข้อมูลสาขา
        print("Fetching fields...")
        fields = get_fields(driver, faculties)
        with open('fields.json', 'w', encoding='utf-8') as f:
            json.dump(fields, f, ensure_ascii=False, indent=4)

        input("Press Enter to continue to programs...")

        # 4. ดึงข้อมูลหลักสูตร
        print("Fetching programs...")
        programs = get_programs(driver, fields)
        with open('programs.json', 'w', encoding='utf-8') as f:
            json.dump(programs, f, ensure_ascii=False, indent=4)

        print("Scraping completed successfully!")
        print("Fetching programs from last 10 fields...")
        programs = get_programs_from_last_10_fields(driver)
        
        # บันทึกข้อมูลลงไฟล์
        with open('programs.json', 'w', encoding='utf-8') as f:
            json.dump(programs, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully saved {len(programs)} programs to programs_test.json")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()
# if __name__ == "__main__":
#     driver = setup_driver()
#     try:
#         # Load faculties from JSON
#         with open('faculties.json', 'r', encoding='utf-8') as f:
#             faculties = json.load(f)

#         # Fetch fields
#         print("Fetching fields...")
#         fields = get_fields(driver, faculties)
#         with open('fields.json', 'w', encoding='utf-8') as f:
#             json.dump(fields, f, ensure_ascii=False, indent=4)

#         input("Press Enter to continue to programs...")

#         # Fetch programs
#         print("Fetching programs...")
#         programs = get_programs(driver, fields)
#         with open('programs.json', 'w', encoding='utf-8') as f:
#             json.dump(programs, f, ensure_ascii=False, indent=4)

#         print("Scraping completed successfully!")

#     except Exception as e:
#         print(f"An error occurred: {e}")

#     finally:
#         driver.quit()
