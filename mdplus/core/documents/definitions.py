class CommentDefinition:
    def __init__(
        self,
        single_line: str,
        multi_line_start: str | list[str],
        multi_line_end: str | list[str] = None,
        multi_line_between: str | list[str] = "",
    ):
        multi_line_start = [multi_line_start] if isinstance(multi_line_start, str) else list(multi_line_start)
        if multi_line_end is None:
            multi_line_end = multi_line_start
        multi_line_end = [multi_line_end] if isinstance(multi_line_end, str) else list(multi_line_end)

        self.single_line = single_line
        self.multi_line_start: list[str] = multi_line_start
        self.multi_line_end: list[str] = multi_line_end
        self.multi_line_between = multi_line_between or ""

    @staticmethod
    def get_python_style():
        return CommentDefinition("#", ('"""', "'''"), ('"""', "'''"), "")

    @staticmethod
    def get_cpp_style():
        return CommentDefinition("//", "/*", "*/", ("", "*"))

    @staticmethod
    def get_markdown_style():
        return CommentDefinition(None, "<!--", "-->", "")
