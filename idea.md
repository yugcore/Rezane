# Personal AI Assistant --- Project Idea

## 1. Project Overview

This project is a **personal desktop AI assistant designed to live on a
dedicated second monitor**.

The goal is not to build another chatbot window. The goal is to build a
persistent, voice-first, visually present assistant that can:

-   Listen to the user.
-   Speak naturally.
-   Understand natural-language requests.
-   Maintain useful context and memory.
-   Observe the computer when explicitly asked.
-   Interact with the operating system through controlled tools.
-   Launch and control applications.
-   Work with files and folders.
-   Execute development workflows.
-   Inspect terminals and command output.
-   Understand Git repositories and status.
-   Provide text responses when voice is inconvenient.
-   Perform multi-step tasks.
-   Show its current activity and status on a dedicated display.
-   Eventually act as a general-purpose personal computer companion.

The assistant should be **local-first**, with its interface and control
services exposed primarily through `localhost`.

The second monitor becomes the assistant's permanent visual workspace
while the first monitor remains the user's normal workstation.

------------------------------------------------------------------------

# 2. Core Vision

The intended experience is:

> The assistant is always there, understands what is happening on the
> computer, can talk with the user naturally, and can perform useful
> actions without requiring the user to manually navigate every
> application.

The assistant should feel more like a **desktop operating layer** than a
conventional AI chat application.

The user should be able to say things such as:

-   "Open Visual Studio."
-   "What windows do I have open?"
-   "Build ZeGFX."
-   "Run the visual benchmark."
-   "What's wrong with this build?"
-   "Look at my screen."
-   "Open the results."
-   "Check Git."
-   "What changed since yesterday?"
-   "Create a folder for this."
-   "Open the documentation."
-   "Run the tests."
-   "Why did the build fail?"
-   "Summarize what happened."
-   "Close the terminal."
-   "Put the browser on the right monitor."

The assistant should combine **conversation, perception, reasoning, and
controlled execution**.

------------------------------------------------------------------------

# 3. Two-Monitor Concept

## Monitor 1 --- Primary Workstation

The primary monitor remains the normal working environment.

Typical applications:

-   IDE
-   Visual Studio / VS Code
-   Unreal Engine
-   Godot / custom engine tools
-   Terminal
-   Browser
-   Documentation
-   File Explorer
-   Games
-   Development utilities

The assistant should not unnecessarily take over this monitor.

## Monitor 2 --- Assistant Display

The second monitor is dedicated to the assistant.

It continuously displays:

-   Assistant live state.
-   Quick Launch.
-   Current active windows.
-   Git status.
-   Embedded browser.
-   AI text output.
-   Conversation history.
-   Task progress.
-   System activity.

The interface should be useful even when the user is not actively
talking to the assistant.

------------------------------------------------------------------------

# 4. Interface Layout

The UI is based on a six-region layout with a central assistant
indicator.

``` text
┌───────────────────────────────┐       ┌───────────────────────────────┐
│                               │       │                               │
│        QUICK LAUNCH           │       │           BROWSER             │
│                               │       │                               │
├───────────────────────────────┤       ├───────────────────────────────┤
│                               │       │                               │
│       ACTIVE WINDOWS          │       │                               │
│                               │       │          AI OUTPUT            │
│                               │       │                               │
├───────────────────────────────┤       │                               │
│                               │       │                               │
│         GIT STATUS            │       │                               │
│                               │       │                               │
└───────────────────────────────┘       └───────────────────────────────┘

                         ┌─────────────┐
                         │             │
                         │ AI IS LIVE  │
                         │             │
                         └─────────────┘
```

The exact visual implementation can evolve, but the functional regions
should remain.

------------------------------------------------------------------------

# 5. Central AI Live Indicator

The central circle is the visual identity of the assistant.

Its primary purpose is to show that the assistant is alive and indicate
its current state.

Possible states:

### Idle

The assistant is available but not actively listening.

