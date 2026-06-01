"""
splash image generator.
outputs: assets/splash.png
run once before pyinstaller build.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, H = 7.6, 2.8  # inches (760x280px @100dpi)

fig, ax = plt.subplots(figsize=(W, H))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#1a1a2e")

for i, alpha in enumerate([0.08, 0.05, 0.03]):
    ax.axhspan(0.55 + i * 0.08, 0.63 + i * 0.08, color="#4a9eff", alpha=alpha)

ax.text(0.5, 0.62, "XRD Analysis", ha="center", va="center",
        fontsize=36, color="#e8f4fd", fontweight="bold",
        fontfamily="sans-serif", transform=ax.transAxes)

ax.text(0.5, 0.38, "X-Ray Diffraction Data Plotter", ha="center", va="center",
        fontsize=13, color="#8ab4d4", transform=ax.transAxes)

ax.text(0.5, 0.16, "Loading...", ha="center", va="center",
        fontsize=10, color="#5a7a9a", transform=ax.transAxes)

ax.axhline(y=0.27, xmin=0.2, xmax=0.8, color="#4a9eff", linewidth=0.8, alpha=0.5)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

out = os.path.join("assets", "splash.png")
os.makedirs("assets", exist_ok=True)
plt.savefig(out, dpi=100, bbox_inches="tight", pad_inches=0, facecolor=fig.get_facecolor())
plt.close()
print("splash.png generated:", out)
