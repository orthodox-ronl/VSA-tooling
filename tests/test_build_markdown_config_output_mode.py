from pathlib import Path

from vsa.config import load_config
from vsa.markdown_builder import build_markdown_site


def test_build_markdown_can_use_output_mode_from_config(tmp_path: Path):
    config_file = tmp_path / "vsa.toml"
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    assets_dir = tmp_path / "assets"

    input_dir.mkdir()

    config_file.write_text(
        '''[hugo]
assets-url-prefix = "/vsa"
output-mode = "shortcode"
''',
        encoding="utf-8",
    )

    (input_dir / "demo.md").write_text(
        '''::: vsa-notatie
{tekst}
:::
''',
        encoding="utf-8",
    )

    config = load_config(config_file)

    build_markdown_site(
        input_dir,
        output_dir,
        assets_dir,
        assets_url_prefix=config.hugo.assets_url_prefix,
        output_mode=config.hugo.output_mode,
    )

    content = (output_dir / "demo.md").read_text(encoding="utf-8")

    assert (
        '{{< vsa src="/vsa/demo-block-1.svg" alt="VSA notatie" '
        'scale="calc(3.4 * var(--vsa-size, 1.25) * 1em)" >}}'
    ) in content