### Listening

The microphone is active and speech is being captured.

### Thinking

The assistant is processing a request.

### Speaking

The assistant is generating or playing speech.

### Executing

The assistant is performing a computer action.

### Waiting

The assistant is waiting for an external operation such as a build,
download, or process.

### Error

An operation failed and requires attention.

The indicator should use animation rather than excessive text.

Example state model:

``` text
IDLE
  ↓
LISTENING
  ↓
PROCESSING
  ↓
PLANNING
  ↓
EXECUTING
  ↓
COMPLETED
  ↓
IDLE
```

------------------------------------------------------------------------

# 6. Quick Launch Panel

The top-left panel is a launcher for commonly used applications, files,
projects, commands, and assistant actions.

It should support:

-   Application launch.
-   Project launch.
-   File launch.
-   Folder launch.
-   Terminal launch.
-   Custom commands.
-   Search.
-   Recently used items.
-   Pinned items.

Example entries:

-   VS Code
-   Visual Studio
-   Terminal
-   ZeGFX Editor
-   Unreal Engine
-   Godot
-   File Explorer
-   Browser

The launcher should eventually support natural-language search.

For example:

> "Open the ZeGFX renderer."

The assistant can identify the relevant executable/project
automatically.

------------------------------------------------------------------------

# 7. Active Windows Panel

The left-middle panel shows the applications and windows currently
active on the computer.

For every window, useful information can include:

-   Application name.
-   Window title.
-   Process.
-   Project/folder path when available.
-   Monitor.
-   Window position.
-   Current state.
-   Application category.

Actions:

-   Focus.
-   Minimize.
-   Maximize.
-   Move.
-   Resize.
-   Close.
-   Move to another monitor.
-   Group related windows.

Example:

``` text
Visual Studio Code
ZeGFX Renderer
D:\Zelyn\ZeGFX

PowerShell
D:\Zelyn\ZeGFX

Unreal Editor
D:\Unreal\EmberWalk
```

The assistant can then understand requests such as:

> "Bring the ZeGFX window to the front."

or:

> "Move Unreal to the second monitor."

------------------------------------------------------------------------

# 8. Git Status Panel

The bottom-left panel provides a live Git overview.

It should support:

-   Current repository.
-   Current branch.
-   Ahead/behind status.
-   Modified files.
-   Added files.
-   Deleted files.
-   Untracked files.
-   Staged files.
-   Commit history.
-   Diff summary.
-   Pull/push status.

Possible actions:

-   Stage files.
-   Unstage files.
-   Commit.
-   Pull.
-   Push.
-   Create branch.
-   Switch branch.
-   View diff.
-   Open changed file.

The assistant should be able to reason over Git status.

Example:

> "What changed?"

The assistant could inspect the current repository and summarize the
changes.

Potentially:

> "You have three modified files and two untracked files. The renderer
> and G-buffer pass were modified."

Git operations that can cause data loss should require confirmation.

------------------------------------------------------------------------

# 9. Embedded Browser Panel

The top-right panel is a small browser integrated directly into the
assistant interface.

Purpose:

-   Search documentation.
-   Open GitHub.
-   Browse technical references.
-   Read web pages.
-   Search Stack Overflow.
-   Open project documentation.
-   Look up APIs.
-   View online resources without switching applications.

Features:

-   Address/search bar.
-   Back.
-   Forward.
-   Refresh.
-   Tabs.
-   Bookmarks.
-   Search.
-   Basic navigation controls.

The browser can eventually be controlled by the assistant.

Example:

> "Look up the DirectX 12 documentation for descriptor heaps."

The assistant could open the relevant page in this panel.

The assistant should not silently submit forms, make purchases, upload
files, or perform sensitive web actions without explicit authorization.

------------------------------------------------------------------------

# 10. AI Output Panel

The bottom-right panel is the assistant's textual communication area.

Voice is the primary interface, but text is necessary for:

