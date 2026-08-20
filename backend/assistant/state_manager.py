"""Assistant Finite State Machine & Lifecycle Management."""
import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ..events.event_bus import event_bus

logger = logging.getLogger("rezane.assistant.state")

class AssistantState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    WAITING = "WAITING"
    ERROR = "ERROR"

class TaskStep(BaseModel):
    id: str
    label: str
    status: str = "pending"  # "pending", "running", "done", "failed"
    detail: Optional[str] = None

class ActiveTask(BaseModel):
    task_id: str
    title: str
    progress: int = 0  # 0 to 100
    steps: List[TaskStep] = Field(default_factory=list)
    output_path: Optional[str] = None

class AssistantStatus(BaseModel):
    current_state: AssistantState = AssistantState.IDLE
    previous_state: Optional[AssistantState] = None
    status_text: str = "Ready and waiting for instructions."
    active_task: Optional[ActiveTask] = None
    last_error: Optional[str] = None

class StateManager:
    """Manages the current runtime state of Rezane AI and broadcasts updates."""
    
    def __init__(self):
        self._status = AssistantStatus()
        self._lock = asyncio.Lock()

    @property
    def status(self) -> AssistantStatus:
        return self._status

    async def set_state(
        self,
        new_state: AssistantState,
        status_text: Optional[str] = None,
        error_msg: Optional[str] = None
    ) -> AssistantStatus:
        async with self._lock:
            self._status.previous_state = self._status.current_state
            self._status.current_state = new_state
            if status_text is not None:
                self._status.status_text = status_text
            if error_msg is not None:
                self._status.last_error = error_msg
            elif new_state != AssistantState.ERROR:
                self._status.last_error = None
            
            logger.info(f"State transition: {self._status.previous_state} -> {self._status.current_state} ({self._status.status_text})")
            
        await self._broadcast_status()
        return self._status

    async def start_task(self, task_id: str, title: str, step_labels: List[str]) -> ActiveTask:
        async with self._lock:
            steps = [
                TaskStep(id=f"step_{idx}", label=label, status="pending")
                for idx, label in enumerate(step_labels)
            ]
            task = ActiveTask(task_id=task_id, title=title, steps=steps, progress=0)
            self._status.active_task = task
            self._status.current_state = AssistantState.EXECUTING
            self._status.status_text = f"Executing: {title}"
        
        await self._broadcast_status()
        return task

    async def update_task_step(self, step_index: int, status: str, detail: Optional[str] = None, progress: Optional[int] = None) -> None:
        async with self._lock:
            if not self._status.active_task or step_index >= len(self._status.active_task.steps):
                return
            
            step = self._status.active_task.steps[step_index]
            step.status = status
            if detail is not None:
                step.detail = detail
            
            if progress is not None:
                self._status.active_task.progress = progress
            else:
                completed = sum(1 for s in self._status.active_task.steps if s.status == "done")
                total = len(self._status.active_task.steps)
                if total > 0:
                    self._status.active_task.progress = int((completed / total) * 100)

        await self._broadcast_status()

    async def complete_task(self, final_message: str = "Task completed.", output_path: Optional[str] = None) -> None:
        async with self._lock:
            if self._status.active_task:
                self._status.active_task.progress = 100
                self._status.active_task.output_path = output_path
                for s in self._status.active_task.steps:
                    if s.status == "running":
                        s.status = "done"
            self._status.current_state = AssistantState.IDLE
            self._status.status_text = final_message
            
        await self._broadcast_status()

    async def _broadcast_status(self) -> None:
        await event_bus.broadcast("state_change", self._status.model_dump())

state_manager = StateManager()
