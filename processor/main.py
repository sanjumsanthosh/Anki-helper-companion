
from pydantic import BaseModel
from tqdm import tqdm
from groq import Groq
from dotenv import load_dotenv
import os
import time
import matplotlib.pyplot as plt
import json


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

def summarize_with_llama(function, force_skip=False):
    function_def = function.function_def
    function_name = function.function_name
    max_retries = 3
    retry_delay = 2  # seconds

    if skip or force_skip:
        return "Summary not available or SKIPPED"

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

    for attempt in range(max_retries):
        try:
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
            print(f"\nAttempt {attempt + 1} failed: {e} | Retrying in {retry_delay} seconds | {function_name}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return "Summary not available"


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


function_lengths = [function.end - function.start for function in get_all_function_start_end]

def plot_histogram_with_threshold(top_n):
    # Sort function lengths and get the top N
    sorted_lengths = sorted(function_lengths, reverse=True)
    top_n_lengths = sorted_lengths[:top_n]
    threshold = top_n_lengths[-1]  # The length of the Nth longest function

    # Calculate averages
    above_threshold = [length for length in function_lengths if length >= threshold]
    below_threshold = [length for length in function_lengths if length < threshold]

    average_above_threshold = sum(above_threshold) / len(above_threshold) if above_threshold else 0
    average_below_threshold = sum(below_threshold) / len(below_threshold) if below_threshold else 0

    # Plot histogram of all function lengths
    plt.figure(figsize=(10, 6))
    plt.hist(function_lengths, bins=50, edgecolor='black')
    plt.xlabel("Function Length")
    plt.ylabel("Frequency")
    plt.title("Histogram of Function Lengths")

    # Draw a vertical line at the threshold
    plt.axvline(threshold, color='red', linestyle='dashed', linewidth=1, label=f'Top {top_n} Threshold: {threshold} lines')
    plt.legend()

    # Add text annotations for averages
    plt.text(0.95, 0.95, f'Avg above threshold: {average_above_threshold:.2f}', 
             horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes, fontsize=10, color='blue')
    plt.text(0.95, 0.90, f'Avg below threshold: {average_below_threshold:.2f}', 
             horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes, fontsize=10, color='blue')

    # Save the plot
    plt.savefig("function_lengths.png")
    plt.close()
    print(f"Saved plot as {os.path.abspath('function_lengths.png')}")


# Interactive loop to ask for top N functions
TOP_X = 20
plot_histogram_with_threshold(TOP_X)
while True:
    user_input = input("Enter the number of top functions to analyze (or a non-number to exit): ")
    if not user_input.isdigit():
        break
    TOP_X = int(user_input)
    plot_histogram_with_threshold(TOP_X)


print(f"Only the top {TOP_X} functions will be summarized with Llama. The rest will be skipped.")

def create_emgithub_link(relativePath, start, end):
    target = GITHUB_URL + relativePath+ f"#L{start}-L{end}"
    encoded_target = target.replace(':', '%3A').replace('/', '%2F').replace('#', '%23')
    return f"https://emgithub.com/iframe.html?target={encoded_target}&style=default&type=code&showBorder=on&showLineNumbers=on&showFileMeta=on&showFullPath=on&showCopy=on"

def calculate_relative_path(project_path, file):
    project_path = project_path.replace('\\', '/')
    return file.replace(project_path, '').lstrip('/').lstrip('\\')

# Sort functions by length
sorted_functions = sorted(get_all_function_start_end, key=lambda f: f.end - f.start, reverse=True)

processed_count = 0

post_fix = {
    "processed_count": 0,
    "skip_counter" : 0,
    "message": "Processing functions"
}

with tqdm(total=len(sorted_functions), desc="Processing functions") as pbar:
    for i, function in enumerate(sorted_functions):
        relative_path = calculate_relative_path(PROJECT_PATH, function.file)

        # if function_name is same as file name, skip as it might be a class
        if function.function_name.lower() == function.file.split('/')[-1].split('.')[0].lower():
            post_fix["skip_counter"] += 1
            post_fix["message"] = f"Skpd {function.function_name}"
            continue

        skip = processed_count >= TOP_X

        JSON_OUTPUT[function.full_fn_name] = {
            "label": function.function_name,
            "systemPath": function.file,
            "relativePath": relative_path,
            "lineNo": function.start,
            "endLineNo": function.end,
            "emgithubIframeLink": create_emgithub_link(relative_path, function.start, function.end),
            "description": summarize_with_llama(function, force_skip=skip)
        }

        # sleep for 1 second to avoid rate limiting
        if not skip:
            time.sleep(1)

        processed_count += 1

        # Update the progress bar
        post_fix["processed_count"] = processed_count
        pbar.set_postfix(post_fix)
        pbar.update(1)

        save_path = JSON_FILE
        with open(save_path, 'w') as f:
            json.dump(JSON_OUTPUT, f, indent=4)