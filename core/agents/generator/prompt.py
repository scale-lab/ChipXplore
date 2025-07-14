DECOMPOSER_SYS_PROMPT = lambda dialect, reqs: f"""Given a [Database schema] description, and a [Question], you need to use valid {dialect} and understand the database, and then decompose the question into subquestions for text-to-SQL generation.
When generating SQL, we should always consider constraints:

[Constraints]
- In `SELECT <column>`, just select needed columns in the Question without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

[Requirements]
  {reqs}

[Hints]
- All cell names in the library are prefixed with a variant-specific prefix. For example,: 
  - HighDensity Prefix is sky130_fd_sc_hd
  - HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
  - HighSpeed Prefix is sky130_fd_sc_hs
  - LowSpeed Prefix is sky130_fd_sc_ls
  - MediumSpeed Prefix is sky130_fd_sc_ms
  - LowPower Prefix is sky130_fd_sc_lp
- For example, the and2_1 cell in the : 
  - high density library is named 'sky130_fd_sc_hd__and2_1'
  - high density low leakage library is named 'sky130_fd_sc_hdll__and2_1'
  - high speed library is named 'sky130_fd_sc_hs__and2_1' 
  - low speed library is named 'sky130_fd_sc_ls__and2_1'
  - medium sped library is named 'sky130_fd_sc_ms__and2_1' 
  - low power library is named 'sky130_fd_sc_lp__and2_1'
"""



DECOMPOSER_WO_DECOMPOSE_SYS_PROMPT = lambda dialect, reqs: f"""Given a [Database schema] description, and a [Question], you need to use valid {dialect} and understand the database, and then generate final SQL.
When generating SQL, we should always consider constraints:

[Constraints]
- In `SELECT <column>`, just select needed columns in the Question without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

[Requirements]
  {reqs}

[Hints]
- All cell names in the library are prefixed with a variant-specific prefix. For example,: 
  - HighDensity Prefix is sky130_fd_sc_hd
  - HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
  - HighSpeed Prefix is sky130_fd_sc_hs
  - LowSpeed Prefix is sky130_fd_sc_ls
  - MediumSpeed Prefix is sky130_fd_sc_ms
  - LowPower Prefix is sky130_fd_sc_lp
- For example, the and2_1 cell in the : 
  - high density library is named 'sky130_fd_sc_hd__and2_1'
  - high density low leakage library is named 'sky130_fd_sc_hdll__and2_1'
  - high speed library is named 'sky130_fd_sc_hs__and2_1' 
  - low speed library is named 'sky130_fd_sc_ls__and2_1'
  - medium sped library is named 'sky130_fd_sc_ms__and2_1' 
  - low power library is named 'sky130_fd_sc_lp__and2_1'
"""

REQS = """
1. You must use the given operating conditions [Operating Condtions] and the standard cell variant [Standard Cell Variant] to filter entries related to the operating condition and the standard cell variant the question is referring to. 
2. Generate a SQL for each sub-query, then generate a final SQL for the input question [Question].
3. Output your answer in the same format as the given examples. 
"""

REQS_PARTITION = """
1. Generate a SQL for each sub-query, then generate a final SQL for the input question [Question].
2. Output your answer in the same format as the given examples. 
"""


DECOMPOSER_EXAMPLE_SUBQ = """
[Database schema]
{desc_str}
[Foreign keys]
{fk_str}
[Standard Cell Variant]
{scl_variant}
[Operating Condtions]
{op_cond}
[Question]
{input}

Decompose the question into sub questions, considering [Constraints], and generate the SQL after thinking step by step:
{decompose_str}
"""

DECOMPOSER_EXAMPLE_SUBQ_PARTITION = """
[Database schema]
{desc_str}
[Foreign keys]
{fk_str}
[Cell Name Prefix]
{scl_variant}
[Question]
{input}

Decompose the question into sub questions, considering [Constraints], and generate the SQL after thinking step by step:
{decompose_str}
"""

DECOMPOSER_SUFFIX_SUBQ = """
[Database schema]
{desc_str}
[Tables Info]
{table_info}
[Foreign keys]
{fk_str}
[Standard Cell Variant]
{scl_variant}
[Operating Condtions]
{op_cond}
[Question]
{input}

You must use the given operating conditions [Operating Condtions] and the standard cell variant [Standard Cell Variant] to filter entries related to the operating condition and the standard cell variant the question is referring to.
Decompose the question into sub questions, considering [Constraints], and generate the SQL after thinking step by step. Give your answer in the same format as the given example:
"""

