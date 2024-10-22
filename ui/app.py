import gradio as gr
from dataclasses import dataclass
from typing import List, Union, Tuple
import re
from scraping.github_scraper import scrape_github_issues, Issue
from models.setfit_model import setfit_classify
from models.llm_model import llm_classify, pull_ollama_model

def validate_github_url(url: str) -> Tuple[bool, str, str]:
    """Validates GitHub URL and determines if it's an issue or project URL"""
    if not url:
        return False, "Invalid", "Please enter a URL"
    
    # GitHub URL patterns
    issue_pattern = r'https?://github\.com/[\w-]+/[\w-]+/issues/\d+'
    project_pattern = r'https?://github\.com/[\w-]+/[\w-]+'
    org_and_project_pattern = r'https?://github\.com/([\w-]+)/([\w-]+)'
    issue_number_pattern = r'https?://github\.com/[\w-]+/[\w-]+/issues/(\d+)'

    if re.match(issue_pattern, url):
        org_and_project_match = re.search(org_and_project_pattern, url)
        org_and_project_name = f"{org_and_project_match.group(1)}/{org_and_project_match.group(2)}"
        return True, "issue", f"Valid issue URL,\nProject: {org_and_project_name}\nIssue Number: {re.search(issue_number_pattern, url).group(1)}"
    elif re.match(project_pattern, url):
        org_and_project_match = re.search(org_and_project_pattern, url)
        org_and_project_name = f"{org_and_project_match.group(1)}/{org_and_project_match.group(2)}"
        return True, "project", f"Valid project URL,\nProject: {org_and_project_name}"
    else:
        return False, "invalid", "Invalid GitHub URL format"

def process_url(url: str, num_issues: int, issue_state: str) -> Tuple[str, gr.update, List[Tuple]]:
    is_valid, url_type, message = validate_github_url(url)
    
    if not is_valid:
        return message, gr.update(visible=False), []
    
    if url_type == "project":
        result = scrape_github_issues(url, num_issues=num_issues, state=issue_state)
    else:  # single issue
        result = scrape_github_issues(url)
        
    if isinstance(result, list) and len(result) > 0:
        output = "Scraped Issues:\n\n"
        for issue in result:
            output += str(issue) + "\n"
            output += f"{'-'*50}\n"
        return output, gr.update(visible=True), result
    elif isinstance(result, Issue):
        output = str(result) + "\n"
        return output, gr.update(visible=True), result
    else:
        return "No issues found", gr.update(visible=False), []

def update_scraping_controls(url: str):
    """Updates visibility of scraping controls based on URL type"""
    is_valid, url_type, message = validate_github_url(url)
    
    if not is_valid:
        return [
            gr.update(visible=False),  # num_issues
            gr.update(visible=False),  # issue_state
            gr.update(value=message)   # validation message
        ]
    
    if url_type == "project":
        return [
            gr.update(visible=True),   # num_issues
            gr.update(visible=True),   # issue_state
            gr.update(value=message)   # validation message
        ]
    else:
        return [
            gr.update(visible=False),  # num_issues
            gr.update(visible=False),  # issue_state
            gr.update(value=message)   # validation message
        ]

def classify_issues(issues: List[Tuple], model_type: str, base_model: str = None) -> List[Tuple]:
    if not isinstance(issues, list):
        issues = [issues] 
    if model_type == "setfit":
        responses = setfit_classify(issues, base_model=base_model)
    elif model_type == "ollama":
        responses = llm_classify(issues, base_model=base_model)
    return responses

def classify_and_display(issues: List[Tuple], model: str, base_model: str, pull_status: str) -> str:
    if model == "ollama" and pull_status != "Model pulled successfully!":
        return "Please pull the Ollama model first before classification."
    
    classified_issues = classify_issues(issues, model, base_model)
    output = "Classified Issues:\n\n"
    for issue in classified_issues:
        output += str(issue) + "\n"
        output += f"{'-'*50}\n"
    return output