-   Long answers.
-   Code.
-   Logs.
-   Errors.
-   Build output.
-   Structured information.
-   URLs.
-   File paths.
-   Technical explanations.
-   Persistent task history.

The panel should support:

-   User messages.
-   Assistant responses.
-   Timestamps.
-   Tool activity.
-   Task progress.
-   Expandable output.
-   Copy.
-   Clear.
-   Pin.
-   Search.
-   Markdown.
-   Code blocks.

Example:

``` text
You:
Build ZeGFX and run the visual benchmark.

Assistant:
Got it.

✓ Configuring project
✓ Compiling shaders
✓ Building renderer
✓ Running visual benchmark

Benchmark completed.

Results:
castle_vista_day       PASS
forest_road             PASS
material_lab            PASS
interior_gi_room        WARNING
night_emissive           PASS
```

------------------------------------------------------------------------

# 11. Voice System

Voice should be a first-class interface.

Pipeline:

``` text
Microphone
    ↓
Voice Activity Detection
    ↓
Speech-to-Text
    ↓
Assistant Core
    ↓
Response Generation
    ↓
Text-to-Speech
    ↓
Speakers
```

Requirements:

-   Low latency.
-   Natural speech recognition.
-   Streaming transcription where possible.
-   Voice activity detection.
-   Interruption support.
-   Speech cancellation.
-   Natural text-to-speech.
-   Optional wake word.
-   Conversation mode.

Possible modes:

### Passive Mode

Assistant waits silently.

### Wake Word Mode

User activates it with a wake phrase.

### Conversation Mode

The assistant remains engaged for a short conversational session without
requiring repeated activation.

### Push-to-Talk

A keyboard shortcut activates listening.

------------------------------------------------------------------------

# 12. Vision / Screen Understanding

The assistant should eventually be able to inspect the computer screen.

The user could say:

> "Look at my screen."

The assistant can capture the relevant screen/window and analyze it.

Potential uses:

-   Identify compiler errors.
-   Understand application state.
-   Read dialogs.
-   Inspect UI problems.
-   Analyze screenshots.
-   Read logs.
-   Understand game/editor scenes.
-   Help troubleshoot software.

The vision system should preferably operate on-demand rather than
continuously capturing the user's screen without reason.

Possible architecture:

``` text
Screen Capture
      ↓
Image Processing
      ↓
OCR / Vision Model
      ↓
Context Extraction
      ↓
Assistant Core
```

------------------------------------------------------------------------

# 13. OS Interaction Layer

The most important technical subsystem is the controlled
operating-system tool layer.

The assistant should never receive unrestricted access to the OS.

Instead, it should use explicit tools.

Example:

``` text
open_application(name)

close_application(name)

focus_window(id)

move_window(id, monitor)

resize_window(id, dimensions)

open_file(path)

open_folder(path)

create_file(path, content)

create_folder(path)

move_file(source, destination)

copy_file(source, destination)

delete_file(path)

run_command(command)

get_terminal_output(process)

read_clipboard()

write_clipboard(text)

take_screenshot()

type_text(text)

press_key(key)

hotkey(keys)
```

The exact tool set should grow gradually.

------------------------------------------------------------------------

# 14. Tool Permission System

Every OS action should have a permission level.

## Level 0 --- Read Only

No confirmation required.

Examples:

-   Read active windows.
-   Read Git status.
-   Read clipboard.
-   Read directory contents.
-   Take screenshot.
-   Inspect process state.

## Level 1 --- Low Risk

Usually automatic.

Examples:

-   Open application.
-   Focus window.
-   Open folder.
-   Open documentation.
-   Move a window.

## Level 2 --- Potentially Destructive

Require confirmation.

Examples:

-   Delete files.
-   Overwrite project files.
-   Run potentially destructive Git commands.
-   Install software.
-   Modify configuration.

## Level 3 --- High Risk

Always require explicit confirmation.

Examples:

