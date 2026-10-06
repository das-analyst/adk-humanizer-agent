import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root))

from google.adk.runners import Runner
from agents.humanizer_orchestrator.agent import root_agent

async def main():
    input_file = Path("benchmarks/private/ldr500_wk05_ai.md")
    text = input_file.read_text(encoding="utf-8")
    
    # We pass the text. The orchestrator will parse it and run the long mode.
    # To enable casual slips, we can append `--casual-slips` to the text.
    prompt = text + "\n\n--casual-slips"

    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.genai import types
    
    runner = Runner(
        agent=root_agent,
        app_name="humanizer_orchestrator",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    import time
    progress_file = Path("benchmarks/private/progress.log")
    progress_file.write_text(f"[{time.strftime('%H:%M:%S')}] Started humanization run...\n", encoding="utf-8")

    parts = []
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    async for event in runner.run_async(user_id="u", session_id="s", new_message=msg):
        text_content = getattr(event, "text", None)
        if not text_content and event.content and event.content.parts:
            text_content = "".join(p.text for p in event.content.parts if hasattr(p, "text") and p.text)
        
        if text_content:
            parts.append(text_content)
            with open(progress_file, "a", encoding="utf-8") as f:
                preview = text_content[:100].replace("\n", " ")
                f.write(f"[{time.strftime('%H:%M:%S')}] Event ({len(text_content)} chars): {preview}...\n")
                        
    output_file = Path("benchmarks/private/ldr500_wk05_agent_output.md")
    output_file.write_text("\n".join(parts), encoding="utf-8")
    with open(progress_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] Complete! Output saved to {output_file}\n")
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
