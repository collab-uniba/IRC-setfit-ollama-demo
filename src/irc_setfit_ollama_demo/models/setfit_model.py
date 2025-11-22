from typing import List
from irc_setfit_ollama_demo.common import Issue

def preprocess_issues(issues: List[Issue]) -> List[str]:
    """
    Preprocesses the issues for SetFit model.
    """
    return [f"{issue.title}\n\n{issue.body}" for issue in issues]

def response_postprocess(responses: List[str], issues: List[Issue]) -> List[Issue]:
    """
    Postprocesses the responses from SetFit model.
    """
    for r, i in zip(responses, issues):
        i.classification = r
    return issues
