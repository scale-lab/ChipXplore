from pyverilog.vparser import parser
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator


# Path to your Verilog file
verilog_file = 'picorv.v'

# Parse the Verilog file
ast, directives = parser.parse([verilog_file])

# Print the AST
print("AST Structure:")
print(ast)

# Optionally, generate Verilog code back from the AST
codegen = ASTCodeGenerator()
generated_code = codegen.visit(ast)
print("\nGenerated Verilog Code:")
print(generated_code)