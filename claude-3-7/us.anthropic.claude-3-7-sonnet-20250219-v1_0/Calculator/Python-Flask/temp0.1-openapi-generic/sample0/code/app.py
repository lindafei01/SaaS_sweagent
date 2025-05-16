
from flask import Flask, request, jsonify
import re
import ast
import operator

app = Flask(__name__)

# Define operators
operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

class ExpressionEvaluator(ast.NodeVisitor):
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return operators[type(node.op)](left, right)
    
    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        return operators[type(node.op)](operand)
    
    def visit_Num(self, node):
        return node.n
    
    def visit_Constant(self, node):
        return node.value
    
    def generic_visit(self, node):
        raise ValueError(f"Invalid expression: {node}")

def evaluate_expression(expression):
    # Sanitize input to only allow basic arithmetic operations
    if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
        raise ValueError("Invalid characters in expression")
    
    # Parse the expression into an AST
    try:
        node = ast.parse(expression, mode='eval')
        result = ExpressionEvaluator().visit(node.body)
        return str(result)
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {str(e)}")

@app.route('/calculator', methods=['POST'])
def calculator():
    try:
        data = request.get_json()
        
        if not data or 'expression' not in data:
            return jsonify({"error": "Missing expression parameter"}), 400
        
        expression = data['expression']
        
        if not isinstance(expression, str):
            return jsonify({"error": "Expression must be a string"}), 400
        
        result = evaluate_expression(expression)
        return jsonify({"result": result})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)