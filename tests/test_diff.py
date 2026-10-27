from reviewforge.diff import parse_changed_lines


def test_added_lines_keep_new_file_line_numbers():
    diff = """diff --git a/demo.py b/demo.py
index 1111111..2222222 100644
--- a/demo.py
+++ b/demo.py
@@ -1,3 +1,4 @@
 line one
+new line
 line two
-line three
+updated line three
"""
    found = parse_changed_lines(diff)
    assert [(x.path, x.new_line, x.content) for x in found] == [
        ("demo.py", 2, "new line"),
        ("demo.py", 4, "updated line three"),
    ]


def test_new_file():
    diff = """diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+print('one')
+print('two')
"""
    found = parse_changed_lines(diff)
    assert [x.new_line for x in found] == [1, 2]
    assert all(x.path == "new.py" for x in found)


def test_non_diff_is_empty():
    assert parse_changed_lines("plain text") == []
