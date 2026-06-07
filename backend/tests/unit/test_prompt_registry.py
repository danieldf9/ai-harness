import pytest
from unittest.mock import MagicMock
from onyx.db.prompt_registry import (
    insert_prompt_template,
    update_prompt_template,
    insert_prompt_version,
    set_active_prompt_version,
    upsert_prompt_assignment,
)
from onyx.db.models import PromptTemplate, PromptVersion, PromptAssignment

def test_insert_prompt_template():
    mock_db = MagicMock()
    mock_template = PromptTemplate(id=1, name="test", description="test desc")
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)
    
    t = insert_prompt_template("test", "test desc", None, mock_db)
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert t.name == "test"
    assert t.description == "test desc"

def test_insert_prompt_version():
    mock_db = MagicMock()
    mock_db.scalar.return_value = None # no existing version
    
    v = insert_prompt_version(1, "system prompt content", None, mock_db)
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert v.prompt_template_id == 1
    assert v.content == "system prompt content"
    assert v.version_number == 1
    assert v.is_active == False

def test_set_active_prompt_version():
    mock_db = MagicMock()
    
    v1 = PromptVersion(id=1, prompt_template_id=1, version_number=1, is_active=True)
    v2 = PromptVersion(id=2, prompt_template_id=1, version_number=2, is_active=False)
    
    mock_db.scalar.return_value = v2
    
    set_active_prompt_version(1, 2, mock_db)
    
    # v1 is not tracked by the session in the mock logic, so its state won't change
    # But v2 should be set to active
    assert v2.is_active == True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
