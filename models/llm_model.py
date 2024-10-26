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
    prompt_parts = [template['task']]

    # Add label explanations if present
    if 'label_explanations' in template:
        prompt_parts.append(template['label_explanations'])

    # Add example (the current issue)
    example = template['example'].format(title=issue_title, body=issue_body)
    prompt_parts.extend(
        (example, template['format_instructions'], template['output'])
    )
    return '\n\n'.join(prompt_parts), template['system']


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
        messages = [
            {"role": "system", "content": prompt[1]},
            {"role": "user", "content": prompt[0]},
        ]
        response = ollama.chat(model=base_model, messages=messages, format='json')
        responses.append((issue, response))
    return [postprocess_response(response) for response in responses]
