from typing import List

def render_template(script: str, names: List[str]) -> List[str]:
    if "{name}" not in script:
        raise ValueError("Script must contain {name} placeholder")

    rendered_scripts = []
    for name in names:
        rendered_scripts.append(script.replace("{name}", name))

    return rendered_scripts
