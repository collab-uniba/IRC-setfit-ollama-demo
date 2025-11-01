import gradio as gr
from dataclasses import dataclass
from typing import List, Union, Tuple
import re
import requests
from scraping.github_scraper import scrape_github_issues
from common.issue import Issue
from llm_model import llm_classify, pull_ollama_model
from model_config import ModelConfigLoader
from label_config_manager import get_label_manager
from loguru import logger
import os

model_loader = ModelConfigLoader()
SETFIT_HOST = os.getenv('SETFIT_BASE_URL', 'http://localhost:8000')

def validate_github_url(url: str) -> Tuple[bool, str, str]:
    """Validates GitHub URL and determines if it's an issue or project URL"""
    if not url:
        return False, "Invalid", "Please enter a URL"

    # GitHub URL patterns
    issue_pattern = r'https?://github\.com/[\w-]+/[\w-]+/issues/\d+'
    project_pattern = r'https?://github\.com/[\w-]+/[\w-]+'
    org_and_project_pattern = r'https?://github\.com/([\w-]+)/([\w-]+)'
    if re.match(issue_pattern, url):
        org_and_project_match = re.search(org_and_project_pattern, url)
        org_and_project_name = f"{org_and_project_match[1]}/{org_and_project_match[2]}"
        issue_number_pattern = r'https?://github\.com/[\w-]+/[\w-]+/issues/(\d+)'

        return (
            True,
            "issue",
            f"Valid issue URL,\nProject: {org_and_project_name}\nIssue Number: {re.search(issue_number_pattern, url)[1]}",
        )
    elif re.match(project_pattern, url):
        org_and_project_match = re.search(org_and_project_pattern, url)
        org_and_project_name = f"{org_and_project_match[1]}/{org_and_project_match[2]}"
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
        return output, gr.update(visible=True), [result]
    else:
        return "No issues found", gr.update(visible=False), []

def process_manual_issue(title: str, body: str) -> Tuple[str, gr.update, List[Issue]]:
    """Process manually entered issue"""
    if not title or not body:
        return "Please enter both title and body", gr.update(visible=False), []
    
    issue = Issue(
        title=title,
        body=body,
        url=None
    )
    
    output = str(issue) + "\n"
    return output, gr.update(visible=True), [issue]

def update_input_visibility(input_type: str):
    """Updates visibility of input controls based on selected input type"""
    if input_type == "Scrape":
        return [
            gr.update(visible=True),   # url_row
            gr.update(visible=False),  # manual_input_row
            gr.update(visible=False),  # manual_submit
            gr.update(visible=True),   # url_components
            gr.update(visible=True),   # url_status
            gr.update(visible=False),  # project_controls
        ]
    else:  # manual
        return [
            gr.update(visible=False),  # url_row
            gr.update(visible=True),   # manual_input_row
            gr.update(visible=True),   # manual_submit
            gr.update(visible=False),  # url_components
            gr.update(visible=False),  # url_status
            gr.update(visible=False),  # project_controls
        ]

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

    if model_type == "ollama":
        return llm_classify(issues, base_model=base_model)

    elif model_type == "setfit":
        # Convert issues to the format expected by the API
        api_issues = [{"title": issue.title, "body": issue.body} for issue in issues]

        try:
            response = requests.post(
                f"{SETFIT_HOST}/classify",
                json={
                    "issues": api_issues,
                    "model_name": base_model
                }
            )
            response.raise_for_status()
            classified_issues = response.json()

            # Update the original issues with classifications
            for issue, classified in zip(issues, classified_issues):
                issue.classification = classified["classification"]
                issue.reasoning = None

            return issues
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling SetFit API: {str(e)}")
            raise Exception(f"Failed to classify issues using SetFit API: {str(e)}") from e

    return issues

