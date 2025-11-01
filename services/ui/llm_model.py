import ollama
import re
import yaml
import os
import json
from label_config_manager import get_label_manager

OLLAMA_HOST = os.getenv(f'OLLAMA_HOST', '0.0.0.0:11434')

def pull_ollama_model(base_model):
    ollama.pull(base_model)

def load_prompt_template(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def format_prompt(template, issue):
    issue_title = issue.title
    issue_body = issue.body
    
    # Get dynamic label information from config
    label_manager = get_label_manager()
    label_names = label_manager.get_label_list_string()
    label_explanations = label_manager.format_label_explanations()
    
    # Replace placeholders in template sections with dynamic label data
    task = template['task'].format(label_list=label_names)
    label_explanations_section = template['label_explanations'].format(label_explanations=label_explanations)
    format_instructions = template['format_instructions'].format(label_list=label_names)
    
    prompt_parts = [task]

    # Add dynamic label explanations
    prompt_parts.append(label_explanations_section)

    # Add example (the current issue)
    example = template['example'].format(title=issue_title, body=issue_body)
    
    prompt_parts.extend(
        (example, format_instructions, template['output'])
    )
    return '\n\n'.join(prompt_parts), template['system']


def postprocess_response(issue_response):
    i, r = issue_response
    # parse json response
    parsed_response = json.loads(r['message']['content'])
    i.classification = parsed_response['label']
    i.reasoning = parsed_response['reasoning']
    return i


def llm_classify(issues, base_model='llama3.2'):
    ollama.pull(base_model)
    prompt_template = load_prompt_template('prompt_templates/bin-template.yaml')
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
