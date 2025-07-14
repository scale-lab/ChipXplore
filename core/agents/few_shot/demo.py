import json 

class Demo:
    def __init__(self, input, source, explain="", scl_variant="", desc_str="", fk_str="", selection_steps="", tables="", query="", op_cond="", scl_explain="", subquestions=[], subqueries=[], route_query="") -> None:
        self.input = input
        self.source = source
        self.explain = explain
        self.scl_variant = scl_variant
        self.scl_explain = scl_explain
        self.desc_str = desc_str
        self.fk_str = fk_str 
        self.selection_steps = selection_steps
        self.tables = tables 
        self.query = query
        self.op_cond = op_cond
        self.route_query = route_query
        self.subquestions_str(subquestions, subqueries)

    def to_dict(self): 

        
        return {
            'input': self.input,
            'source': self.source,
            'explain': self.explain,
            "scl_variant": self.scl_variant,
            "scl_explain": self.scl_explain,
            'query': self.query,
            "desc_str": self.desc_str,
            "fk_str": self.fk_str,
            "tables": self.tables,
            'decompose_str': self.decompose_str,
            "op_cond": self.op_cond,
            'selection_steps': self.selection_steps,
            'route_query': self.route_query
        }

    def subquestions_str(self, subquestions, subqueries):
        self.decompose_str = ""
        for i, (subquestion, subquery) in enumerate(zip(subquestions, subqueries)):
            self.decompose_str += f"""
Subquestion {i+1}: {subquestion}
SQL 
```sql 
{subquery}
```
"""
        self.decompose_str += f"""
Final SQL is: 
SQL
```sql
{self.query}
```

Question Solved.
"""