"""
Workflow Engine — runs declarative multi-step tool chains defined in config.
"""

from __future__ import annotations

import logging
import re
from typing import Any, TYPE_CHECKING

from torii.config import WorkflowConfig

if TYPE_CHECKING:
    from torii.mcp.gateway import ToriiGateway

logger = logging.getLogger(__name__)

_TEMPLATE_RE = re.compile(r"\{\{([^}]+)\}\}")


def _resolve(value: Any, context: dict[str, Any]) -> Any:
    """Replace {{key.subkey}} templates in a value using the step output context."""
    if not isinstance(value, str):
        return value

    def replace(match: re.Match) -> str:
        expr = match.group(1).strip()
        parts = expr.split(".")
        current: Any = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, match.group(0))
            else:
                return match.group(0)
        return str(current)

    return _TEMPLATE_RE.sub(replace, value)


def _resolve_dict(d: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Recursively resolve templates in all values of a dict."""
    return {k: _resolve(v, context) for k, v in d.items()}


class WorkflowEngine:
    """
    Runs named workflows by sequentially calling tools and
    passing outputs from earlier steps into later ones via {{step_id.output}} templates.
    """

    def __init__(self, gateway: "ToriiGateway") -> None:
        self._gateway = gateway
        self._workflows: dict[str, WorkflowConfig] = {}

    def register(self, wf: WorkflowConfig) -> None:
        """Register a workflow definition."""
        self._workflows[wf.name] = wf
        logger.info(f"[workflow] '{wf.name}' registered ({len(wf.steps)} steps)")

    async def run(self, name: str, input_params: dict[str, Any] | None = None) -> str:
        """
        Execute a workflow by name.

        Step outputs are stored in a context dict keyed by step ID.
        Templates like {{fetch_prs.output}} are resolved before each step runs.
        """
        wf = self._workflows.get(name)
        if not wf:
            return f"Error: workflow '{name}' not found"

        context: dict[str, Any] = {
            "input": input_params or {},
        }

        logger.info(f"[workflow:{name}] Starting ({len(wf.steps)} steps)")

        for step in wf.steps:
            logger.debug(f"[workflow:{name}] Step '{step.id}' → tool '{step.tool}'")

            # Resolve template variables in step inputs
            resolved_input = _resolve_dict(step.input, context)

            # Call the tool
            try:
                output = await self._gateway.call_tool(step.tool, resolved_input)
            except Exception as e:
                error_msg = f"Step '{step.id}' failed: {e}"
                logger.error(f"[workflow:{name}] {error_msg}")
                return f"Error: {error_msg}"

            # Store output for subsequent steps
            context[step.id] = {"output": output}
            logger.debug(f"[workflow:{name}] Step '{step.id}' completed")

        logger.info(f"[workflow:{name}] Completed successfully")

        # Return the output of the last step
        if wf.steps:
            last = wf.steps[-1]
            return context.get(last.id, {}).get("output", "Workflow completed")

        return "Workflow completed (no steps)"

    def list_workflows(self) -> list[str]:
        return list(self._workflows.keys())
