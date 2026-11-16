from pathlib import Path

ROOT = Path(__file__).resolve().parent


def register(ctx):
    from agent.skill_utils import parse_frontmatter

    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        frontmatter, _ = parse_frontmatter(path.read_text())
        ctx.register_skill(path.parent.name, path, frontmatter.get("description", ""), frontmatter)
