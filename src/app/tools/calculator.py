import re
import math

def calculate(expression: str) -> str:
    """
    Safely evaluates a basic mathematical expression.
    Supported: +, -, *, /, **, %, sqrt, sin, cos, tan, log.
    """
    # Remove any characters that aren't math-safe
    expression = re.sub(r'[^0-9+\-*/().%sqrtincolasog\s]', '', expression)
    
    # Replace common function names with math equivalents
    replacements = {
        'sqrt': 'math.sqrt',
        'sin': 'math.sin',
        'cos': 'math.cos',
        'tan': 'math.tan',
        'log': 'math.log',
        'pi': 'math.pi',
        'e': 'math.e'
    }
    
    for word, replacement in replacements.items():
        expression = expression.replace(word, replacement)

    try:
        # Using a restricted eval for safety
        result = eval(expression, {"__builtins__": None}, {"math": math})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test cases
    print(calculate("127.5 * 3.4"))
    print(calculate("sqrt(256) + log(10)"))
