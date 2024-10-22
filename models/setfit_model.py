from setfit import SetFitModel
from typing import List
from scraping.github_scraper import Issue

def preprocess_issues(issues: List[Issue]):
    """
    Preprocesses the issues for SetFit model.
    """
    if not isinstance(issues, list):
        issues = [issues]
    return [f"{issue.title}\n\n{issue.body}" for issue in issues]

def response_postprocess(responses: List[str], issues: List[Issue]):
    """
    Postprocesses the responses from SetFit model.
    """
    for r, i in zip(responses, issues):
        i.classification = r
    return issues

def setfit_classify(issues: List[Issue], base_model: str = "Collab-uniba/cfs-binary-setfit"):
    """
    Classifies the issues using the SetFit model.
    """
    p_issues = preprocess_issues(issues)
    model = SetFitModel.from_pretrained(base_model)
    responses = model.predict(p_issues)
    return response_postprocess(responses, issues)

