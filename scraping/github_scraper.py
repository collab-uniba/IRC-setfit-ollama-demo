# define the scrape_github_issues function
from typing import List
from github import Github
from loguru import logger

# Define an issue object
class Issue:
    def __init__(self, title: str, body: str, url: str):
        self.title = title
        self.body = body
        self.url = url
        self.classification = None
        self.reasoning = None
    
    def __str__(self):
        url = f"URL: {self.url}\n\n" if self.url else ""
        if not self.classification:
            return f"{url}Title: {self.title}\n\nBody: {self.body}"
        if self.reasoning:
            return f"{url}Classification: {self.classification}\n\nReasoning: {self.reasoning}"
        else:
            return f"{url}Classification: {self.classification}"


def validate_github_url(url: str) -> bool:
    """
    Uses GitHub API to validate the URL, for both issue and repository URLs
    """
    g = Github()
    try:
        if "issues" in url and url.split("/")[-1].isdigit():
            issue = g.get_repo(url).get_issue(int(url.split("/")[-1]))
        else:
            org_name = url.split("/")[3]
            repo_name = url.split("/")[4]
            repo = g.get_repo(f"{org_name}/{repo_name}")
    except Exception:
        return False

    return True


def scrape_github_issues(url: str, num_issues: int = 5, state: str = 'all') -> List[str]:
    """
    Scrapes GitHub issues from an URL
    If the url is a repository URL, it will scrape the issues from the repository
    If the url is an issue URL, it will scrape the issue details
    """
    # Initialize the Github object
    g = Github()
    
    org_name = url.split("/")[3]
    repo_name = url.split("/")[4]
    
    # Check if the URL is an issue URL
    if "issues" in url and url.split("/")[-1].isdigit():
        logger.info(f"Scraping issue from {url}")
        issue_number = int(url.split("/")[-1])

        repo = g.get_repo(f"{org_name}/{repo_name}")
        issue = repo.get_issue(issue_number)
        url = issue.html_url
        return Issue(issue.title, issue.body, url)
    
    # Scrape the issues and return the latest num_issues issues
    repo = g.get_repo(f"{org_name}/{repo_name}")
    issues = repo.get_issues(state=state, sort='created', direction='desc')
    issue_list = []
    for issue in issues[:num_issues]:
        issue_list.append(Issue(issue.title, issue.body, issue.html_url))
    
    return issue_list

if __name__ == "__main__":
    url = "https://github.com/PyGithub/PyGithub/issues/3064"
    issues = scrape_github_issues(url)
    for issue in issues:
        print(issue)
    