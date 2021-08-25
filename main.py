# Imports
from selenium import webdriver

import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
import time
import os
import re

import argparse

# Converter modules - mostly local imports
from latex2sympy_master.latex2sympy.process_latex import process_sympy
from mathconverter.converter import mathml2latex_yarosh
import latex2mathml.converter as latex2mathml
from HTML_calculator.create_calculator import create_calculator

# Not really necessary here, but makes it easier to convert between the notebook and this `.py` file
math_print = lambda latex_input: print(fr"{latex_input}")

# Setup argument parser
parser = argparse.ArgumentParser()

# Username and password - required
parser.add_argument("username", type=str, help="Your DTU username - 's______'")
parser.add_argument("password", type=str, help="Your DTU password - '____________'")

# Absolute path to 'chromedriver.exe'
parser.add_argument("PATH", type=str, help="Path to your chromedriver.exe file, e.g. C:/Program Files (x86)/chromedriver.exe")

# Increase verbosity - optional
parser.add_argument("-v", "--verbosity", action="store_true", default=False,
                    help="increase output verbosity")

# save args to variable
args = parser.parse_args()

# Global variables
USER = args.username
PASSWORD = args.password
VERBOSE = args.verbosity

TO_REMOVE_ALL = ["\\left", "\\right", "\;"]

# Helper function
def rm_all_tmp_files():
    for file in os.listdir("./temp_files/"):
        if not ("empty" in file) or ("checkpoint" in file):
            os.remove("./temp_files/" + file)

#### Preprocessing
# Remove all instances of to_remove
def remove_all(expr, to_remove): # e.g. \\left and \\right
    """
    Args:
        expr (str) - the latex expression
        to_remove (str, list or tuple) - the parts to remove
        
    Returns:
        the input expression, but with `to_removed` removed from it explicitly
        - note that given e.g. \\phantom it will NOT remove the first '{' and last '}'
        
    Example:
        >>>remove_all("\\left[\\begin{array}{cc}-1& 5\\\\ 9& -3\\end{array}\\right]\\phantom{\\rule{3pt}{0ex}} * 2", ["\\left", "\\right"])
        '[\\begin{array}{cc}-1& 5\\\\ 9& -3\\end{array}]\\phantom{\\rule{3pt}{0ex}} * 2'
    """
    if isinstance(to_remove, (list, tuple)):
        for trm in to_remove:
            expr = expr.replace(trm, "")
    elif isinstance(to_remove, str):
        expr = expr.replace(to_remove, "")
    else:
        raise Exception("Error, `to_remove` has to be a list, tuple or a string")
    return expr


# Remove more systematically
def remove_in_out(expr, to_remove, ins=True):
    """
    Args:
        expr (str) - the latex expression
        to_remove (str) - the part to remove
        ins (bool) - whether or not to keep what's inside of that which is to be removed
        
    Returns:
        the input expression, but with `to_removed` removed from it 
        - note that given e.g. \\phantom it will also remove the first { and last }
        
    Example:
        >>>remove_in_out("\\frac{{\\mathit{x}}^{2}}{\\sqrt{\\mathit{\\pi }}}\\phantom{\\rule{3pt}{0ex}}", "\\mathit")
        '\\frac{{x}^{2}}{\\sqrt{\\pi }}\\phantom{\\rule{3pt}{0ex}}'
        >>>remove_in_out("\\frac{{\\mathit{x}}^{2}}{\\sqrt{\\mathit{\\pi }}}\\phantom{\\rule{3pt}{0ex}}", "\\mathit", False)
        '\\frac{{}^{2}}{\\sqrt{}}\\phantom{\\rule{3pt}{0ex}}'
        >>>remove_in_out("\\frac{{\\mathit{x}}^{2}}{\\sqrt{\\mathit{\\pi }}}\\phantom{\\rule{3pt}{0ex}}", "\\phantom", False)
        '\\frac{{\\mathit{x}}^{2}}{\\sqrt{\\mathit{\\pi }}}'
        
    """
    
    num_left, num_right = 0, 0
    new_expr = []
    
    for i, part in enumerate(expr.split(to_remove)):
        if ins:
            inside = ""
        
        if i == 0:
            new_expr.append(part)
            continue
        
        idx = 0
        
        for j, char in enumerate(part):
            if char == "{":
                num_left += 1
                if num_left == 1:
                    continue
            elif char == "}":
                num_right += 1
            
            if num_left == num_right:
                idx = j
                break
            
            if ins:
                inside += char
        
        if ins:
            new_expr.append(inside)
        new_expr.append(part[idx + 1:])
        num_left, num_right = 0, 0

    ret_expr = "".join(new_expr)
    return ret_expr

