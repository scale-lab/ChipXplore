import re 
import os 
import json 

from collections import Counter


def unpack_questions(questions: list[str]) -> str:
    """Returns a string with each list element numbered and separated by new line."""
    out = ""
    for i, question in enumerate(questions):
        out += f"{i + 1}. {question}\n"

    return out


def convert_quotes(match):
    return '"' + match.group(1).replace('"', '\\"') + '"'


def process_subtopics(generated_subtopics):
    if isinstance(generated_subtopics, dict):
        return json.dumps(generated_subtopics, indent=2)
    
    if not isinstance(generated_subtopics, str):
        generated_subtopics = str(generated_subtopics)
    
    data_string_fixed = re.sub(r"'([^']*)'", convert_quotes, generated_subtopics)
    
    try:
        data_dict = json.loads(data_string_fixed)
        return json.dumps(data_dict, indent=2)
    except json.JSONDecodeError:
        return generated_subtopics


def merge_subtopics(*topic_lists):
    merged = []
    used_names = set()
    
    for data in topic_lists:
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.values()
        else:
            raise ValueError(f"Unsupported data type: {type(data)}. Expected list or dict.")
        
        for topic in items:
            print(topic)
            if topic['name'] not in used_names:
                merged.append(topic)
                used_names.add(topic['name'])
            else:
                print(f"Warning: Duplicate name '{topic['name']}' found. Skipping this entry.")
    
    # Sort the merged list by the original ID to maintain relative order
    merged.sort(key=lambda x: x['id'])
    
    # Renumber the IDs
    for new_id, topic in enumerate(merged, start=1):
        topic['id'] = new_id
    
    return merged


    
def write_json(topic, questions, queries, results, json_path):
    if os.path.exists(json_path):
        with open(json_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}
    
    start_index = max(map(int, data.keys())) + 1 if data else 0
    for i, (question, query, result) in enumerate(zip(questions, queries, results), start=start_index):
        temp_corner = result.get('temp_corner', "")
        voltage_corner = result.get('voltage_corner', "")
        pvt_corner = result.get("pvt_corner", "")
        techlef_op_cond = result.get("techlef_op_cond", "")

        data[str(i)] = {
            'subtopic': topic,
            'question': question,
            'scl_library': result['scl_library'],
            'view': result['view'],
            'tables': result['tables'],
            # 'pvt_corner': pvt_corner,
            'temp_corner': temp_corner,
            'voltage_corner': voltage_corner,
            'techlef_op_cond': techlef_op_cond,
            'query': query,
        }
    
    with open(json_path, "w") as file:
        json.dump(data, file, indent=4)

    print(f"Updated {json_path} with {len(questions)} new entries.")



def count_stats(json_path):
    clauses = [
        "SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
        "LIMIT", "JOIN", "UNION", 
        "CREATE",   "IN", "EXISTS", "LIKE",
        "BETWEEN", "IS NULL", "IS NOT NULL", "AND", "OR", "NOT"
        ]

    clause_patterns = {clause: re.compile(r'\b' + clause + r'\b', re.IGNORECASE) for clause in clauses}
    
    clause_counts = Counter()
    with open(json_path, 'r') as file:
        data = json.load(file)
    
    for _, entry in data.items(): 
        for clause, pattern in clause_patterns.items():
            clause_counts[clause] += len(pattern.findall(entry['query']))
        
    return dict(clause_counts) 



def parse_json_list_from_string(input_string):
    json_pattern = r'```(?:json)?(.*?)```'
    matches = re.findall(json_pattern, input_string, re.DOTALL)
    
    parsed_json_list = []
    
    for match in matches:
        json_like_string = match.strip()
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
            parsed_json_list.append(table_dict)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Attempted to parse: {json_string}")
    
    return parsed_json_list