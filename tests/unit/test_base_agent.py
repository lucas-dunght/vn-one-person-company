from core.agents.base_agent import BaseAgent
from unittest.mock import MagicMock


def test_base_agent_speak_calls_llm():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "Tôi đồng ý phương án A vì..."

    agent = BaseAgent(
        name_vn="Test Agent",
        role="tester",
        system_prompt="Bạn là chuyên viên test.",
        llm=mock_llm,
    )

    response = agent.speak(
        brief="Test brief",
        brain_context={"strategy": "..."},
        history=[],
    )

    assert "đồng ý" in response
    mock_llm.complete.assert_called_once()


def test_base_agent_includes_brain_in_prompt():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "ok"

    agent = BaseAgent(name_vn="A", role="r", system_prompt="sys", llm=mock_llm)
    agent.speak(brief="b", brain_context={"strategy": "VN"}, history=[])

    # Verify brain_context được inject
    call_args = mock_llm.complete.call_args
    messages = call_args[0][0] if call_args[0] else call_args.kwargs["messages"]
    full_text = str(messages)
    assert "VN" in full_text