def update_model_choices(model_choice: str):
    if model_choice == "setfit":
        return [
            gr.update(
                visible=True,
                choices=[
                    "Collab-uniba/cfs-binary-setfit",
                    "Collab-uniba/fprime-binary-setfit",
                    "Collab-uniba/nlbse-multi-class-setfit",
                    "Collab-uniba/nlbse-binary-setfit",
                ],
                value="Collab-uniba/fprime-binary-setfit",
                label="Select SetFit Base Model"
            ),
            gr.update(visible=False),
            gr.update(visible=False)
        ]
    else:  # ollama
        return [
            gr.update(
                visible=True,
                choices=[
                    "llama3.1",
                    "llama3.2",
                    "mistral",
                    "gemma2",
                    "qwen2.5",
                    "phi3.5",
                    "codegemma",
                ],
                value="llama3.1",
                label="Select Ollama Base Model"
            ),
            gr.update(visible=True),
            gr.update(visible=True, value="")
        ]

def pull_model(base_model: str) -> str:
    try:
        pull_ollama_model(base_model)
        return "Model pulled successfully!"
    except Exception as e:
        return f"Error pulling model: {str(e)}"

with gr.Blocks() as iface:
    gr.Markdown("# GitHub Issue/Project Scraper and Classifier")
    
    with gr.Row():
        url_input = gr.Textbox(label="Enter GitHub URL")
    
    # URL validation message
    url_status = gr.Textbox(
        label="URL Status",
        interactive=False,
        value=""
    )
    
    # Project-specific controls
    with gr.Row(visible=False) as project_controls:
        num_issues = gr.Slider(
            minimum=1,
            maximum=100,
            value=10,
            step=1,
            label="Number of Issues to Scrape"
        )
        issue_state = gr.Dropdown(
            choices=["open", "closed", "all"],
            value="all",
            label="Issue State"
        )
    
    scrape_button = gr.Button("Scrape")
    scraped_output = gr.Textbox(label="Scraped Result")
    
    with gr.Row(visible=False) as classification_row:
        with gr.Column():
            model_dropdown = gr.Dropdown(
                choices=["setfit", "ollama"],
                label="Select Classification Model",
                value="setfit"
            )
            
            base_model_dropdown = gr.Dropdown(
                choices=[
                    "Collab-uniba/cfs-binary-setfit",
                    "Collab-uniba/fprime-binary-setfit",
                    "Collab-uniba/nlbse-multi-class-setfit",
                    "Collab-uniba/nlbse-binary-setfit",
                ],
                label="Select SetFit Base Model",
                value="Collab-uniba/fprime-binary-setfit",
                visible=True
            )
            
            with gr.Column(visible=False) as ollama_controls:
                pull_button = gr.Button("Pull Ollama Model")
                pull_status = gr.Textbox(
                    label="Pull Status",
                    interactive=False,
                    value=""
                )
            
        classify_button = gr.Button("Classify Issues")
    
    classified_output = gr.Textbox(label="Classified Result")
    
    scraped_issues = gr.State([])
    
    # Event handlers
    url_input.change(
        update_scraping_controls,
        inputs=[url_input],
        outputs=[project_controls, issue_state, url_status]
    )
    
    scrape_button.click(
        process_url,
        inputs=[url_input, num_issues, issue_state],
        outputs=[scraped_output, classification_row, scraped_issues]
    )
    
    model_dropdown.change(
        update_model_choices,
        inputs=[model_dropdown],
        outputs=[base_model_dropdown, ollama_controls, pull_status]
    )
    
    pull_button.click(
        pull_model,
        inputs=[base_model_dropdown],
        outputs=[pull_status]
    )
    
    classify_button.click(
        classify_and_display,
        inputs=[scraped_issues, model_dropdown, base_model_dropdown, pull_status],
        outputs=classified_output
    )

if __name__ == "__main__":
    iface.launch()