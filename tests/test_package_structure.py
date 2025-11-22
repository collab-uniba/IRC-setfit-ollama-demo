"""
Basic tests to verify package structure and imports.
"""
import sys
import pytest

def test_common_imports():
    """Test that common module imports work."""
    from irc_setfit_ollama_demo.common import Issue
    
    # Test Issue class instantiation
    issue = Issue(title="Test", body="Test body", url="http://example.com")
    assert issue.title == "Test"
    assert issue.body == "Test body"
    assert issue.url == "http://example.com"
    assert issue.classification is None
    assert issue.reasoning is None

def test_config_imports():
    """Test that config module imports work."""
    from irc_setfit_ollama_demo.config import (
        ModelConfigLoader, 
        ModelConfig,
        LabelConfigManager,
        get_label_manager
    )
    
    # Test that classes are available
    assert ModelConfigLoader is not None
    assert ModelConfig is not None
    assert LabelConfigManager is not None
    assert get_label_manager is not None

def test_models_imports():
    """Test that models module imports work."""
    from irc_setfit_ollama_demo.models import (
        llm_classify,
        pull_ollama_model,
        preprocess_issues,
        response_postprocess
    )
    
    # Test that functions are available
    assert callable(llm_classify)
    assert callable(pull_ollama_model)
    assert callable(preprocess_issues)
    assert callable(response_postprocess)

def test_scraping_imports():
    """Test that scraping module imports work."""
    from irc_setfit_ollama_demo.scraping import (
        scrape_github_issues,
        validate_github_url
    )
    
    # Test that functions are available
    assert callable(scrape_github_issues)
    assert callable(validate_github_url)

def test_issue_string_representation():
    """Test Issue __str__ method."""
    from irc_setfit_ollama_demo.common import Issue
    
    # Test without classification
    issue = Issue(title="Bug", body="Something broke", url="http://example.com")
    str_repr = str(issue)
    assert "Bug" in str_repr
    assert "Something broke" in str_repr
    assert "http://example.com" in str_repr
    
    # Test with classification
    issue.classification = "bug"
    str_repr = str(issue)
    assert "bug" in str_repr
    
    # Test with reasoning
    issue.reasoning = "This is a bug report"
    str_repr = str(issue)
    assert "This is a bug report" in str_repr

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
