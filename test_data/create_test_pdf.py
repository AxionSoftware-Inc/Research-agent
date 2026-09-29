from pathlib import Path
import fitz

out = Path(r"D:\AI-ResearchAssistant\test_data\formula_test.pdf")
doc = fitz.open()
page = doc.new_page(width=900, height=650)
page.insert_text((60, 60), "Quantum transport test", fontsize=24, fontname="hebo")
page.insert_text((60, 105), "For a one-dimensional wave packet, the normalized state is", fontsize=15)
page.insert_textbox((60, 130, 840, 230),
    "psi(x,t) = 1 / (2*pi*sigma_t^2)^(1/4) * exp[ -(x-x0-vt)^2/(4*sigma_t^2) + i/hbar*(p0*x - p0^2*t/(2*m)) ]\n\n"
    "sigma_t = sigma_0 * sqrt( 1 + (hbar*t/(2*m*sigma_0^2))^2 )",
    fontsize=18, fontname="tiro", lineheight=1.7, align=0)
page.insert_text((60, 275), "The measured error for three discretizations is shown below.", fontsize=15)
x0, y0 = 60, 320
cols = [140, 170, 170, 170]
rows = [42, 42, 42]
data = [
    ["Grid size N", "128", "256", "512"],
    ["Relative error", "1.7 x 10^-3", "4.2 x 10^-4", "1.0 x 10^-4"],
    ["Runtime (s)", "0.08", "0.31", "1.24"],
]
for r in range(len(rows)):
    y = y0 + sum(rows[:r])
    for c, w in enumerate(cols):
        x = x0 + sum(cols[:c])
        page.draw_rect(fitz.Rect(x, y, x+w, y+rows[r]), color=(0,0,0), fill=(0.93,0.93,0.93) if r == 0 else None, width=1)
        page.insert_text((x+10, y+27), data[r][c], fontsize=14, fontname="hebo" if r == 0 else "helv")
page.insert_text((60, 500), "The expected convergence rate is O(N^-2).", fontsize=16)
page.insert_text((60, 550), "Task: reconstruct this page faithfully as Markdown and LaTeX; preserve equations and table values.", fontsize=13)
doc.save(out)
doc.close()
print(out)
