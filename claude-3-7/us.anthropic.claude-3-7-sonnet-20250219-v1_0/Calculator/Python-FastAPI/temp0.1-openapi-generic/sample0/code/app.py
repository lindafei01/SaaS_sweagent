
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import re

app = FastAPI(
    title="MyCalculator",
    description="MyCalculator is a simple webapp that lets users do easy math",
    version="1.0.11"
)

class CalculatorRequest(BaseModel):
    expression: str

class CalculatorResponse(BaseModel):
    result: str

def evaluate_expression(expression: str) -> float:
    """
    Safely evaluate a mathematical expression.
    
    This function uses a simple approach to evaluate basic arithmetic expressions
    with +, -, *, /, and parentheses. It first validates the input to ensure it
    only contains allowed characters.
    """
    # Validate the expression to only contain allowed characters
    if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
        raise ValueError("Expression contains invalid characters")
    
    # Check for potential security issues
    if '__' in expression or 'eval' in expression or 'exec' in expression or 'import' in expression:
        raise ValueError("Potentially unsafe expression")
    
    try:
        # Use eval with restricted globals/locals for basic arithmetic
        # This is still safer than direct eval since we've validated the input
        result = eval(expression, {"__builtins__": {}}, {})
        return result
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {str(e)}")

@app.post("/calculator", response_model=CalculatorResponse)
async def calculate(request: CalculatorRequest):
    try:
        result = evaluate_expression(request.expression)
        return CalculatorResponse(result=str(result))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)