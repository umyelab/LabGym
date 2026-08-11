"""AF regression: notebook page selection and close protection by object identity."""

from LabGym import mywx  # patch wx.App before any import of wx / gui_utils
from LabGym.gui_utils import is_protected_notebook_page, select_notebook_page


class _StubNotebook:
	"""Minimal notebook stand-in with reordering support (no live wx session)."""

	def __init__(self):
		self._pages = []
		self._titles = []
		self.selection = None

	def AddPage(self, page, title, select=False):
		self._pages.append(page)
		self._titles.append(title)
		if select or self.selection is None:
			self.selection = len(self._pages) - 1

	def GetPageCount(self):
		return len(self._pages)

	def GetPage(self, index):
		return self._pages[index]

	def GetPageText(self, index):
		return self._titles[index]

	def SetPageText(self, index, title):
		self._titles[index] = title

	def SetSelection(self, index):
		self.selection = index

	def InsertPage(self, index, page, title, select=False):
		self._pages.insert(index, page)
		self._titles.insert(index, title)
		if select:
			self.selection = index
		elif self.selection is not None and self.selection >= index:
			self.selection += 1

	def MovePage(self, old_index, new_index):
		page = self._pages.pop(old_index)
		title = self._titles.pop(old_index)
		self._pages.insert(new_index, page)
		self._titles.insert(new_index, title)


def test_select_workflow_map_after_unrelated_tabs_inserted_or_reordered():
	home = object()
	workflow = object()
	other = object()
	nb = _StubNotebook()
	nb.AddPage(home, 'Home', select=True)
	nb.AddPage(workflow, 'Workflow Map')
	nb.InsertPage(0, other, 'Other Tab')
	assert nb.GetPage(0) is other
	assert select_notebook_page(nb, workflow) is True
	assert nb.GetPage(nb.selection) is workflow

	nb.MovePage(nb.selection, 0)
	assert nb.GetPage(0) is workflow
	extra = object()
	nb.AddPage(extra, 'Extra')
	assert select_notebook_page(nb, workflow) is True
	assert nb.GetPage(nb.selection) is workflow


def test_home_and_workflow_protected_after_reordering():
	home = object()
	workflow = object()
	other = object()
	nb = _StubNotebook()
	nb.AddPage(home, 'Home')
	nb.AddPage(workflow, 'Workflow Map')
	nb.AddPage(other, 'Analysis')
	nb.MovePage(0, 2)  # home no longer at index 0
	protected = (home, workflow)

	for i in range(nb.GetPageCount()):
		page = nb.GetPage(i)
		should_protect = page is home or page is workflow
		assert is_protected_notebook_page(page, protected) is should_protect


def test_other_pages_not_protected():
	home = object()
	workflow = object()
	other = object()
	assert is_protected_notebook_page(other, (home, workflow)) is False
	assert is_protected_notebook_page(None, (home, workflow)) is False


def test_title_change_does_not_break_object_identity():
	home = object()
	workflow = object()
	nb = _StubNotebook()
	nb.AddPage(home, 'Home')
	nb.AddPage(workflow, 'Workflow Map')
	nb.SetPageText(0, 'Renamed Home')
	nb.SetPageText(1, 'Renamed Map')
	assert select_notebook_page(nb, home) is True
	assert nb.GetPage(nb.selection) is home
	assert select_notebook_page(nb, workflow) is True
	assert nb.GetPage(nb.selection) is workflow
	assert is_protected_notebook_page(home, (home, workflow))
	assert is_protected_notebook_page(workflow, (home, workflow))


def test_select_missing_page_returns_false():
	nb = _StubNotebook()
	nb.AddPage(object(), 'Home')
	assert select_notebook_page(nb, object()) is False
	assert select_notebook_page(None, object()) is False
	assert select_notebook_page(nb, None) is False