-   Administrator operations.
-   Disk operations.
-   System configuration.
-   Mass deletion.
-   Security-sensitive changes.

The assistant should clearly state what it is about to do before
requesting confirmation.

------------------------------------------------------------------------

# 15. Localhost Architecture

The application should be designed around localhost communication.

Example:

``` text
Frontend
localhost:3000

Assistant Backend
localhost:8000

WebSocket Events
ws://127.0.0.1:8000/events
```

The backend becomes the controlled gateway between the UI, AI models,
and the operating system.

Recommended high-level architecture:

``` text
┌─────────────────────────────────────────────┐
│              ASSISTANT DISPLAY              │
│                                             │
│ Quick Launch │ Active Windows │ Git Status  │
│                                             │
│              AI LIVE CORE                   │
│                                             │
│ Browser      │ AI Output                    │
└───────────────────┬─────────────────────────┘
                    │
              localhost
                    │
┌───────────────────▼─────────────────────────┐
│             ASSISTANT BACKEND               │
│                                             │
│ Conversation Manager                        │
│ Memory                                      │
│ Context                                     │
│ Planner                                     │
│ Tool Router                                 │
│ Voice Manager                               │
│ Vision Manager                              │
└───────────────────┬─────────────────────────┘
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
      AI/LLM      Voice        Vision
        │           │            │
        └───────────┼────────────┘
                    │
              Tool Layer
                    │
        ┌───────────┼──────────────┐
        ▼           ▼              ▼
       OS         Files          Developer
      Tools       Tools           Tools
```

------------------------------------------------------------------------

# 16. Native Assistant Host

Although the UI can be a web application, a small native host should run
in the background.

Responsibilities:

-   Microphone access.
-   Speaker access.
-   Global hotkeys.
-   Screen capture.
-   OS window management.
-   Process management.
-   Keyboard/mouse integration.
-   Local tool execution.
-   Startup with Windows.
-   Communication with the localhost backend.

This avoids giving the browser direct privileged access to the operating
system.

------------------------------------------------------------------------

# 17. Security Model

The assistant should be local-first and secure by default.

The OS control API should bind to:

``` text
127.0.0.1
```

rather than exposing itself to the local network.

The backend should implement:

-   Tool authentication.
-   Permission checks.
-   Action confirmation.
-   Audit logs.
-   Process isolation where practical.
-   Command validation.
-   Restricted filesystem operations.
-   Clear execution history.

The assistant should never assume that because a model generated a
command, the command is safe.

------------------------------------------------------------------------

# 18. Memory System

The assistant should have persistent memory, but memory should be
deliberate and inspectable.

Possible memory categories:

### Short-Term Context

Current conversation and task.

### Session Context

What the user is currently working on.

### Project Context

Known project paths, tools, repositories, build systems, and workflows.

### Long-Term Preferences

Useful user preferences and recurring workflows.

### Action History

What the assistant recently did.

Example:

``` text
Current Project:
ZeGFX

Repository:
D:\Zelyn\ZeGFX

Current Branch:
main

Recent Task:
Visual benchmark

Last Action:
Built renderer successfully
```

The user should be able to inspect, edit, or delete stored memories.

------------------------------------------------------------------------

# 19. Context Awareness

The assistant should understand the computer's current context.

Potential context sources:

-   Active application.
-   Active window.
-   Current project.
-   Current repository.
-   Current directory.
-   Git branch.
-   Terminal state.
-   Clipboard.
-   Recent assistant actions.
-   User's current conversation.
-   Explicit screen capture.

This allows natural commands.

Instead of:

> "Open `D:\Zelyn\ZeGFX\tests\visual_benchmark_manifest.json`."

the user can say:

> "Open the benchmark manifest."

The assistant resolves the reference using context.

------------------------------------------------------------------------

# 20. Developer Mode

Because this assistant is intended to be useful during software
development, development tooling should be a major subsystem.

Potential tools:

