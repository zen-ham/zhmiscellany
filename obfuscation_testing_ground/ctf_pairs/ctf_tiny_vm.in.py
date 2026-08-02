def run(program):
    stack = []
    for op, arg in program:
        if op == "PUSH":
            stack.append(arg)
        elif op == "ADD":
            b = stack.pop(); a = stack.pop(); stack.append(a + b)
        elif op == "MUL":
            b = stack.pop(); a = stack.pop(); stack.append(a * b)
        elif op == "XOR":
            b = stack.pop(); a = stack.pop(); stack.append(a ^ b)
        elif op == "EMIT":
            return chr(stack.pop())
    return None

prog = [("PUSH", 7), ("PUSH", 6), ("MUL", 0), ("PUSH", 65), ("ADD", 0),
        ("PUSH", 30), ("XOR", 0), ("EMIT", 0)]
print(run(prog))
