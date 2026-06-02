"""State Schema 测试"""
import pytest
from backend.orchestrator.state import create_initial_state, SmartEyeState


class TestCreateInitialState:
    """初始状态创建"""

    def test_creates_with_required_fields(self):
        """初始状态应包含所有必需字段"""
        state = create_initial_state(task_id="test123", task_type="inspection")
        assert state["task_id"] == "test123"
        assert state["task_type"] == "inspection"
        assert state["status"] == "pending"
        assert state["next_agent"] == "supervisor"
        assert state["alert_triggered"] is False
        assert state["error"] is None
        assert state["detections"] is None
        assert state["retry_count"] == 0
        assert state["messages"] == []

    def test_with_image(self):
        """带图像的初始状态"""
        state = create_initial_state(
            task_id="img001",
            task_type="inspection",
            image_b64="fakebase64data",
        )
        assert state["image_b64"] == "fakebase64data"

    def test_with_user_message(self):
        """带用户消息的初始状态"""
        state = create_initial_state(
            task_id="chat001",
            task_type="chat",
            user_message="BGA焊点标准是多少？",
        )
        assert state["user_message"] == "BGA焊点标准是多少？"

    def test_all_task_types(self):
        """各种任务类型"""
        for ttype in ["inspection", "analysis", "report", "chat"]:
            state = create_initial_state(task_id=ttype, task_type=ttype)
            assert state["task_type"] == ttype


class TestStateSchema:
    """State 类型系统"""

    def test_is_typeddict(self):
        """确认是 TypedDict"""
        from typing import get_type_hints
        hints = get_type_hints(SmartEyeState)
        assert "task_id" in hints
        assert "detections" in hints
        assert "messages" in hints
        assert "next_agent" in hints

    def test_optional_fields_default_none(self):
        """可选字段默认为 None"""
        state = create_initial_state(task_id="test")
        for field in ["image_b64", "detections", "analysis_results",
                       "report_markdown", "alert_message"]:
            assert state[field] is None, f"{field} should be None"
