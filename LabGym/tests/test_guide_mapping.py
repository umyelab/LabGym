"""AF regression: Workflow Map popup guide tokens resolve to page numbers.

Isolated from gui_main import (and its heavy panel/selftest dependencies) by
reading the module source and evaluating only the guide table assignments.
"""

import ast
from pathlib import Path


def _gui_main_source_path() -> Path:
	# LabGym/tests/this_file.py -> LabGym/gui_main.py
	return Path(__file__).resolve().parent.parent / 'gui_main.py'


def _literal_assign(tree: ast.AST, name: str):
	"""Return the literal value of a top-level assignment ``name = <literal>``."""
	for node in tree.body:
		if not isinstance(node, ast.Assign):
			continue
		for target in node.targets:
			if isinstance(target, ast.Name) and target.id == name:
				return ast.literal_eval(node.value)
	raise AssertionError('Assignment {!r} not found in gui_main.py'.format(name))


def _load_guide_tables():
	source = _gui_main_source_path().read_text(encoding='utf-8')
	tree = ast.parse(source, filename=str(_gui_main_source_path()))
	box_popup = _literal_assign(tree, '_BOX_POPUP')
	guide_pages = _literal_assign(tree, '_GUIDE_PAGES')
	return box_popup, guide_pages


def _resolve_guide_page_number(guide_pages, ref: str):
	if not ref:
		return None
	return guide_pages.get(ref.strip().lower())


def _iter_box_popup_guide_refs(box_popup):
	for key, data in box_popup.items():
		guide = data[3]
		for ref in guide.split(','):
			ref = ref.strip()
			if ref:
				yield key, ref


def _practical_guide_url(page_number: int) -> str:
	return 'https://www.labgym.org/guides/practical-guide#page-{}'.format(page_number)


def test_every_intentional_popup_guide_token_resolves():
	box_popup, guide_pages = _load_guide_tables()
	unresolved = []
	for box_key, ref in _iter_box_popup_guide_refs(box_popup):
		page = _resolve_guide_page_number(guide_pages, ref)
		if page is None:
			unresolved.append((box_key, ref))
	assert unresolved == [], 'Unresolved guide tokens: {}'.format(unresolved)


def test_background_subtraction_section_lll_a_is_page_28():
	box_popup, guide_pages = _load_guide_tables()
	guide = box_popup['bg_sub'][3]
	tokens = [r.strip() for r in guide.split(',')]
	assert 'Part 3.1' in tokens
	assert 'Part 4.1' in tokens
	assert 'Section lll A' in tokens
	assert _resolve_guide_page_number(guide_pages, 'Section lll A') == 28
	assert _practical_guide_url(28) == (
		'https://www.labgym.org/guides/practical-guide#page-28'
	)
