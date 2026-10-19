import tkinter as tk
from TreasureGridModel import MyGridModel, EMPTY, STATIC_WALL, TREASURE, TRAP


class TreasureHuntGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Treasure Hunt Game")

        # Gets the grid from Dylon's code
        self.model = MyGridModel(8)

        # Set grid cell size
        self.cell_size = 60

        # Create a canvas to display the grid
        self.canvas = tk.Canvas(
            self.root,
            width=self.model.size * self.cell_size,
            height=self.model.size * self.cell_size,
            bg="white"
        )
        self.canvas.pack(padx=20, pady=20)

        # Button to regenerate the grid
        self.regenerate_button = tk.Button(
            self.root,
            text="Regenerate Grid",
            command=self.regenerate_grid
        )
        self.regenerate_button.pack(pady=(0, 20))

        # Draw the grid
        self.draw_grid()

    def regenerate_grid(self):
        self.model.generate_grid()
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for row in range(self.model.size):
            for col in range(self.model.size):
                cell = self.model.grid[row, col]

                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "white"
                symbol = ""

                if cell == STATIC_WALL:
                    color = "gray"
                    symbol = "#"
                elif cell == TREASURE:
                    color = "lightgreen"
                    symbol = "T"
                elif cell == TRAP:
                    color = "lightcoral"
                    symbol = "X"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="black"
                )

                if symbol:
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=symbol,
                        font=("Arial", 20, "bold")
                    )


if __name__ == "__main__":
    root = tk.Tk()
    app = TreasureHuntGUI(root)
    root.mainloop()
