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
