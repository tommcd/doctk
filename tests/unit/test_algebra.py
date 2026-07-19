"""The documented pipeline algebra, exercised exactly as documented.

Every form shown in the README / docstrings must execute. These tests keep
the advertised API honest: selectors are dual-use (predicate on nodes,
subset operation on documents), select is idempotent, and matches/contains
follow regex/literal semantics respectively.
"""

from doctk import Document, Heading, Paragraph, compose, contains, matches, select, where
from doctk.core import CodeBlock
from doctk.operations import Selector, heading, is_heading, paragraph, promote

SAMPLE = """# Title

Intro paragraph.

## Section A

### Detail A1

### Detail A2

## Section B
"""


def _doc() -> Document:
    return Document.from_string(SAMPLE)


class TestDocumentedPipelines:
    """The exact pipelines shown in the README and docstrings."""

    def test_readme_flagship_pipeline_executes(self):
        # README: doc | select(heading) | where(level=3) | promote()
        result = _doc() | select(heading) | where(level=3) | promote()
        assert [node.level for node in result.nodes] == [2, 2]
        assert [node.text for node in result.nodes] == ["Detail A1", "Detail A2"]

    def test_select_heading_equals_bare_heading(self):
        via_select = _doc() | select(heading)
        bare = _doc() | heading
        assert [n.text for n in via_select.nodes] == [n.text for n in bare.nodes]

    def test_compose_right_to_left(self):
        # compose(f, g, h)(x) = f(g(h(x)))
        process = compose(promote(), where(level=3), select(heading))
        result = process(_doc())
        assert [node.level for node in result.nodes] == [2, 2]


class TestSelectorDuality:
    """A selector is both a predicate on nodes and an operation on documents."""

    def test_selector_as_predicate(self):
        assert heading(Heading(level=1, text="T")) is True
        assert heading(Paragraph(content="p")) is False

    def test_selector_as_operation(self):
        result = heading(_doc())
        assert all(isinstance(node, Heading) for node in result.nodes)
        assert len(result.nodes) == 5

    def test_select_is_idempotent(self):
        assert select(heading) is heading
        doc = _doc()
        assert select(select(is_heading))(doc).nodes == select(is_heading)(doc).nodes

    def test_where_is_dual_use(self):
        level2 = where(level=2)
        assert level2(Heading(level=2, text="S")) is True
        assert level2(Heading(level=3, text="S")) is False
        result = _doc() | heading | level2
        assert [node.text for node in result.nodes] == ["Section A", "Section B"]

    def test_selectors_have_names(self):
        assert isinstance(heading, Selector)
        assert heading.__name__ == "heading"
        assert paragraph.__name__ == "paragraph"


class TestMatchesAndContains:
    """matches() is regex; contains() is literal substring."""

    def test_matches_plain_substring(self):
        result = _doc() | matches("Section")
        assert len(result.nodes) == 2

    def test_matches_regex_anchor(self):
        result = _doc() | matches(r"^Detail A\d$")
        assert [node.text for node in result.nodes] == ["Detail A1", "Detail A2"]

    def test_matches_searches_code_blocks(self):
        doc = Document([CodeBlock(code="def main():\n    pass", language="python")])
        assert len((doc | matches(r"def \w+")).nodes) == 1

    def test_contains_treats_pattern_literally(self):
        doc = Document([Paragraph(content="Uses C++ (not regex)")])
        assert len((doc | contains("C++ (not regex)")).nodes) == 1
        assert len((doc | contains("C--")).nodes) == 0

    def test_matches_ignores_nodes_without_text(self):
        from doctk.core import RawBlock

        doc = Document([RawBlock(content="---", token_type="hr")])
        assert len((doc | matches("-")).nodes) == 0
