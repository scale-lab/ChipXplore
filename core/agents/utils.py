import re
import json 


def parse_json_from_string(input_string):
    json_pattern = r'```(?:json)?(.*?)```'
    matches = re.findall(json_pattern, input_string, re.DOTALL)
    
    if matches:
        json_like_string = matches[-1].strip()
    else:
        json_like_string = input_string.strip()
    
    json_string = '{'
    for line in json_like_string.split('\n'):
        line = line.strip()
        if '//' in line:  # Remove comments after '//'
            line = line.split('//', 1)[0].strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().strip('"')  # Clean up key
            value = value.strip().strip(',')  # Clean up value
            if not (value.startswith('"') and value.endswith('"')) and not value.isnumeric():
                value = f'"{value}"'  # Add quotes to value if it's not already quoted or numeric
            json_string += f'"{key}": {value},'
    
    json_string = json_string.rstrip(',') + '}'
    
    try:
        table_dict = json.loads(json_string)
        return table_dict
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Attempted to parse: {json_string}")
        return None
    

def parse_json_from_string_v2(input_string):
    json_pattern = r'```(?:json)?(.*?)```'
    matches = re.findall(json_pattern, input_string, re.DOTALL)
    
    if matches:
        json_like_string = matches[-1].strip()
    else:
        json_like_string = input_string.strip()

    json_string = '{'
    for line in json_like_string.split('\n'):
        line = line.strip()
        if '//' in line:  # Remove comments after '//'
            line = line.split('//', 1)[0].strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().strip('"')  # Clean up key
            value = value.strip().strip(',')  # Clean up value
            
            # Fix unescaped double quotes inside values
            value = value.replace('"', '\\"')
            
            if not (value.startswith('"') and value.endswith('"')) and not value.isnumeric():
                value = f'"{value}"'  # Add quotes if not already quoted or numeric
            
            json_string += f'"{key}": {value},'

    json_string = json_string.rstrip(',') + '}'

    try:
        table_dict = json.loads(json_string)
        return table_dict
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Attempted to parse: {json_string}")
        return None


def parse_json_from_string_list(input_string):
    json_pattern = r'```(?:json)?(.*?)```'
    matches = re.findall(json_pattern, input_string, re.DOTALL)
    
    if matches:
        json_like_string = matches[-1].strip()
    else:
        json_like_string = input_string.strip()
    
    json_string = '{'
    for line in json_like_string.split('\n'):
        line = line.strip()
        if '//' in line:  # Remove comments after '//'
            line = line.split('//', 1)[0].strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().strip('"')  # Clean up key
            value = value.strip().rstrip(',')  # Remove trailing comma
            
            # Check if value is a list (proper JSON formatting)
            if value.startswith("[") and value.endswith("]"):
                json_string += f'"{key}": {value},'
            # Check if value is already a properly quoted string
            elif value.startswith('"') and value.endswith('"'):
                json_string += f'"{key}": {value},'
            # Check if value is a boolean, number, or null
            elif value.lower() in ["true", "false", "null"] or value.replace('.', '', 1).isdigit():
                json_string += f'"{key}": {value},'
            else:
                # Add quotes only if value is a plain string
                json_string += f'"{key}": "{value}",'
    
    json_string = json_string.rstrip(',') + '}'  # Remove last comma
    
    try:
        table_dict = json.loads(json_string)
        return table_dict
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Attempted to parse: {json_string}")
        return None
