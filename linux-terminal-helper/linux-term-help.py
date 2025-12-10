import sys
import os
import platform
import subprocess
from google import genai
from google.genai import types

os_info = platform.freedesktop_os_release()
os_name = os_info.get("NAME", "Unknown").lower()
os_kernel = platform.release()

if len(sys.argv) > 1:
    user_prompt = " ".join(sys.argv[1:])
else:
    user_prompt = "No arguments were given. ask user to give arguments."


def get_installed_packages(filter_term: str = None) -> str:
    command = []
    
    if "ubuntu" in os_name or "debian" in os_name:
        command = ["dpkg", "--get-selections"]
    elif "arch" in os_name or "manjaro" in os_name:
        command = ["pacman", "-Q"]
    elif "fedora" in os_name or "centos" in os_name or "rhel" in os_name:
        command = ["rpm", "-qa"]
    else:
        return f"Error: The user's distribution '{os_name}' is not supported for package listing."

    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=5)
        package_list = process.stdout
        
        if filter_term:
            filtered_list = [line for line in package_list.splitlines() if filter_term.lower() in line.lower()]
            
            if len(filtered_list) > 50:
                 filtered_list = filtered_list[:50]
                 filtered_list.append("...(list truncated to save tokens)")
            
            return "\n".join(filtered_list)
        
        return "Package list is too large to send completely. Please ask the user to refine their query or use a filter_term."

    except subprocess.CalledProcessError as e:
        return f"Error running package command: {e.stderr}"
    except FileNotFoundError:
        return "Error: Package manager command not found."
    except subprocess.TimeoutExpired:
        return "Error: Package command timed out."
    
def get_manpage(package):
    command = ["man", package]

    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, timeout=5)
        manpage = process.stdout
        return manpage

    except subprocess.CalledProcessError as e:
        return f"Error running manpage command: {e.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: manpage command timed out."
    

DEFAULT_SINCE = "5 hours ago" 

def read_logs(filter_term: str = None, unit_name: str = None, since_time: str = DEFAULT_SINCE) -> str:
    
    # Simple check for Systemd environment
    if not os.path.isdir("/run/systemd/system"):
        return "Error: This system does not appear to use Systemd (journalctl not available)."

    command = ["journalctl", "--no-pager", "-o", "short"] 

    command.extend(["--since", since_time])

    if unit_name:
        command.extend(["-u", unit_name])

    if filter_term:
        command.extend(["-g", filter_term])

        if filter_term.lower() in ["error", "fail", "failure"]:
            command.extend(["-p", "err..alert"])
            
    command.extend(["-n", "100"])

    try:
        subprocess.run(["which", "journalctl"], check=True, stdout=subprocess.DEVNULL)
        
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
        
        if not result.stdout.strip():
            return f"Journalctl found no entries matching the criteria in logs from {since_time} to now."

        if len(result.stdout) > 20000: 
            return "Log output is still too large. Please use more specific filters (e.g., a unit_name or a more restrictive time frame)."
            
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        if "No entries found" in e.stderr:
            return f"Journalctl found no entries matching the criteria in logs from {since_time} to now."
        return f"Error executing journalctl: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'journalctl' command not found."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# --- Tool schema definition ---

package_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name='get_installed_packages',
            description="Retrieves a filtered list of packages installed on the user's Linux system to check for specific software. Only call this when package information is strictly necessary.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'filter_term': types.Schema(
                        type=types.Type.STRING,
                        description='An optional search term (e.g., "python", "nginx") to filter the package list by. Use this to keep the package list small and save tokens.',
                    ),
                },
                required=[],
            ),
        ),
        
    
    
    ]
)

manpage_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name='get_manpage',
            description="Retrieves the manpage for a package. Use this for giving info about usage of a specific package.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'package': types.Schema(
                        type=types.Type.STRING,
                        description='Name of the package to search.',
                    ),
                },
                required=['package'],
            ),
        ),
    ]
)

read_logs_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name='read_logs',
            description="Queries the Systemd journal for recent logs and errors. MUST be used when the user asks about system errors, service failures, or specific log file contents.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    # ... (Existing parameters) ...
                    'since_time': types.Schema(
                        type=types.Type.STRING,
                        description='An optional timestamp or relative time phrase to start reading logs from (e.g., "yesterday", "3 days ago", "10:00").',
                    ),
                },
                required=[],
            ),
        )
    ]
)

# --- 3System prompt ---

client = genai.Client()
system_preprompt = f"""
You are a Linux Terminal AI Helper. Your role is to help the user with linux terminal commands.
Keep the answers simple without unnecessary detail.
System Info: Distribution name: {os_name}, Kernel version: {os_kernel}.
If asked what you are, explain your role and mention the system info so the user knows you are aware of the environment they are running.
also describe your tools and other functions.
Use only simple text without any formatting not suitable for a terminal.
You have access to a tool named 'get_installed_packages' to check which software is installed on the user's system.
**ALWAYS use the 'get_installed_packages' tool with a filter_term whenever the user asks about a specific package (e.g., install 'nginx', remove 'vim', check status of 'python').**
If asked about installing or updating packages, check if 'yay' or some other package manager is installed using the tool. If so, **ALWAYS** recommend it alongside the default package manager with something like 'but since you have yay installed it is recommended to...'.
If the tool output confirms the package is installed, inform the user. and after that provide installation/update instructions.
You have access to a tool named 'get_manpage' that returns the manpage of a package if available. **Always try using the 'get_manpage' tool first, when the user asks about how to use the package (e.g. 'How do I use curl') if the manpage isn't found. use your own information.**
"""

function_map = {
    'get_installed_packages': get_installed_packages,
    'read_logs': read_logs,
    'get_manpage': get_manpage,
}


# --- Main Function and  Tool loop---

def main():
    print("Generating response...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_preprompt,
            tools=[package_tool, read_logs_tool, manpage_tool]
        ),
        contents=user_prompt,
    )

    while response.function_calls:
        tool_call = response.function_calls[0]
        function_name = tool_call.name
        
        if function_name in function_map:
            function_to_call = function_map[function_name]
            function_args = dict(tool_call.args)
            
            print(f"Using tool: {function_name}({function_args})", file=sys.stderr)
            
            tool_output = function_to_call(**function_args)
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_preprompt,
                    tools=[package_tool, read_logs_tool, manpage_tool]
                ),
                contents=[
                    user_prompt,
                    types.Part.from_function_response(
                        name=function_name,
                        response={"result": tool_output},
                    ),
                ],
            )
        else:
            print(f"Error: Unknown tool call requested: {function_name}")
            break

    # Final response
    print(response.text)

if __name__ == "__main__":
    main()