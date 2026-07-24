#!/usr/bin/env python3
"""
Demo: build one agent per MABP archetype, plus one blended example.
Run directly: python3 framework/examples.py

This only prints generated system prompts — it doesn't call any API or LLM.
"""
from agent_blueprint import build_agent, list_archetypes


def main() -> None:
    print(f"Archetypes available: {list_archetypes()}\n")

    for archetype in list_archetypes():
        agent = build_agent(archetype, name=f"{archetype}Bot")
        print("=" * 70)
        print(f"{agent.name}  —  {agent.archetype}")
        print(f"Evidence basis: {agent.evidence_basis}")
        print("-" * 70)
        print(agent.system_prompt)
        print()

    # Blended example: as many agents as you like, mixing archetypes.
    blended = build_agent(
        "Architect",
        name="Ferry",
        blend_with="Resident",
        extra_instructions=["Report weekly on which patterns you preserved vs. changed."],
    )
    print("=" * 70)
    print(f"{blended.name}  —  {blended.archetype}")
    print(f"Evidence basis: {blended.evidence_basis}")
    print("-" * 70)
    print(blended.system_prompt)


if __name__ == "__main__":
    main()
