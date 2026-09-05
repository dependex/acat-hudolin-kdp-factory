"""Tests for the pipeline orchestrator."""
from src.orchestrator.state import PipelineState, Stage


def test_initial_state():
    state = PipelineState()
    assert state.current == Stage.IDLE
    assert len(state.history) == 0


def test_state_transition():
    state = PipelineState()
    state.transition(Stage.HARVEST)
    assert state.current == Stage.HARVEST
    assert len(state.history) == 1
    assert state.history[0].stage == Stage.HARVEST
    assert state.history[0].status == "running"


def test_multiple_transitions():
    state = PipelineState()
    state.transition(Stage.HARVEST)
    state.transition(Stage.ASSEMBLE)
    assert state.current == Stage.ASSEMBLE
    assert len(state.history) == 2
    assert state.history[0].status == "done"
    assert state.history[1].status == "running"