# The preprocess function
def preprocess(expr):
    """
    Args:
        expr (str) - the raw latex expression
    
    Returns (str):
        the input expression, but with all the redundant latex (which latex2sympy can't parse) removed
        
    Example:
        >>>preprocess("\\frac{{4}^{6}\\cdot {8}^{8}\\cdot {32}^{5}}{{16}^{7}}\\phantom{\\rule{3pt}{0ex}}")
        '\\frac{{4}^{6}\\cdot {8}^{8}\\cdot {32}^{5}}{{16}^{7}}'
    """
    # Note: this ordering of remove calls is the one I found to work the best
    expr = remove_all(expr, TO_REMOVE_ALL)
    expr = remove_in_out(expr, "\\phantom", ins=False)
    expr = remove_in_out(expr, "\\mathit", ins=True)
    expr = remove_in_out(expr, "\\mathrm", ins=True)    
    expr = remove_all(expr, "{}")
    
    expr = expr.replace("–", "-") # because these are apparently not the same thing
    expr = " ".join(expr.split())
    unnecesarry_brackets = re.findall("{[a-zA-Z]}", expr)
    for unnec in unnecesarry_brackets:
        expr = expr.replace(unnec, unnec[1])
    
    expr = expr.strip()
    expr = expr[:-1].strip() if expr[-1] == "=" else expr
    return expr


###### CONVERSIONS
def mathml2latex(file_path):
    """
    Args:
        file_path (str) - file path to the xml document with the mathml to translate
        
    Returns (str):
        the mathml in the `file_path` xml file, but converted to latex 
    """
    
    # Read the data
    data = open(file_path, 'rb')
    xslt_content = data.read()
    data.close()
    
    # Convert mathml to latex
    out = mathml2latex_yarosh(xslt_content)
    
    # Remove unnecessary spaces + "$" characters
    out = "".join(out.split("$")).strip()
    
    return out

def mathml2sympy(file_path):
    try:
        tex_expr = mathml2latex(file_path)
        expr = preprocess(tex_expr)
        ret_expr = process_sympy(expr)
    except Exception as e:
        if VERBOSE:
            print(f"Error: {e}")
        
    if VERBOSE:
        print(f"Latex Expression: {tex_expr}")
        print(f"Preprocessed Latex Expression: {expr}")
        print(f"Sympy Expression: {ret_expr}")
    return ret_expr


# The webdriver configs
PATH = args.PATH
start_url = "https://cn.inside.dtu.dk/cnnet/element/642687/mapletav2/student"

# The path for file translations
tmp_path = "./temp_files/"

# Starting the webdriver
driver = webdriver.Chrome(PATH)
driver.get(start_url)

# More global variables
former_url = ""
former_print_url = ""

start_time = time.time()
former_section_name = ""

if VERBOSE:
    print(str(former_section_name)[:50] + "...")

mjaxes_print_counter = 0

command_to_run_before = ""

rm_all_tmp_files()

