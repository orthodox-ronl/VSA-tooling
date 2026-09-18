from pathlib import Path


REUSABLE = Path(".github/workflows/pages-deploy-reusable.yml")
DOCS_PAGES = Path(".github/workflows/docs-pages.yml")


def test_pages_deploy_reusable_workflow_exists():
    assert REUSABLE.exists()


def test_pages_deploy_reusable_is_workflow_call():
    text = REUSABLE.read_text(encoding="utf-8")

    assert "workflow_call:" in text
    assert "artifact_name:" in text
    assert "publish_dir:" in text
    assert "url_prefix:" in text


def test_pages_deploy_reusable_uses_peaceiris_not_deploy_pages():
    text = REUSABLE.read_text(encoding="utf-8")

    assert "peaceiris/actions-gh-pages@v4" in text
    assert "publish_branch: gh-pages" in text
    assert "keep_files:" in text
    assert "actions/deploy-pages" not in text
    assert "actions/upload-pages-artifact" not in text


def test_pages_deploy_reusable_documents_pages_source_notice():
    text = REUSABLE.read_text(encoding="utf-8")

    assert "pages build and deployment" in text
    assert "Deploy from a branch" in text


def test_pages_deploy_reusable_has_concurrency_with_cancel():
    """Verouderde gh-pages-deploys annuleren i.p.v. 15–30 min in de wachtrij."""
    text = REUSABLE.read_text(encoding="utf-8")

    assert "concurrency:" in text
    assert "cancel-in-progress: true" in text
    assert "cancel-in-progress: false" not in text


def test_pages_deploy_reusable_runs_publication_check():
    text = REUSABLE.read_text(encoding="utf-8")

    assert "check-publication-output.py" in text
    assert "skip_publication_check" in text


def test_pages_deploy_reusable_supports_subdirectory_and_root_deploy():
    text = REUSABLE.read_text(encoding="utf-8")

    assert "destination_dir != ''" in text
    assert "destination_dir == ''" in text


def test_docs_pages_uses_pages_deploy_reusable():
    text = DOCS_PAGES.read_text(encoding="utf-8")

    assert "pages-deploy-reusable.yml" in text
    assert "artifact_name: pages-docs-site" in text
    assert "upload-artifact@v7" in text
    assert "jobs:" in text
    assert "build:" in text
    assert "deploy:" in text
    assert "needs: build" in text
    assert "vsa_tooling_ref: ${{ github.sha }}" in text


def test_docs_pages_main_deploys_root_preview_subdir():
    text = DOCS_PAGES.read_text(encoding="utf-8")

    assert 'url_prefix=/VSA-tooling/"' in text or "url_prefix=/VSA-tooling/" in text
    assert "url_prefix=/VSA-tooling/preview/" in text
    assert "destination_dir=preview" in text


def test_pages_deploy_reusable_carries_forward_sibling_dirs_on_root():
    """Root-deploy wist gh-pages schoon en zet sibling-deploys (preview/, branches) terug."""
    text = REUSABLE.read_text(encoding="utf-8")

    assert "Carry forward sibling deploy dirs from current gh-pages" in text
    assert 'echo "Carried forward $name/"' in text
    assert "No sibling deploy dirs to carry forward" in text
    # Root peaceiris: altijd keep_files false (na carry-forward).
    assert "keep_files: false" in text


def test_docs_pages_keep_files_false_with_preview_carry_forward():
    """main en preview zetten keep_files=false; siblings blijven via reusable carry-forward."""
    text = DOCS_PAGES.read_text(encoding="utf-8")

    assert 'echo "keep_files=true"' not in text
    assert text.count('echo "keep_files=false"') == 2