DECOMPOSER_SUFFIX_SUBQ_PARTITION = """
[Database schema]
{desc_str}
[Tables Info]
{table_info}
[Foreign keys]
{fk_str}
[Cell Name Prefix]
{scl_variant}
[Question]
{input}

Decompose the question into sub questions, considering [Constraints], and generate the SQL after thinking step by step. Give your answer in the same format as the given example:
"""

DECOMPOSER_EXAMPLE_ZSHOT = """
[Database schema]
{desc_str}
[Foreign keys]
{fk_str}
[Standard Cell Variant]
{scl_variant}
[Operating Condtions]
{op_cond}
[Question]
{input}

Generate final SQL, considering [Constraints].Give your answer in the same format as the given example:
{query}
"""

DECOMPOSER_EXAMPLE_ZSHOT_PARTITION = """
[Database schema]
{desc_str}
[Foreign keys]
{fk_str}
[Cell Name Prefix]
{scl_variant}
[Question]
{input}

Generate final SQL, considering [Constraints].Give your answer in the same format as the given example:
{query}
"""

DECOMPOSER_SUFFIX_ZSHOT = """
[Database schema]
{desc_str}
[Tables Info]
{table_info}
[Foreign keys]
{fk_str}
[Standard Cell Variant]
{scl_variant}
[Operating Condtions]
{op_cond}
[Question]
{input}

You must use the given operating conditions [Operating Condtions] and the standard cell variant [Standard Cell Variant] to find entries related to the operating condition and the standard cell variant the question is referring to.

Generate final SQL, considering [Constraints].Give your answer in the same format as the given example:
"""

DECOMPOSER_SUFFIX_ZSHOT_PARTITION = """
[Database schema]
{desc_str}
[Tables Info]
{table_info}
[Foreign keys]
{fk_str}
[Standard Cell Variant]
{scl_variant}
[Question]
{input}

Generate final SQL, considering [Constraints].Give your answer in the same format as the given example:
"""
# You must use the given operating conditions [Operating Condtions] and the standard cell variant [Standard Cell Variant] to find the Condition_ID, and filter entries related to the operating condition and the standard cell variant the question is referring to.
# Generate final SQL, considering [Constraints].Give your answer in the same format as the given example:

SQL_CODER_USER_PROMPT = """<|begin_of_text|><|start_header_id|>user<|end_header_id|>

Generate a SQL query to answer this question: `{input}`

[Requirements]
  1. You must use the given operating conditions [Operating Condtions] and the standard cell variant [Standard Cell Variant] to find the Condition_ID, and filter entries related to the operating condition and the standard cell variant the question is referring to. 
  2. Generate a SQL for each sub-query, then generate a final SQL for the input question [Question].
  3. Output your answer in the same format as the given examples. 

[Hints]
- All cell names in the library are prefixed with a variant-specific prefix. For example,: 
  - HighDensity Prefix is sky130_fd_sc_hd
  - HighDensityLowLeakage Prefix is sky130_fd_sc_hdll
  - HighSpeed Prefix is sky130_fd_sc_hs
  - LowSpeed Prefix is sky130_fd_sc_ls
  - MediumSpeed Prefix is sky130_fd_sc_ms
  - LowPower Prefix is sky130_fd_sc_lp
- For example, the and2_1 cell in the : 
  - high density library is named 'sky130_fd_sc_hd__and2_1'
  - high density low leakage library is named 'sky130_fd_sc_hdll__and2_1'
  - high speed library is named 'sky130_fd_sc_hs__and2_1' 
  - low speed library is named 'sky130_fd_sc_ls__and2_1'
  - medium sped library is named 'sky130_fd_sc_ms__and2_1' 
  - low power library is named 'sky130_fd_sc_lp__and2_1'
- All cells in the same library have the same height.

DDL statements:

{table_info}
[Tables Info]
{desc_str}
[Foreign keys]
{fk_str}
[Standard Cell Variant]
{scl_variant}
[Operating Condtions]
{op_cond}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

The following SQL query best answers the question `{input}`:
```sql
"""