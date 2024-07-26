
from pydantic import BaseModel
from tqdm import tqdm
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

JSON_FILE = os.getenv("JSON_FILE")
DOT_FILE = os.getenv("DOT_FILE")
PROJECT_PATH = os.getenv("PROJECT_PATH")
GITHUB_URL = os.getenv("GITHUB_URL")
skip = os.getenv("SKIP").lower() == 'true'
KEY = os.getenv("GROQ_API_KEY")


print(f"JSON_FILE: {JSON_FILE}")
print(f"DOT_FILE: {DOT_FILE}")
print(f"PROJECT_PATH: {PROJECT_PATH}")
print(f"GITHUB_URL: {GITHUB_URL}")
print(f"SKIP: {skip}")



class ExtractedFunction(BaseModel):
    file: str
    line_number: int
    function_name: str
    full_fn_name: str


def getAllFunctions(DOT_FILE):
    all_functions = []
    with open(DOT_FILE, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'label=' in line:
                full_fn_name = line.split('[label=')[0].lstrip().rstrip()
                line = line.split('label="')[1]
                line = line.split('",')[0]
                if ':' in line:
                    file = line.split('(')[1].split(')')[0]
                    line_number = file.split(':')[-1]
                    file = file.split(':')[:-1]
                    file = ':'.join(file)
                    function_name = line.split('\\n')[0]
                    all_functions.append(ExtractedFunction(file=file, line_number=line_number, function_name=function_name, full_fn_name=full_fn_name))
    return all_functions


all_functions = getAllFunctions(DOT_FILE)

class FunctionDetails(BaseModel):
    function_name: str
    file: str
    start: int
    end: int
    full_fn_name: str
    function_def: str = None

get_all_function_start_end = []

def isChildDef(line, current_indent):
    return line.lstrip().startswith('def') and len(line) - len(line.lstrip()) > current_indent

def getFunctionDef(file, start, end):
    with open(file, 'r',encoding='utf-8') as f:
        lines = f.readlines()
        function_def = ''
        for i in range(start, end):
            function_def += lines[i]
        return function_def

for function in all_functions:
    file = function.file
    line_number = function.line_number
    function_name = function.function_name
    file = file.replace('\\', '/')
    with open(file, 'r',encoding='utf-8') as f:
        lines = f.readlines()
        line_number = max(0, int(line_number)-10)
        for i, line in enumerate(lines):
            if i == int(line_number):
                
                while f'def {function_name}' not in line and f'class {function_name}' not in line:
                    i += 1
                    line = lines[i]
                i+=1
                start = i
                i+=1
                indentation_level = len(line) - len(line.lstrip())

                # Initialize 'end' to the end of the file in case the function goes till the last line
                end = len(lines)

                # Go until the next function definition or end of file, checking indentation
                while i < len(lines):
                    
                    current_indent = len(lines[i]) - len(lines[i].lstrip())
                    if lines[i].strip() == '' or lines[i].lstrip().startswith('#') or ( lines[i].lstrip().startswith(")") and current_indent == indentation_level) :
                        i += 1
                        continue
                    
                    # Check if the current line is at the same or a higher level of indentation
                    if current_indent <= indentation_level and lines[i] != "\n"  and not isChildDef(lines[i], current_indent):
                        end = i
                        break
                    i += 1
                
                function_def = getFunctionDef(file, start, end)
                get_all_function_start_end.append(FunctionDetails(function_name=function_name, file=file, start=start, end=end, full_fn_name=function.full_fn_name, function_def=function_def))
                break

client = Groq(
    api_key=KEY
)

def summarize_with_llama(function_def):
    

    if skip:
        return "Summary not available"
    try:
        prompt = '''
You are an expert programmer. read though the selection below and give the following

[Quick summary]
in one para describe what this fuction does. and also whats the purpos of this code. max 3 lines. Short and to the point

[Inputs]
what are the inputs and what do you think they mean?. as points only

[output]
what is the expected output. as points only

Just the summary, inputs and output is required for output
'''
        # Point to the local server
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": function_def,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=1.0,
            stream=False,
            model="gemma2-9b-it",
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(e)
        return "Summary not available"


# {"ANKIConfig":{"GIT_URL":"https://github.com/piku/piku/blob/master/"},
# "piku__deploy_python":{"label":"deploy_python",
# "systemPath":"C:/Users/sanju/Desktop/projects/explore/piku\\piku.py:646",
# "relativePath":"piku.py","lineNo":"646","emgithubIframeLink":"https://emgithub.com/iframe.html?target=https%3A%2F%2Fgithub.com%2Fpiku%2Fpiku%2Fblob%2Fmaster%2Fpiku.py%23L646-L696&style=default&type=code&showBorder=on&showLineNumbers=on&showFileMeta=on&showFullPath=on&showCopy=on",
# "description":"[Quick summary]\n\nThis function, `deploy_python`, deploys a Python application. It sets up a virtual environment if needed, installs dependencies from a `requirements.txt` file, and then starts the application using another function (`spawn_app`).\n\n[Inputs]\n\n* `app`: String representing the name of the Python application to deploy.\n* `deltas` (optional): Dictionary containing additional arguments to be passed to the `spawn_app` function (presumably for customization during deployment).\n\n[Output]\n\n* The function doesn't explicitly return a value, but it likely calls another function `spawn_app` (not shown) to start the deployed application.  "},
class OutputFormat(BaseModel):
    label: str
    systemPath: str
    relativePath: str
    lineNo: int
    endLineNo: int
    emgithubIframeLink: str
    description: str

JSON_OUTPUT = {}

JSON_OUTPUT["ANKIConfig"] = {"GIT_URL": GITHUB_URL}

def create_emgithub_link(relativePath, start, end):
    target = GITHUB_URL + relativePath+ f"#L{start}-L{end}"
    encoded_target = target.replace(':', '%3A').replace('/', '%2F').replace('#', '%23')
    return f"https://emgithub.com/iframe.html?target={encoded_target}&style=default&type=code&showBorder=on&showLineNumbers=on&showFileMeta=on&showFullPath=on&showCopy=on"

def calculate_relative_path(project_path, file):
    project_path = project_path.replace('\\', '/')
    return file.replace(project_path, '').lstrip('/').lstrip('\\')

for function in tqdm(get_all_function_start_end, desc="Processing functions"):
    relative_path = calculate_relative_path(PROJECT_PATH, function.file)
    JSON_OUTPUT[function.full_fn_name] = {
        "label": function.function_name,
        "systemPath": function.file,
        "relativePath": relative_path,
        "lineNo": function.start,
        "endLineNo": function.end,
        "emgithubIframeLink": create_emgithub_link(relative_path, function.start, function.end),
        "description": summarize_with_llama(function.function_def)
    }

    # sleep for 1 second to avoid rate limiting
    import time
    if not skip: time.sleep(1)


    save_path = JSON_FILE
    import json
    with open(save_path, 'w') as f:
        json.dump(JSON_OUTPUT, f, indent=4)