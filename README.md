# Maple-TAuto

Maple-TAuto is a tool made for anyone who can't be bothered to do anything <em><font face="Brush Script MT" size=4> TRIVIAL </font></em>.
It allows you to write python code (vanilla, sympy, numpy, whatever) from the browser and get the return value of your code - also in the browser.

### Requirements
- python 3
- requests==2.23.0
- lxml==4.5.1
- click==7.1.2
- numpy==1.19.3
- sympy==1.8
- selenium==3.141.0
- ~atplotlib==3.2.2
- latex2mathml==3.61.0
- matplotlib==3.4.3

### How to use
1. <a href="https://chromedriver.chromium.org/downloads">Install</a> the selenium chromedriver that corresponds to your version of google Chrome
    - <em>Remember</em> to save the path to your <i>chromedriver.exe</i> file somewhere you will remember
2. Download this repo to your local machine
3. Go to the folder containing this project and run: ```pip install -r requirements.txt```
4. Create an empty folder in the main directory named "temp_files"
5. Now *while in the folder* run ```python main.py "DTU inside username" "DTU inside password" "path to chromedriver.exe file"```
6. Enjoy :)

### Vision
None, this project was made for no real reason at all (maybe to get some DTU street cred?).

### TODO
- It can't really parse vectors or matrices
- It thinks: 

<div style="text-align:center"><img src="https://latex.codecogs.com/svg.image?cos(x)=c&space;\cdot&space;o&space;\cdot&space;s&space;\cdot&space;x" title="cos(x)=c \cdot o \cdot s \cdot x" /></div>

- If one wants to be really sneaky, then:
    - Have selenium read what's in the <input> tag and then evaluate from there (i.e. discard the calculator)
    - Have it be a chrome extension rather than a selenium script


