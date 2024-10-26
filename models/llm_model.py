import ollama
import re
import yaml
import os
import json

OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

def pull_ollama_model(base_model):
    ollama.pull(base_model)

def load_prompt_template(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def format_prompt(template, issue):
    issue_title = issue.title
    issue_body = issue.body
    prompt_parts = []

    # Add task description
    prompt_parts.append(template['task'])

    # Add label explanations if present
    if 'label_explanations' in template:
        prompt_parts.append(template['label_explanations'])

    # Add example (the current issue)
    example = template['example'].format(title=issue_title, body=issue_body)
    prompt_parts.append(example)

    # Add format instructions
    prompt_parts.append(template['format_instructions'])

    # Add output placeholder
    prompt_parts.append(template['output'])

    return '\n\n'.join(prompt_parts), template['system']


def get_label(text):
    try:
        label = re.search(r"(:?\\\"|\")label(:?\\\"|\"):\s*(:?\\\"|\")(bug|non-bug)(:?\\\"|\")", text, flags=re.DOTALL)[4]
        return label
    except Exception:
        return "label not found in response"


def postprocess_response(issue_response):
    i, r = issue_response
    # parse json response
    parsed_response = json.loads(r['message']['content'])
    i.classification = parsed_response['label']
    i.reasoning = parsed_response['reasoning']
    return i


def llm_classify(issues, base_model='llama3.1'):
    ollama.pull(base_model)
    prompt_template = load_prompt_template('prompting/bin-template.yaml')
    responses = []
    if not isinstance(issues, list):
        issues = [issues]
    
    for issue in issues:
        prompt = format_prompt(prompt_template, issue)
        messages = []
        messages.append({"role": "system", "content": prompt[1]})
        messages.append({"role": "user", "content": prompt[0]})
        response = ollama.chat(model=base_model, messages=messages, format='json')
        responses.append((issue, response))
    return [postprocess_response(response) for response in responses]