``` text
build_project()

run_tests()

run_benchmark()

run_application()

kill_process()

read_build_log()

parse_compiler_errors()

open_source_file()

search_codebase()

git_status()

git_diff()

git_commit()

git_branch()

git_pull()

git_push()
```

The assistant can become a development companion capable of executing
and interpreting workflows.

Example:

``` text
User:
Build ZeGFX.

Assistant:
Building...

✓ Configure
✓ Compile
✓ Link

Build successful.

User:
Run the benchmark.

Assistant:
Running visual benchmark...

✓ 5 scenes captured
✓ 4 passed
⚠ 1 scene shows temporal instability
```

------------------------------------------------------------------------

# 21. Task Execution Model

The assistant should not treat complex requests as one giant model
response.

Instead:

``` text
User Request
     ↓
Intent Understanding
     ↓
Task Planning
     ↓
Plan Validation
     ↓
Tool Selection
     ↓
Execution
     ↓
Observation
     ↓
Correction
     ↓
Completion
```

Example:

> "Prepare my ZeGFX environment for development."

The assistant could determine:

1.  Identify ZeGFX project.
2.  Check repository state.
3.  Check active development tools.
4.  Open required applications.
5.  Open the project.
6.  Open terminal.
7.  Check build configuration.
8.  Report readiness.

------------------------------------------------------------------------

# 22. Observation Loop

For tasks involving the OS, the assistant should operate as an observe →
act → observe system.

``` text
Observe
   ↓
Reason
   ↓
Act
   ↓
Observe Result
   ↓
Reason
   ↓
Continue / Correct / Stop
```

This is much safer and more reliable than generating an entire sequence
of blind actions.

------------------------------------------------------------------------

# 23. Task History

The interface should show what the assistant has done.

Example:

``` text
10:42
Opened Visual Studio

10:43
Built ZeGFX

10:44
Build failed

10:45
Parsed compiler output

10:46
Opened PipelineOrchestrator.cpp
```

This gives the user confidence that the assistant is actually doing
something.

------------------------------------------------------------------------

# 24. System Status

The assistant can expose useful system information.

Potential information:

-   CPU utilization.
-   GPU utilization.
-   RAM usage.
-   VRAM usage.
-   Disk activity.
-   Network state.
-   Active processes.
-   Current audio device.
-   Microphone state.
-   Assistant state.

This can become another future dashboard region.

------------------------------------------------------------------------

# 25. Application Launcher / Automation

The assistant should support user-defined workflows.

Example:

``` text
"Start ZeGFX development."

→ Open VS Code
→ Open ZeGFX folder
→ Open terminal
→ Start build environment
→ Open Unreal/Godot if required
→ Arrange windows
```

These workflows can be stored as named routines.

Example:

``` text
/start-zegfx

/open-game-project

/run-benchmark

/prepare-recording
```

Natural language can map to these routines.

------------------------------------------------------------------------

# 26. Embedded Browser + Assistant Integration

The browser should eventually be integrated with the assistant's
context.

For example:

> "Find the DirectX 12 documentation for this error."

The assistant can:

1.  Read the error.
2.  Search the browser.
3.  Open relevant documentation.
4.  Summarize the result.
5.  Keep the page visible.

The browser should remain independently usable as a normal lightweight
browser.

------------------------------------------------------------------------

# 27. UI Design Direction

The visual style should be:

-   Sleek.
-   Professional.
-   Futuristic.
-   Dark.
-   Minimal.
-   High information density.
-   Not overly "AI-themed."
-   Not filled with unnecessary glowing effects.
-   Clear typography.
-   Subtle animations.
-   Strong hierarchy.

The assistant should feel like a **professional desktop control
center**, not a sci-fi movie prop.

The central AI indicator can have more visual personality because it is
the identity of the assistant.

------------------------------------------------------------------------

# 28. Suggested Technology Structure

A possible implementation:

