"""Tests for the workflow engine."""

import pytest
from unittest.mock import AsyncMock

from torii.workflow import WorkflowEngine
from torii.config import WorkflowConfig, StepConfig


def make_workflow(steps: list[dict]) -> WorkflowConfig:
    return WorkflowConfig(
        name="test-workflow",
        description="A test workflow",
        steps=[StepConfig(**s) for s in steps],
    )


class FakeGateway:
    """Minimal gateway stub for testing the workflow engine."""

    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, params: dict) -> str:
        self.calls.append((name, params))
        return self.responses.get(name, f"result_of_{name}")


class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_runs_steps_in_order(self):
        gateway = FakeGateway({"tool_a": "output_a", "tool_b": "output_b"})
        engine = WorkflowEngine(gateway)
        wf = make_workflow([
            {"id": "step1", "tool": "tool_a", "input": {}},
            {"id": "step2", "tool": "tool_b", "input": {}},
        ])
        engine.register(wf)
        result = await engine.run("test-workflow")
        assert gateway.calls[0][0] == "tool_a"
        assert gateway.calls[1][0] == "tool_b"

    @pytest.mark.asyncio
    async def test_template_resolution(self):
        gateway = FakeGateway({"fetch": "hello world"})
        engine = WorkflowEngine(gateway)
        wf = make_workflow([
            {"id": "step1", "tool": "fetch", "input": {}},
            {"id": "step2", "tool": "fetch", "input": {"msg": "{{step1.output}}"}},
        ])
        engine.register(wf)
        await engine.run("test-workflow")
        assert gateway.calls[1][1]["msg"] == "hello world"

    @pytest.mark.asyncio
    async def test_input_available_in_templates(self):
        gateway = FakeGateway({"my_tool": "ok"})
        engine = WorkflowEngine(gateway)
        wf = make_workflow([
            {"id": "s1", "tool": "my_tool", "input": {"val": "{{input.city}}"}},
        ])
        engine.register(wf)
        await engine.run("test-workflow", {"city": "Tokyo"})
        assert gateway.calls[0][1]["val"] == "Tokyo"

    @pytest.mark.asyncio
    async def test_unknown_workflow_returns_error(self):
        engine = WorkflowEngine(FakeGateway({}))
        result = await engine.run("does-not-exist")
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_returns_last_step_output(self):
        gateway = FakeGateway({"a": "first", "b": "final_result"})
        engine = WorkflowEngine(gateway)
        wf = make_workflow([
            {"id": "s1", "tool": "a", "input": {}},
            {"id": "s2", "tool": "b", "input": {}},
        ])
        engine.register(wf)
        result = await engine.run("test-workflow")
        assert result == "final_result"
