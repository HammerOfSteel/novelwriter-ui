"""
English-language generator that extends NovelWriter's Generator.

Keeps the original Japanese novelwriter/ submodule untouched while adding
English prompt support. Also provides `analyze_and_generate_plot` and
`generate_outline_from_structure` for the "import existing directory" workflow.
"""
from __future__ import annotations

import json
import os
import sys

# Ensure the novelwriter submodule is importable
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_BACKEND_DIR)
sys.path.insert(0, os.path.join(_ROOT, "novelwriter"))

from generators import Generator  # noqa: E402
from config import Config  # noqa: E402


class GeneratorEN(Generator):
    """Drop-in replacement for Generator that uses English prompts."""

    # ------------------------------------------------------------------
    # Core generation methods (all overriding parent)
    # ------------------------------------------------------------------

    def generate_plot(self, idea: str | None = None) -> str:
        prompt = (
            "Create a detailed plot for a long-form novel of approximately "
            "70,000–100,000 words. "
        )
        if idea:
            prompt += f"\n\nStarting idea:\n{idea}\n\n"
        prompt += (
            "Structure the narrative with a clear beginning, escalating middle, "
            "and satisfying conclusion. Describe the central conflict, key turning "
            "points, subplots, and thematic core. Write in English."
        )
        plot = self.client.generate_text(prompt)
        self.state_manager.save_plot(plot)
        return plot

    def generate_characters(self, plot: str) -> list:
        prompt = f"""Based on the plot below, create a character list in JSON format.
Each character must include:
- name
- age  (number or description like "mid-thirties")
- role (protagonist / antagonist / supporting / minor)
- personality (key traits and motivation)
- speech_style (how they speak — terse, eloquent, sarcastic, etc.)
- background (brief history relevant to the story)

Rule: if the plot mentions unnamed relatives, mentors, or historical figures,
invent names for them — leave no important person nameless.

Plot:
{plot}

Output ONLY valid JSON — no markdown fences. Format:
[
  {{
    "name": "Full Name",
    "age": "Age",
    "role": "Role",
    "personality": "...",
    "speech_style": "...",
    "background": "..."
  }}
]
All values in English."""
        response = self._clean_json_response(self.client.generate_text(prompt))
        try:
            characters = json.loads(response)
            self.state_manager.save_characters(characters)
            return characters
        except json.JSONDecodeError:
            self.state_manager.save_text("characters_raw.txt", response)
            return []

    def generate_world(self, plot: str) -> dict:
        prompt = f"""Based on the plot below, create world-building settings in JSON format.

Plot:
{plot}

Output ONLY valid JSON. Format:
{{
  "location_names": ["Place 1", "Place 2"],
  "history": "Relevant world history...",
  "magic_system": "Any special systems, technology, or rules — write 'None' if N/A",
  "important_rules": "Key constraints or laws of this world"
}}
All values in English."""
        response = self._clean_json_response(self.client.generate_text(prompt))
        try:
            world = json.loads(response)
            self.state_manager.save_world(world)
            return world
        except json.JSONDecodeError:
            self.state_manager.save_text("world_raw.txt", response)
            return {}

    def generate_outline(self, plot: str, characters: list | dict, world: dict) -> list:
        prompt = f"""Create a detailed chapter-and-scene outline for a long-form novel.
Aim for 10–15 chapters with 2–4 scenes each.

Plot (excerpt):
{plot[:2500]}

Characters:
{json.dumps(characters, ensure_ascii=False)[:1200]}

World:
{json.dumps(world, ensure_ascii=False)[:600]}

Output ONLY a valid JSON array — no markdown fences. Format:
[
  {{
    "chapter_id": 1,
    "chapter_title": "Title",
    "scenes": [
      {{
        "scene_id": 1,
        "title": "Scene Title",
        "location": "Where",
        "characters_present": ["Name"],
        "summary": "What happens",
        "emotional_tone": "Tension / Hope / Grief / etc."
      }}
    ]
  }}
]
All values in English. scene_id must be globally unique and sequential."""
        # Outline JSON for 10-15 chapters × 3 scenes is large — give it more room.
        # With thinking OFF this fits; with thinking ON the budget is shared.
        response = self._clean_json_response(
            self.client.generate_text(prompt, max_tokens=6000)
        )
        try:
            outline = json.loads(response)
            self.state_manager.save_outline(outline)
            return outline
        except json.JSONDecodeError:
            self.state_manager.save_text("outline_raw.txt", response)
            return []

    def write_scene(
        self,
        scene: dict,
        previous_summary: str,
        characters: list | dict,
        world: dict,
        current_state: dict,
    ) -> str:
        prompt = f"""Write a complete, vivid scene for a novel.

Scene info:
{json.dumps(scene, ensure_ascii=False)}

Previous events:
{previous_summary[:600] if previous_summary else "This is the opening of the story."}

Characters:
{json.dumps(characters, ensure_ascii=False)[:2000]}

World:
{json.dumps(world, ensure_ascii=False)[:600]}

Narrative state:
{json.dumps(current_state, ensure_ascii=False)[:600]}

Viewpoint: {Config.NOVEL_VIEWPOINT}
Style: {Config.NOVEL_STYLE}

Instructions:
- Write at least 1,500 words.
- Include dialogue, internal monologue, sensory details, and meaningful action.
- Do NOT add a title header.
- Write in English."""
        return self.client.generate_text(prompt)

    def generate_title(self, scene_text: str) -> str:
        prompt = f"""Write a short, evocative title (3–7 words) for this scene.

{scene_text[:600]}

Output ONLY the title — no quotes, no punctuation other than what belongs in the title."""
        return self.client.generate_text(prompt).strip().strip('"').strip("'")

    def summarize_scene(self, scene_text: str) -> str:
        prompt = f"""Summarize the following scene in 3–5 sentences.
Focus on key plot developments, character actions, and important revelations.
Write in English.

Scene:
{scene_text[:3500]}"""
        return self.client.generate_text(prompt)

    def update_state(self, scene_text: str, current_state: dict, characters: list | dict) -> dict:
        prompt = f"""Update the story tracking state based on this new scene.
Return a JSON object with keys:
character_locations, relationships, revealed_secrets, active_conflicts, items_of_note.

Previous state:
{json.dumps(current_state, ensure_ascii=False)[:700]}

Characters:
{json.dumps(characters, ensure_ascii=False)[:1200]}

New scene:
{scene_text[:2500]}

Output ONLY valid JSON — no markdown fences."""
        response = self._clean_json_response(self.client.generate_text(prompt))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return current_state  # Fall back to unchanged state

    # ------------------------------------------------------------------
    # Import workflow helpers (not in the original Generator)
    # ------------------------------------------------------------------

    def analyze_and_generate_plot(self, content_summary: str) -> str:
        """
        Derive a plot document from an excerpt of existing written chapters.
        Used when importing a generic writing directory.
        """
        prompt = f"""You are given excerpts from a novel-in-progress.
Analyze the content and write a comprehensive plot document covering:
- Main story arc and central conflict
- Key events and turning points discovered so far
- Main characters and their goals
- Setting and world
- Themes and tone
- Where the story currently stands

Content excerpts:
{content_summary[:5000]}

Write a detailed plot summary in English (at least 500 words)."""
        return self.client.generate_text(prompt)

    def generate_outline_from_structure(
        self, chapters_structure: list, content_summary: str
    ) -> list:
        """
        Build a NovelWriter outline JSON from an imported directory structure.
        Preserves the folder-name → chapter-title and file-name → scene-title mapping.
        """
        chapters_str = json.dumps(chapters_structure, ensure_ascii=False)[:2500]

        prompt = f"""You are given a writing project's directory structure and content excerpts.
Create a NovelWriter-format outline that maps the existing files to chapters and scenes.

Directory structure (folder = chapter, file = scene):
{chapters_str}

Content excerpts:
{content_summary[:2500]}

Rules:
- Use folder names as chapter_title values.
- Use file names (without .md) as scene title values.
- Assign scene_id sequentially starting from 1.
- Write brief summaries for each scene based on filenames / content hints.

Output ONLY a valid JSON array — no markdown fences. Format:
[
  {{
    "chapter_id": 1,
    "chapter_title": "Folder Name",
    "scenes": [
      {{
        "scene_id": 1,
        "title": "File Name",
        "summary": "Brief description of what this scene contains"
      }}
    ]
  }}
]
All values in English."""
        response = self._clean_json_response(self.client.generate_text(prompt))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []
