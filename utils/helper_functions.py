def format_classification_output(issues, results):
    """
    Formats the classification output for display.
    """
    output = []
    for issue, result in zip(issues, results):
        output.append(f"**Issue:** {issue}\n**Classification:** {result}")
    return "\n\n".join(output)