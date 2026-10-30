import pytest

from vsa.markdown_directives import process_directives, DirectiveError


def test_passthrough_plain_text():
    text = "# Titel\n\nGewone tekst.\n"
    assert process_directives(text) == text


def test_pagebreak():
    text = "Voor.\n:::pagebreak:::\nNa.\n"
    result = process_directives(text)
    assert '<div class="pagebreak"></div>' in result
    assert ":::pagebreak:::" not in result
    assert "Voor." in result
    assert "Na." in result


def test_web_only_block():
    text = ":::web-only:::\nAlleen web.\n:::end-web-only:::\n"
    result = process_directives(text)
    assert "{{< web-only >}}" in result
    assert "{{< /web-only >}}" in result
    assert "Alleen web." in result
    assert ":::web-only:::" not in result
    assert ":::end-web-only:::" not in result


def test_opening_shortcode_does_not_insert_blank_line():
    text = ":::web-only:::\n# Titel\n:::end-web-only:::\n"
    result = process_directives(text)
    assert "{{< web-only >}}\n# Titel" in result
    assert "{{< web-only >}}\n\n# Titel" not in result


def test_print_only_block():
    text = ":::print-only:::\nAlleen print.\n:::end-print-only:::\n"
    result = process_directives(text)
    assert "{{< print-only >}}" in result
    assert "{{< /print-only >}}" in result
    assert "Alleen print." in result


def test_keep_together_block():
    text = ":::keep-together:::\nSamen op één pagina.\n:::end-keep-together:::\n"
    result = process_directives(text)
    assert "{{< keep-together >}}" in result
    assert "{{< /keep-together >}}" in result
    assert "Samen op één pagina." in result
    assert ":::keep-together:::" not in result
    assert ":::end-keep-together:::" not in result


def test_keep_together_with_scale():
    text = ':::keep-together scale="70%":::\nInhoud.\n:::end-keep-together:::\n'
    result = process_directives(text)
    assert '{{< keep-together scale="70%" >}}' in result
    assert "{{< /keep-together >}}" in result
    assert "scale" not in result.split("{{< /keep-together >}}")[1]


def test_keep_together_with_size():
    text = ':::keep-together size="1.1":::\nInhoud.\n:::end-keep-together:::\n'
    result = process_directives(text)
    assert '{{< keep-together size="1.1" >}}' in result
    assert "{{< /keep-together >}}" in result


def test_keep_together_with_size_and_scale():
    text = (
        ':::keep-together size="1.1" scale="70%":::\n'
        "Inhoud.\n"
        ":::end-keep-together:::\n"
    )
    result = process_directives(text)
    assert 'size="1.1"' in result
    assert 'scale="70%"' in result


def test_keep_together_without_scale_has_no_scale_attr():
    text = ":::keep-together:::\nInhoud.\n:::end-keep-together:::\n"
    result = process_directives(text)
    assert 'scale=' not in result
    assert 'size=' not in result


def test_multiple_directives_in_sequence():
    text = (
        ":::pagebreak:::\n"
        ":::web-only:::\nWeb inhoud.\n:::end-web-only:::\n"
        ":::print-only:::\nPrint inhoud.\n:::end-print-only:::\n"
        ":::keep-together:::\nSamen.\n:::end-keep-together:::\n"
    )
    result = process_directives(text)
    assert '<div class="pagebreak"></div>' in result
    assert "{{< web-only >}}" in result
    assert "{{< /web-only >}}" in result
    assert "{{< print-only >}}" in result
    assert "{{< /print-only >}}" in result
    assert "{{< keep-together >}}" in result
    assert "{{< /keep-together >}}" in result


def test_directives_inside_code_fence_ignored():
    text = (
        "```\n"
        ":::pagebreak:::\n"
        ":::web-only:::\nTekst.\n:::end-web-only:::\n"
        "```\n"
    )
    result = process_directives(text)
    assert ":::pagebreak:::" in result
    assert ":::web-only:::" in result
    assert ":::end-web-only:::" in result
    assert '<div class="pagebreak"></div>' not in result
    assert "{{< web-only >}}" not in result


def test_unclosed_web_only_raises():
    text = ":::web-only:::\nInhoud zonder sluiting.\n"
    with pytest.raises(DirectiveError, match="Niet-gesloten blok"):
        process_directives(text)


def test_unclosed_print_only_raises():
    text = ":::print-only:::\nInhoud.\n"
    with pytest.raises(DirectiveError, match="Niet-gesloten blok"):
        process_directives(text)


def test_unclosed_keep_together_raises():
    text = ":::keep-together:::\nInhoud.\n"
    with pytest.raises(DirectiveError, match="Niet-gesloten blok"):
        process_directives(text)


def test_end_tag_without_opening_raises():
    text = "Tekst.\n:::end-web-only:::\n"
    with pytest.raises(DirectiveError, match="zonder overeenkomend openingsblok"):
        process_directives(text)


def test_mismatched_end_tag_raises():
    text = ":::web-only:::\nInhoud.\n:::end-print-only:::\n"
    with pytest.raises(DirectiveError, match="Verkeerde sluitingstag"):
        process_directives(text)


def test_nested_directives_raise():
    text = (
        ":::web-only:::\n"
        ":::print-only:::\n"
        "Inhoud.\n"
        ":::end-print-only:::\n"
        ":::end-web-only:::\n"
    )
    with pytest.raises(DirectiveError, match="Geneste directives"):
        process_directives(text)