def classify_and_display(issues: List[Tuple], model: str, base_model: str, pull_status: str) -> str:
    if model == "ollama" and pull_status != "Model pulled successfully!":
        return "Please pull the Ollama model first before classification."
    
    try:
        classified_issues = classify_issues(issues, model, base_model)
        output = "Classified Issues:\n\n"
        for issue in classified_issues:
            output += str(issue) + "\n"
            output += f"{'-'*50}\n"
        return output
    except Exception as e:
        return f"Classification error: {str(e)}"

async def update_model_choices(model_choice: str):
    if model_choice == "setfit":
        try:
            # Get available models from the API
            response = requests.get(f"{SETFIT_HOST}/models")
            response.raise_for_status()
            models_info = response.json()
            available_models = [model["path"] for model in models_info["available_models"]]
            default_model = models_info["default_model"]
            
            return [
                gr.update(
                    visible=True,
                    choices=available_models,
                    value=default_model,
                    label="Select SetFit Base Model"
                ),
                gr.update(visible=False),
                gr.update(visible=False)
            ]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching SetFit models: {str(e)}")
            # Fallback to config file
            return [
                gr.update(
                    visible=True,
                    choices=model_loader.get_model_choices("setfit"),
                    value=model_loader.get_default_model("setfit"),
                    label="Select SetFit Base Model"
                ),
                gr.update(visible=False),
                gr.update(visible=False)
            ]
    else:  # ollama
        return [
            gr.update(
                visible=True,
                choices=model_loader.get_model_choices("ollama"),
                value=model_loader.get_default_model("ollama"),
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

# Label management functions
def get_labels_dataframe():
    """Get labels as a list of lists for Gradio dataframe."""
    label_manager = get_label_manager()
    labels = label_manager.read_labels()
    return [[label['name'], label['description']] for label in labels]

def add_new_label(name: str, description: str) -> Tuple[List[List[str]], str]:
    """Add a new label to the configuration."""
    if not name or not description:
        return get_labels_dataframe(), "Error: Both name and description are required"
    
    try:
        label_manager = get_label_manager()
        label_manager.add_label(name.strip(), description.strip())
        return get_labels_dataframe(), f"Label '{name}' added successfully!"
    except Exception as e:
        return get_labels_dataframe(), f"Error: {str(e)}"

def update_label(old_name: str, new_name: str, new_description: str) -> Tuple[List[List[str]], str]:
    """Update an existing label."""
    if not old_name or not new_name or not new_description:
        return get_labels_dataframe(), "Error: All fields are required"
    
    try:
        label_manager = get_label_manager()
        label_manager.update_label(old_name.strip(), new_name.strip(), new_description.strip())
        return get_labels_dataframe(), f"Label '{old_name}' updated successfully!"
    except Exception as e:
        return get_labels_dataframe(), f"Error: {str(e)}"

def delete_label(name: str) -> Tuple[List[List[str]], str]:
    """Delete a label from the configuration."""
    if not name:
        return get_labels_dataframe(), "Error: Label name is required"
    
    try:
        label_manager = get_label_manager()
        label_manager.delete_label(name.strip())
        return get_labels_dataframe(), f"Label '{name}' deleted successfully!"
    except Exception as e:
        return get_labels_dataframe(), f"Error: {str(e)}"

def populate_edit_fields(evt: gr.SelectData, labels_data: List[List[str]]) -> Tuple[str, str, str]:
    """Populate edit fields when a row is selected from the labels table."""
    if evt.index is not None and evt.index[0] < len(labels_data):
        row_data = labels_data[evt.index[0]]
        return row_data[0], row_data[0], row_data[1]  # old_name, new_name, new_description
    return "", "", ""

with gr.Blocks() as iface:
    gr.Markdown("# GitHub Issue/Project Scraper and Classifier")
    
    # Label Management Section
    with gr.Accordion("Label Management", open=False):
        gr.Markdown("### Manage Classification Labels")
        gr.Markdown("Configure the labels used for issue classification. Changes are saved immediately and will be used in the next classification.")
        
        # Display current labels
        labels_table = gr.Dataframe(
            headers=["Label Name", "Description"],
            value=get_labels_dataframe(),
            label="Current Labels",
            interactive=False,
            wrap=True
        )
        
        # Add new label
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Add New Label")
                new_label_name = gr.Textbox(label="Label Name", placeholder="e.g., feature-request")
                new_label_description = gr.Textbox(
                    label="Description", 
                    placeholder="Describe what this label represents...",
                    lines=3
                )
                add_label_btn = gr.Button("Add Label", variant="primary")
        
        # Edit existing label
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Edit Label (click a row above to populate fields)")
                edit_old_name = gr.Textbox(label="Current Label Name", interactive=False)
                edit_new_name = gr.Textbox(label="New Label Name")
                edit_description = gr.Textbox(label="New Description", lines=3)
                with gr.Row():
                    update_label_btn = gr.Button("Update Label", variant="secondary")
                    delete_label_btn = gr.Button("Delete Label", variant="stop")
        
        # Status message for label operations
        label_status = gr.Textbox(label="Status", interactive=False, value="")
    
    # Input type selector
    input_type = gr.Radio(
        choices=["Scrape", "Manual"],
        value="Scrape",
        label="Select Input Type",
        info="Choose whether to input a GitHub URL or manually enter an issue"
    )
    
    # URL input components
    with gr.Row(visible=True) as url_row:
        url_input = gr.Textbox(label="Enter GitHub URL")
    
    # Manual input components
    with gr.Row(visible=False) as manual_input_row:
        with gr.Column():
            issue_title = gr.Textbox(label="Issue Title")
            issue_body = gr.Textbox(label="Issue Body", lines=5)
    
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
            value=5,
            step=1,
            label="Number of Issues to Scrape"
        )
        issue_state = gr.Dropdown(
            choices=["open", "closed", "all"],
            value="all",
            label="Issue State"
        )
    
    with gr.Row() as url_components:
        scrape_button = gr.Button("Scrape")
    
    with gr.Row(visible=False) as manual_submit:
        submit_button = gr.Button("Submit Issue")
    
    scraped_output = gr.Textbox(label="Result")
    
    with gr.Row(visible=False) as classification_row:
        with gr.Column():
            model_dropdown = gr.Dropdown(
                choices=["setfit", "ollama"],
                label="Select Classification Model",
                value="setfit"
            )
            
            base_model_dropdown = gr.Dropdown(
                choices=model_loader.get_model_choices("setfit"),
                label="Select SetFit Base Model",
                value=model_loader.get_default_model("setfit"),
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
    input_type.change(
        update_input_visibility,
        inputs=[input_type],
        outputs=[url_row, manual_input_row, manual_submit, url_components, url_status, project_controls]
    )
    
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
    
    submit_button.click(
        process_manual_issue,
        inputs=[issue_title, issue_body],
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
    
    # Label management event handlers
    labels_table.select(
        populate_edit_fields,
        inputs=[labels_table],
        outputs=[edit_old_name, edit_new_name, edit_description]
    )
    
    add_label_btn.click(
        add_new_label,
        inputs=[new_label_name, new_label_description],
        outputs=[labels_table, label_status]
    )
    
    update_label_btn.click(
        update_label,
        inputs=[edit_old_name, edit_new_name, edit_description],
        outputs=[labels_table, label_status]
    )
    
    delete_label_btn.click(
        delete_label,
        inputs=[edit_old_name],
        outputs=[labels_table, label_status]
    )

if __name__ == "__main__":   
    # Launch with specific parameters to make URL accessible from Docker
    iface.launch(
        server_name="0.0.0.0",  # Bind to all network interfaces
        server_port=7860,
        share=False,  # Set to True if you want a public URL
        show_error=True,
        quiet=False,  # This ensures the URL is printed
    )