``` text
assistant/
├── frontend/
│   ├── dashboard/
│   ├── quicklaunch/
│   ├── windows/
│   ├── git/
│   ├── browser/
│   └── output/
│
├── backend/
│   ├── assistant/
│   ├── planner/
│   ├── memory/
│   ├── context/
│   ├── tools/
│   ├── permissions/
│   └── events/
│
├── host/
│   ├── audio/
│   ├── os/
│   ├── windows/
│   ├── input/
│   └── capture/
│
├── models/
│   ├── llm/
│   ├── speech/
│   ├── tts/
│   └── vision/
│
├── integrations/
│   ├── git/
│   ├── terminal/
│   ├── vscode/
│   ├── visual_studio/
│   ├── unreal/
│   └── browser/
│
└── data/
    ├── memory/
    ├── settings/
    ├── workflows/
    └── logs/
```

The exact language/framework is not locked yet.

------------------------------------------------------------------------

# 29. Model-Agnostic Design

The assistant should not be permanently tied to a single AI model.

The model layer should be abstracted.

``` text
Assistant Core
      ↓
Model Interface
      ↓
┌──────────────┬──────────────┬──────────────┐
│ Local Model  │ Cloud Model  │ Future Model │
└──────────────┴──────────────┴──────────────┘
```

This allows experimentation with:

-   Local LLMs.
-   Cloud LLMs.
-   Different reasoning models.
-   Different vision models.
-   Different speech models.
-   Different TTS engines.

The assistant's tool system should remain independent from the model.

------------------------------------------------------------------------

# 30. Local-First Philosophy

The system should prefer local processing when practical.

Potential local components:

-   Wake-word detection.
-   Voice activity detection.
-   Speech recognition.
-   TTS.
-   Screen capture.
-   OS tools.
-   Memory.
-   Git integration.
-   Window management.
-   Local files.

Cloud AI can be optional rather than mandatory.

This improves:

-   Privacy.
-   Latency.
-   Reliability.
-   Offline capability.
-   Control.

------------------------------------------------------------------------

# 31. Failure Handling

The assistant must be able to fail safely.

Examples:

### Application fails to open

Report:

> "Visual Studio failed to start."

### Build fails

Read the error and explain it.

### Tool unavailable

Do not pretend it succeeded.

### Permission denied

Explain exactly what permission is required.

### Ambiguous request

Ask a concise clarification rather than guessing.

### Destructive action

Request confirmation.

------------------------------------------------------------------------

# 32. Interruption

The user should always be able to interrupt the assistant.

Example:

Assistant:

> "I'm opening the project and then---"

User:

> "Stop."

The current operation should be cancelled when possible.

This is especially important for:

-   Voice output.
-   Long-running tasks.
-   Shell commands.
-   Automation sequences.
-   Browser navigation.

------------------------------------------------------------------------

# 33. Transparency

The assistant should make actions visible.

Instead of silently executing:

``` text
run_command(...)
```

the interface should show:

``` text
Running:
cmake --build build --config Release
```

For long-running tasks:

``` text
BUILDING
████████████████░░░░ 82%
```

The user should always have a rough understanding of what the assistant
is doing.

------------------------------------------------------------------------

# 34. Future Capabilities

Potential future extensions:

-   Calendar integration.
-   Email integration.
-   Notes.
-   Reminders.
-   Smart-home control.
-   Media control.
-   File organization.
-   Automated backups.
-   Project monitoring.
-   Download monitoring.
-   System maintenance.
-   Personal knowledge base.
-   Codebase indexing.
-   Local documentation indexing.
-   Multi-agent workflows.
-   Custom plugins.
-   User-created tools.
-   Custom voice/personality.
-   Full desktop automation.

------------------------------------------------------------------------

# 35. Plugin / Tool Ecosystem

Eventually, the assistant should support plugins.

A plugin could expose:

``` text
name
description
permissions
tools
events
configuration
```

Example:

