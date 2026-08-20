"""Conversation Manager & Natural Language Intent Orchestrator."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .state_manager import state_manager, AssistantState
from ..events.event_bus import event_bus
from ..tools.router import tool_router

logger = logging.getLogger("rezane.assistant.conversation")

class ChatMessage(BaseModel):
    id: str
    role: str  # "you", "assistant", "system"
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%I:%M %p"))
    checklist: Optional[List[Dict[str, Any]]] = None
    result_path: Optional[str] = None

class ConversationManager:
    """Orchestrates conversation history, intent parsing, and task execution workflows."""

    def __init__(self):
        self.messages: List[ChatMessage] = [
            ChatMessage(
                id="msg_init_1",
                role="you",
                text="Build ZeGFX renderer and run the visual benchmark.",
                timestamp="10:42 AM"
            ),
            ChatMessage(
                id="msg_init_2",
                role="assistant",
                text="Got it. Building ZeGFX renderer...",
                timestamp="10:42 AM",
                checklist=[
                    {"label": "Configuring project", "status": "done"},
                    {"label": "Compiling shaders", "status": "done"},
                    {"label": "Building renderer", "status": "done"},
                    {"label": "Running visual benchmark...", "status": "done"}
                ]
            ),
            ChatMessage(
                id="msg_init_3",
                role="assistant",
                text="Benchmark completed. Results saved to:",
                timestamp="10:45 AM",
                result_path="tests/results/benchmark_2025-05-18_1045/"
            )
        ]

    def get_history(self) -> List[ChatMessage]:
        return self.messages

    async def handle_user_message(self, text: str) -> ChatMessage:
        user_msg = ChatMessage(
            id=f"msg_{int(datetime.now().timestamp()*1000)}",
            role="you",
            text=text,
            timestamp=datetime.now().strftime("%I:%M %p")
        )
        self.messages.append(user_msg)
        await event_bus.broadcast("chat_message", user_msg.model_dump())

        # Start thinking
        await state_manager.set_state(AssistantState.THINKING, f"Analyzing: '{text}'")
        
        # Async background task to process request and drive execution
        asyncio.create_task(self._process_intent(text))
        return user_msg

    async def _process_intent(self, text: str) -> None:
        t_lower = text.lower().strip()
        await asyncio.sleep(0.4)  # Natural thinking pause

        # Intent: Screenshot
        if "screenshot" in t_lower or "look at my screen" in t_lower:
            await state_manager.set_state(AssistantState.EXECUTING, "Capturing screen...")
            res = await tool_router.execute("take_screenshot")
            path = res.data.get("file_path", "") if res.data else ""
            reply = ChatMessage(
                id=f"msg_{int(datetime.now().timestamp()*1000)}",
                role="assistant",
                text="Screen captured successfully.",
                result_path=path
            )
            self.messages.append(reply)
            await event_bus.broadcast("chat_message", reply.model_dump())
            await state_manager.set_state(AssistantState.IDLE, "Ready.")
            return

        # Intent: Git Status / Check Git
        if "git" in t_lower or "what changed" in t_lower:
            await state_manager.set_state(AssistantState.EXECUTING, "Inspecting Git repository...")
            res = await tool_router.execute("git_status")
            data = res.data or {}
            branch = data.get("branch", "main")
            mod_count = len(data.get("modified", []))
            untr_count = len(data.get("untracked", []))
            
            summary = f"Git status on branch `{branch}`: {mod_count} modified files, {untr_count} untracked files."
            reply = ChatMessage(
                id=f"msg_{int(datetime.now().timestamp()*1000)}",
                role="assistant",
                text=summary
            )
            self.messages.append(reply)
            await event_bus.broadcast("chat_message", reply.model_dump())
            await state_manager.set_state(AssistantState.IDLE, "Ready.")
            return

        # Intent: Build / Benchmark Workflow (Simulated/Controlled task execution)
        if "build" in t_lower or "benchmark" in t_lower:
            step_labels = [
                "Configuring project",
                "Compiling shaders",
                "Building renderer",
                "Running visual benchmark"
            ]
            await state_manager.start_task(
                task_id=f"task_{int(datetime.now().timestamp())}",
                title="Build & Benchmark Workflow",
                step_labels=step_labels
            )

            # Assistant acknowledgement
            ack_msg = ChatMessage(
                id=f"msg_{int(datetime.now().timestamp()*1000)}",
                role="assistant",
                text="Starting build & visual benchmark pipeline...",
                checklist=[{"label": lbl, "status": "pending"} for lbl in step_labels]
            )
            self.messages.append(ack_msg)
            await event_bus.broadcast("chat_message", ack_msg.model_dump())

            # Progressively execute steps
            for idx, label in enumerate(step_labels):
                await state_manager.update_task_step(idx, "running")
                ack_msg.checklist[idx]["status"] = "running"
                await event_bus.broadcast("checklist_update", {"msg_id": ack_msg.id, "checklist": ack_msg.checklist})
                await asyncio.sleep(0.8)

                await state_manager.update_task_step(idx, "done")
                ack_msg.checklist[idx]["status"] = "done"
                await event_bus.broadcast("checklist_update", {"msg_id": ack_msg.id, "checklist": ack_msg.checklist})

            # Task Completion
            res_path = "tests/results/benchmark_latest/"
            await state_manager.complete_task(
                final_message="Build and benchmark finished successfully.",
                output_path=res_path
            )

            completion_msg = ChatMessage(
                id=f"msg_{int(datetime.now().timestamp()*1000)}",
                role="assistant",
                text="Benchmark completed.\nResults saved to:",
                result_path=res_path
            )
            self.messages.append(completion_msg)
            await event_bus.broadcast("chat_message", completion_msg.model_dump())
            return

        # Default general response
        await state_manager.set_state(AssistantState.SPEAKING, "Responding...")
        reply = ChatMessage(
            id=f"msg_{int(datetime.now().timestamp()*1000)}",
            role="assistant",
            text=f"Understood: '{text}'. Monitoring system and ready for next command."
        )
        self.messages.append(reply)
        await event_bus.broadcast("chat_message", reply.model_dump())
        await asyncio.sleep(0.5)
        await state_manager.set_state(AssistantState.IDLE, "Ready.")

conversation_manager = ConversationManager()
