import re 
import sys
import argparse
import logging
from colorama import Fore, Style, init

init(autoreset=True)

class ColorFormatter(logging.Formatter):
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: Fore.CYAN + FORMAT + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + FORMAT + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + FORMAT + Style.RESET_ALL,
        logging.ERROR: Fore.RED + FORMAT + Style.RESET_ALL,
        logging.CRITICAL: Fore.MAGENTA + FORMAT + Style.RESET_ALL
    }

    def format(self, record):
        if record.levelno == logging.INFO and ':' in record.msg:
            # Extract color from the message
            color, message = record.msg.split(':', 1)
            color_attr = getattr(Fore, color.upper(), Fore.WHITE)
            record.msg = message.strip()
            log_fmt = color_attr + self.FORMAT + Style.RESET_ALL
        else:
            log_fmt = self.FORMATS.get(record.levelno, self.FORMAT)
        
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)



def get_logger(output):
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=output, level=logging.INFO, filemode='w+')
    logging.getLogger("httpx").setLevel(logging.WARNING)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())

    file_handler = logging.FileHandler(output)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(ColorFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def parse_qa_pairs(text: str) -> list:
    if '```sql' in text:
        return parse_qa_pairs_code_blocks(text)
    else:
        return parse_qa_pairs_code_blocks(text)

def parse_qa_pairs_code_blocks(text: str) -> list:
    subq_pattern = r"Subquestion\s*\d+\s*:"
    lines = text.split('\n')
    qa_pairs = []
    for idx, line in enumerate(lines):
        if re.findall(subq_pattern, line, re.IGNORECASE):
            query = line.strip()
            try:
                start_idx = next(i for i in range(idx + 1, len(lines)) if '```' in lines[i])
                end_idx = next(i for i in range(start_idx + 1, len(lines)) if '```' in lines[i])
                answer = " ".join(lines[start_idx + 1: end_idx]).strip()
                qa_pairs.append((query, answer))
            except StopIteration:
                break
    return qa_pairs

def parse_qa_pairs_inline(text: str) -> list:
    subquestions = re.split(r'Subquestion \d+:', text)[1:]
    qa_pairs = []
    for subq in subquestions:
        parts = subq.split('SQL', 1)
        if len(parts) == 2:
            question = parts[0].strip()
            answer = parts[1].strip()
            answer = re.sub(r'; Question Solved\..*', '', answer, flags=re.DOTALL)
            final_sql_match = re.search(r'Final SQL is:(.*)', answer, re.DOTALL)
            if final_sql_match:
                answer = final_sql_match.group(1).strip()
            else:
                answer = answer.rstrip(';')
            qa_pairs.append((question, answer))
    return qa_pairs

# # source: 
# def parse_qa_pairs(res: str, end_pos=2333) -> list:
#     subq_pattern = r"Subquestion\s*\d+\s*:"
#     lines = res.split('\n')
#     qa_pairs = []
#     end_pos = len(lines) if (end_pos == 2333) else end_pos
#     for idx in range(0, end_pos):
#         if re.findall(subq_pattern, lines[idx], re.IGNORECASE) != []:
#             query = lines[idx]
#             start_idx = -1
#             for idx2 in range(idx + 1, end_pos):
#                 if '```' in lines[idx2]:
#                     start_idx = idx2
#                     break
#             if start_idx == -1: return []
#             for idx3 in range(start_idx + 1, end_pos):
#                 if '```' in lines[idx3]:
#                     end_idx = idx3
#                     break
#             if end_idx == -1: return []
#             answer = " ".join(lines[start_idx + 1: end_idx])
#             qa_pairs.append((str(query), str(answer)))
#             idx = end_idx
#     return qa_pairs


# def parse_qa_pairs_2(text: str) -> list:
#     # Split the text into subquestions
#     subquestions = re.split(r'Subquestion \d+:', text)[1:]
    
#     qa_pairs = []
    
#     for subq in subquestions:
#         # Split each subquestion into question and answer parts
#         parts = subq.split('SQL', 1)
#         if len(parts) == 2:
#             question = parts[0].strip()
#             answer = parts[1].strip()
            
#             # Remove the "Question Solved." part if it exists
#             answer = re.sub(r'; Question Solved\..*', '', answer, flags=re.DOTALL)
            
#             # Handle the case of the last subquestion with Final SQL
#             final_sql_match = re.search(r'Final SQL is:(.*)', answer, re.DOTALL)
#             if final_sql_match:
#                 answer = final_sql_match.group(1).strip()
#             else:
#                 # Remove the trailing semicolon if it exists
#                 answer = answer.rstrip(';')
            
#             qa_pairs.append((question, answer))
    
#     return qa_pairs



def parse_sql_from_string(input_string):
    # Check if the input contains SQL code blocks
    sql_pattern = r'```sql(.*?)```'
    code_block_matches = list(re.finditer(sql_pattern, input_string, re.DOTALL))
    
    if code_block_matches:
        # If code blocks are present, return the last SQL block
        return code_block_matches[-1].group(1).strip()
    else:
        # If no code blocks, look for inline SQL
        final_sql_pattern = r'Final SQL is:\s*(.*?)(?:;\s*Question Solved\.|\Z)'
        final_sql_match = re.search(final_sql_pattern, input_string, re.DOTALL)
        
        if final_sql_match:
            return final_sql_match.group(1).strip()
        else:
            # If no "Final SQL" is found, extract all SQL statements
            sql_statements = re.findall(r'SQL\s+(.*?)(?=Subquestion|\Z)', input_string, re.DOTALL)
            if sql_statements:
                return '; '.join(stmt.strip() for stmt in sql_statements)
            else:
                return input_string.strip()


            
# def parse_sql_from_string(input_string):
#     sql_pattern = r'```sql(.*?)```'
#     all_sqls = []
#     for match in re.finditer(sql_pattern, input_string, re.DOTALL):
#         all_sqls.append(match.group(1).strip())
    
#     if all_sqls:
#         return all_sqls[-1]
#     else:
#         return input_string


def parse_sql_text(text):
    lines = text.split('\n')
    questions = []
    answers = []
    final_sql = ""
    
    current_question = ""
    current_answer = ""
    
    for line in lines:
        if line.startswith("Subquestion"):
            if current_question and current_answer:
                questions.append(current_question)
                answers.append(current_answer)
                current_question = ""
                current_answer = ""
            current_question = line
        elif line.startswith("SQL"):
            current_answer += line[4:].strip() + " "
        elif line.startswith("Final SQL is:"):
            final_sql = " ".join(lines[lines.index(line)+1:])
            break
    
    # Add the last question-answer pair if exists
    if current_question and current_answer:
        questions.append(current_question)
        answers.append(current_answer)
    
    return questions, answers, final_sql


def parse_cypher_from_string(input_string):
    cypher_pattern = r'```cypher(.*?)```'
    all_cyphers = []
    for match in re.finditer(cypher_pattern, input_string, re.DOTALL):
        all_cyphers.append(match.group(1).strip())
    
    if all_cyphers:
        return all_cyphers[-1]
    else:
        return input_string


def parse_temp(string):
    match = re.search(r"Temperature of ([\d\.]+)", string)
    if match:
        temperature = float(match.group(1))
        print("Temperature:", temperature)
    else:
        print("[ERROR]: Temperature not found, assuming default temperature 25.0")
        return float(25.0)
        # sys.exit(0)
    return float(temperature) 


def parse_voltage(string):
    match = re.search(r"Voltage of ([\d\.]+)", string)
    if match:
        voltage = float(match.group(1))
    else:
        print("[ERROR]: Voltage not found, assuming default voltage 1.8")
        return float(1.8)
        # sys.exit(0)
    return float(voltage) 

def main():
    gpt_four_response = """
Response is:  To solve the question "Which input pin of the sky130_fd_sc_hd__nand2_1 has the lowest fall propagation delay for an output load of 0.0005 and input rise time of 0.01?", we need to follow these steps:

### Subquestions and SQL Queries

#### Subquestion 1: Identify the Condition_ID for the high density library variant under the given operating conditions (temperature 25 and voltage 1.8).
```sql
SELECT Condition_ID 
FROM Operating_Conditions 
WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd';
```

#### Subquestion 2: Find the Cell_ID for the cell named sky130_fd_sc_hd__nand2_1 under the identified Condition_ID.
```sql
SELECT Cell_ID 
FROM Cells 
WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = (
    SELECT Condition_ID 
    FROM Operating_Conditions 
    WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd'
);
```

#### Subquestion 3: Find the Output_Pin_IDs associated with the Cell_ID obtained from Subquestion 2.
```sql
SELECT Output_Pin_ID 
FROM Output_Pins 
WHERE Cell_ID = (
    SELECT Cell_ID 
    FROM Cells 
    WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = (
        SELECT Condition_ID 
        FROM Operating_Conditions 
        WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd'
    )
);
```

#### Subquestion 4: Find the Timing_Table_ID for the timing type 'cell_fall' related to the Output_Pin_IDs obtained from Subquestion 3.
```sql
SELECT Timing_Table_ID, Related_Input_Pin 
FROM Timing_Tables 
WHERE Output_Pin_ID IN (
    SELECT Output_Pin_ID 
    FROM Output_Pins 
    WHERE Cell_ID = (
        SELECT Cell_ID 
        FROM Cells 
        WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = (
            SELECT Condition_ID 
            FROM Operating_Conditions 
            WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd'
        )
    )
) AND Timing_Type = 'cell_fall';
```

#### Subquestion 5: Find the input pin with the lowest fall propagation delay for the specified output load and input rise time.
```sql
SELECT Related_Input_Pin 
FROM Timing_Table_Values 
JOIN Timing_Tables ON Timing_Tables.Timing_Table_ID = Timing_Table_Values.Timing_Table_ID
WHERE Timing_Table_Values.Index_1 = 0.01 AND Timing_Table_Values.Index_2 = 0.0005 AND Timing_Tables.Timing_Type = 'cell_fall'
ORDER BY Timing_Table_Values.Value ASC
LIMIT 1;
```

### Final SQL Query
Combining the necessary parts from the subquestions, the final SQL query to directly answer the question would be:
```sql
SELECT Related_Input_Pin 
FROM Timing_Table_Values 
JOIN Timing_Tables ON Timing_Tables.Timing_Table_ID = Timing_Table_Values.Timing_Table_ID
WHERE Timing_Table_Values.Index_1 = 0.01 AND Timing_Table_Values.Index_2 = 0.0005 
AND Timing_Tables.Timing_Type = 'cell_fall'
AND Timing_Tables.Output_Pin_ID IN (
    SELECT Output_Pin_ID 
    FROM Output_Pins 
    WHERE Cell_ID = (
        SELECT Cell_ID 
        FROM Cells 
        WHERE Name = 'sky130_fd_sc_hd__nand2_1' AND Condition_ID = (
            SELECT Condition_ID 
            FROM Operating_Conditions 
            WHERE Temperature = 25.0 AND Voltage = 1.8 AND Cell_Variant = 'sky130_fd_sc_hd'
        )
    )
)
ORDER BY Timing_Table_Values.Value ASC
LIMIT 1;
```
"""

    sql_coder_response = """
Subquestion 1: Identify the Condition_ID for the operating condition 'nom'
SQL SELECT Condition_ID FROM Operating_Conditions WHERE Condition = 'nom'; Subquestion 2: Filter the entries in the RoutingLayers table related to the standard cell variant'sky130_fd_sc_hd' and the operating condition 'nom' SQL SELECT * FROM RoutingLayers WHERE CellVariant ='sky130_fd_sc_hd' AND Corner = 'nom'; Subquestion 3: Filter the entries in the RoutingLayers table related to the standard cell variant'sky130_fd_sc_hs' and the operating condition 'nom' SQL SELECT * FROM RoutingLayers WHERE CellVariant ='sky130_fd_sc_hs' AND Corner = 'nom'; Subquestion 4: Compare the pitch value for the met5 layer between the high density and high speed libraries for the nominal corner SQL SELECT (SELECT PitchX FROM RoutingLayers WHERE Name ='met5' AND CellVariant ='sky130_fd_sc_hd' AND Corner = 'nom') - (SELECT PitchX FROM RoutingLayers WHERE Name ='met5' AND CellVariant ='sky130_fd_sc_hs' AND Corner = 'nom'); Final SQL is: SELECT (SELECT PitchX FROM RoutingLayers WHERE Name ='met5' AND CellVariant ='sky130_fd_sc_hd' AND Corner = 'nom') - (SELECT PitchX FROM RoutingLayers WHERE Name ='met5' AND CellVariant ='sky130_fd_sc_hs' AND Corner = 'nom'); Question Solved.
"""

    sql_coder_response_2 = """
 Subquestion 1: Find the Macro_ID of the cell 'nand2_1' in the High Density library. Prefix the cell name with library name, i.e., 'nand2_1' in the High Density library is named'sky130_fd_sc_hd__nand2_1'
SQL
SELECT m.Macro_ID FROM Macros m WHERE m.Name ='sky130_fd_sc_hd__nand2_1' AND m.Cell_Library ='sky130_fd_sc_hd'
Subquestion 2: Find the Macro_ID of the cell 'nand2_1' in the Medium Speed library. Prefix the cell name with library name, i.e., 'nand2_1' in the Medium Speed library is named'sky130_fd_sc_ms__nand2_1'
SQL
SELECT m.Macro_ID FROM Macros m WHERE m.Name ='sky130_fd_sc_ms__nand2_1' AND m.Cell_Library ='sky130_fd_sc_ms'
Subquestion 3: Retrieve the cell width with the Macro_ID found in the previous steps
SQL
SELECT m.Size_Width FROM Macros m WHERE m.Macro_ID = (SELECT m.Macro_ID FROM Macros m WHERE m.Name ='sky130_fd_sc_hd__nand2_1' AND m.Cell_Library ='sky130_fd_sc_hd') AND m.Macro_ID = (SELECT m.Macro_ID FROM Macros m WHERE m.Name ='sky130_fd_sc_ms__nand2_1' AND m.Cell_Library ='sky130_fd_sc_ms')
"""

    qa_pairs = parse_qa_pairs(gpt_four_response) 

    for pair in qa_pairs:
        question = pair[0]
        query = pair[1]
        print("------------------------")
        print("Subquestion: ", question)
        print("Subquery: ", query)
        print("------------------------")
   
    sqls = parse_sql_from_string(gpt_four_response)
    print("Final SQL is", sqls)
    
    qa_pairs = parse_qa_pairs(text=sql_coder_response) 
    for pair in qa_pairs:
        question = pair[0]
        query = pair[1]
        print("------------------------")
        print("Subquestion: ", question)
        print("Subquery: ", query)
        print("------------------------")
    sqls = parse_sql_from_string(sql_coder_response)
    print("Final SQL is", sqls)
    
    qa_pairs = parse_qa_pairs(text=sql_coder_response_2) 
    for pair in qa_pairs:
        question = pair[0]
        query = pair[1]
        print("------------------------")
        print("Subquestion: ", question)
        print("Subquery: ", query)
        print("------------------------")
    
    sqls = parse_sql_from_string(sql_coder_response_2)
    print("Final SQL is", sqls)
   
if __name__ == '__main__':
    main()
    