``` text
ZeGFX Plugin
├── Build renderer
├── Run benchmark
├── Open renderer
├── Inspect logs
└── Capture benchmark
```

Another plugin:

``` text
Git Plugin
├── Status
├── Diff
├── Commit
├── Branch
├── Pull
└── Push
```

Another:

``` text
Windows Plugin
├── List windows
├── Focus
├── Move
├── Resize
└── Close
```

This keeps the core assistant small while allowing capabilities to grow.

------------------------------------------------------------------------

# 36. MVP

The first version should NOT attempt to implement everything.

Recommended MVP:

## Phase 1 --- Dashboard

-   Second-monitor UI.
-   Central live indicator.
-   Quick Launch.
-   Active Windows.
-   Git Status.
-   Browser panel.
-   AI Output panel.

## Phase 2 --- Voice

-   Microphone.
-   Speech-to-text.
-   Text-to-speech.
-   Basic conversation.
-   Push-to-talk / wake word.

## Phase 3 --- Local Backend

-   Localhost API.
-   WebSocket events.
-   Assistant state management.
-   Tool router.

## Phase 4 --- OS Tools

-   Launch application.
-   List windows.
-   Focus window.
-   Open files/folders.
-   Read clipboard.
-   Screenshot.
-   Terminal execution.

## Phase 5 --- Permissions

-   Tool permission system.
-   Confirmation dialogs.
-   Action logging.

## Phase 6 --- Developer Tools

-   Git.
-   Build.
-   Tests.
-   Terminal.
-   Compiler error parsing.
-   Project detection.

## Phase 7 --- Vision

-   Screenshot analysis.
-   OCR.
-   Screen understanding.

## Phase 8 --- Memory

-   Session memory.
-   Project context.
-   Long-term user-approved memory.

------------------------------------------------------------------------

# 37. Example End-to-End Interaction

User:

> "Hey, build ZeGFX."

Assistant:

``` text
LISTENING
    ↓
PROCESSING
    ↓
Identified project: ZeGFX
    ↓
Checking repository
    ↓
Building
```

The dashboard shows:

``` text
ACTIVE TASK

Build ZeGFX

✓ Project found
✓ Repository checked
✓ Build configured
⟳ Compiling
```

Build finishes.

Assistant:

> "ZeGFX built successfully."

User:

> "Run the visual benchmark."

Assistant:

``` text
✓ Found benchmark manifest
✓ Started renderer
✓ Captured scene 1
✓ Captured scene 2
✓ Captured scene 3
✓ Captured scene 4
✓ Captured scene 5
```

Assistant:

> "Benchmark completed. Four scenes passed. One scene shows possible
> temporal instability."

User:

> "Show me."

Assistant opens the results in the browser panel.

That is the target experience.

------------------------------------------------------------------------

# 38. Design Principles

The project should follow these principles:

1.  **Voice first, but never voice only.**
2.  **Local-first whenever practical.**
3.  **The AI does not get unrestricted OS access.**
4.  **Every action is a tool with explicit permissions.**
5.  **Complex tasks are planned and observed incrementally.**
6.  **The user can interrupt the assistant.**
7.  **The assistant is transparent about what it is doing.**
8.  **The interface should remain useful without active conversation.**
9.  **The model layer should remain replaceable.**
10. **The assistant should become more capable through tools rather than
    becoming an increasingly giant monolith.**

------------------------------------------------------------------------

# 39. Long-Term Goal

The final goal is a **personal computer AI layer**.

Not simply:

> "Ask an AI questions."

Instead:

> "Have an AI that lives alongside you while you use your computer."

It should understand what you are doing, communicate naturally, provide
useful information, operate software when authorized, help with
development, manage repetitive workflows, and give you a persistent
visual and conversational interface to your computer.

The second monitor becomes the assistant's home.

The first monitor remains yours.

The assistant sits between you and the operating system as a
**controlled, observable, extensible intelligence layer**.