# The main loop
while "dtu" in driver.current_url:
    try:
        if len(driver.window_handles) >= 2 and "dtu.mobius" not in driver.current_url:
            driver.switch_to.window(driver.window_handles[1])

        # Loggin in
        if "sts.ait.dtu.dk" in driver.current_url:
            user = driver.find_element_by_id("userNameInput")
            user.send_keys(USER)
            pas = driver.find_element_by_id("passwordInput")
            pas.send_keys(PASSWORD)
            driver.find_element_by_id("submitButton").click()
        # Go to the course    
        if "cn.inside.dtu.dk" in driver.current_url:
            a = driver.find_elements_by_tag_name("a")
            for link in a:
                if "til kursets forside" in link.text:
                    link.click()

        # At the same URL
        try:
            new_former = driver.find_elements_by_class_name("sectionName")[0].text
        except:
            continue
        if (former_url == driver.current_url) and (former_section_name == new_former):

            # Has the calculator been created yet?
            try:
                sp_input = driver.find_element_by_id("sp_input")
            except:
                sp_input = None

            # Calculator hasn't been created yet
            if not sp_input:
                create_calculator(driver)
                if VERBOSE:
                    print(f"Created HTML-Calculator")
                for i, val in enumerate(x):
                    # driver.execute_script(f"""createInfoBox('{latex2mathml.convert(sp.latex(val))}', {i})""")
                    driver.execute_script(f"""createInfoBox('{sp.maple_code(val)}', {i})""")

            # Calculator has already been created
            else: 
                command_to_run = sp_input.get_attribute("value").strip()
                if len(command_to_run) > 0 and command_to_run != command_to_run_before:
                    command_to_run_before = command_to_run

                    # run command if last character is an `;`
                    if command_to_run[-1] == ";":
                        command_to_run = command_to_run[:-1]
                        if VERBOSE:
                            print(f"\nExecuting: {command_to_run}")
                        exec("ret_val = " + command_to_run)
                        print(f"Result: ", end="")
                        math_print(sp.latex(ret_val))

                        # remove all current outputs
                        driver.execute_script("""let p_node = document.getElementById('sp_call_output'); while (p_node.firstChild) {p_node.removeChild(p_node.lastChild)}""")
                        # add output to HTML
                        # driver.execute_script(f"""document.getElementById('sp_call_output').appendChild((new DOMParser().parseFromString('<span class="MathJax">{latex2mathml.convert(sp.latex(ret_val))}</span>', "text/xml").firstChild))""")                        
                        # Display it as maple code, cause that's what the '<input>' expects - i.e. it's ready for copy paste 
                        driver.execute_script(f"""displayOutput('<span>{sp.maple_code(ret_val)}</span>')""")
                        
                    else:
                        time.sleep(1)
                        print("#", end="")
                        continue

                else:
                    time.sleep(1)
                    print("#", end="")
                    continue

        # New URL
        else:
            time.sleep(4)
            if former_print_url != driver.current_url:
                if VERBOSE:
                    print("Current URL (possibly shortened): ", str(driver.current_url)[:50] + "\n")
                former_print_url = driver.current_url

            mjaxes = driver.find_elements_by_class_name("MathJax")
            mjaxes = [mjax for mjax in mjaxes if mjax.get_attribute("data-mathml") is not None]

            if len(mjaxes) == 0:
                mjaxes_print_counter += 1
                if mjaxes_print_counter % 10 == 0:
                    if VERBOSE:
                        print("Length mjaxes = 0")
                continue

            # This is a somewhat necessary step
            rm_all_tmp_files()
            for i, mjax in enumerate(mjaxes):
                expr = mjax.get_attribute("data-mathml")
                with open(f"./temp_files/mjax_{i}.xml", "w") as f:
                    f.write(expr)
                f.close()

            x = []

            # Convert the mathml to sympy
            for file in os.listdir("./temp_files/"):
                try:
                    sp_expr = mathml2sympy("./temp_files/" + file)
                except Exception as e: 
                    print(e)
                    rm_all_tmp_files()
                    sp_expr = None
                    break

                if not (sp_expr is None):
                    x.append(sp_expr)

                if VERBOSE:
                    print(f"Interpreted as:")
                    math_print(sp.latex(sp_expr))

                    print(f"Calling `sp.simplify`:")
                    math_print(sp.latex(sp.simplify(sp_expr)))

                    print(f"In Mathml form: " + latex2mathml.convert(sp.latex(sp_expr)))

            former_url = driver.current_url
            former_section_name = driver.find_elements_by_class_name("sectionName")[0].text
    except Exception as e:
        print(f"Error: {e}")





