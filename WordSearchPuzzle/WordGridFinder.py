from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema.message import Message
import json


class WordGridFinder(Component):
    display_name = "Word Grid Finder"
    description = "Finds words in a 2D letter grid and generates HTML visualization"
    icon = "grid"

    inputs = [
        MessageTextInput(
            name="letter_grid_json",
            display_name="Letter Grid (JSON)",
            info="2D array JSON string of letters",
            required=True,
        ),
        MessageTextInput(
            name="word_list",
            display_name="Word List",
            info="Comma-separated list of words to find in the grid",
            required=True,
        ),
    ]

    outputs = [
        Output(
            display_name="HTML",
            name="html_output",
            method="find_and_visualize",
        ),
    ]

    DIRECTIONS = [
        (0, 1),   # right
        (0, -1),  # left
        (1, 0),   # down
        (-1, 0),  # up
        (1, 1),   # down-right
        (1, -1),  # down-left
        (-1, 1),  # up-right
        (-1, -1), # up-left
    ]

    COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#F0B27A", "#82E0AA",
    ]

    def find_word(self, grid, word):
        rows = len(grid)
        cols = len(grid[0])
        word = word.upper()

        for r in range(rows):
            for c in range(cols):
                for dr, dc in self.DIRECTIONS:
                    coords = []
                    for i, ch in enumerate(word):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc].upper() == ch:
                            coords.append((nr, nc))
                        else:
                            break
                    if len(coords) == len(word):
                        return coords
        return None

    def find_and_visualize(self) -> Message:
        # Parse grid
        try:
            grid_text = self.letter_grid_json
            if hasattr(grid_text, "text"):
                grid_text = grid_text.text
            grid = json.loads(grid_text)
        except Exception as e:
            return Message(
                text=f"<p>Error parsing grid JSON: {e}</p>",
                sender="Machine",
                sender_name="WordGridFinder",
            )

        # Parse words
        word_list_raw = self.word_list
        if hasattr(word_list_raw, "text"):
            word_list_raw = word_list_raw.text
        words = [w.strip().upper() for w in word_list_raw.replace("\n", ",").split(",") if w.strip()]

        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0

        # Find each word and track highlighted cells
        highlighted = {}  # (r, c) -> color
        results = []

        for idx, word in enumerate(words):
            color = self.COLORS[idx % len(self.COLORS)]
            coords = self.find_word(grid, word)
            if coords:
                for r, c in coords:
                    highlighted[(r, c)] = color
                results.append(f'<li style="color:{color}; font-weight:bold;">✓ {word}</li>')
            else:
                results.append(f'<li style="color:#aaa;">✗ {word} (not found)</li>')

        # Build HTML grid table
        cell_size = "36px"
        table_rows = ""
        for r in range(rows):
            row_html = ""
            for c in range(cols):
                letter = grid[r][c].upper()
                bg = highlighted.get((r, c), "transparent")
                color = "#000" if bg != "transparent" else "#ccc"
                row_html += (
                    f'<td style="width:{cell_size};height:{cell_size};text-align:center;'
                    f'vertical-align:middle;font-weight:bold;font-size:14px;'
                    f'background:{bg};color:{color};border:1px solid #333;'
                    f'border-radius:4px;">{letter}</td>'
                )
            table_rows += f"<tr>{row_html}</tr>"

        word_list_html = "\n".join(results)

        html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
    h2 {{ color: #4ECDC4; }}
    table {{ border-collapse: separate; border-spacing: 3px; margin-bottom: 30px; }}
    ul {{ list-style: none; padding: 0; columns: 2; }}
    li {{ padding: 4px 8px; margin: 2px 0; font-size: 15px; }}
    .container {{ display: flex; gap: 40px; flex-wrap: wrap; }}
    .word-list {{ background: #16213e; padding: 16px; border-radius: 8px; min-width: 200px; }}
    .word-list h3 {{ color: #4ECDC4; margin-top: 0; }}
  </style>
</head>
<body>
  <h2>Word Grid Finder</h2>
  <div class="container">
    <div>
      <table>{table_rows}</table>
    </div>
    <div class="word-list">
      <h3>Words</h3>
      <ul>{word_list_html}</ul>
    </div>
  </div>
</body>
</html>
"""

        return Message(
            text=html,
            sender="Machine",
            sender_name="WordGridFinder",
        )