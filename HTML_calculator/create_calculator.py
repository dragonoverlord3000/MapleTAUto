
def create_calculator(driver):
    driver.execute_script("console.log('Setting up calculator')")
    with open("./HTML_calculator/calc_setup_str.txt", "r") as f:
        js_str = f.read()
    f.close()
    driver.execute_script(js_str)
    driver.execute_script("console.log('Successfully created calculator')")






