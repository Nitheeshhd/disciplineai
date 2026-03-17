from __future__ import annotations

from io import BytesIO

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render_weekly_productivity_chart(
    points: list[dict[str, float | str]],
    title: str = "Weekly Productivity",
) -> BytesIO:
    labels = [point["date"][5:] for point in points]
    values = [float(point["value"]) for point in points]
    habits = [float(point["habits"]) for point in points]

    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=130)
    fig.patch.set_facecolor("#F7F9FD")
    ax1.set_facecolor("#FFFFFF")

    ax1.plot(
        labels,
        values,
        color="#2C7BE5",
        linewidth=2.2,
        marker="o",
        markersize=5,
        label="Productivity Value",
    )
    ax1.fill_between(labels, values, color="#2C7BE5", alpha=0.12)
    ax1.set_ylabel("Total Value", color="#2C7BE5")
    ax1.tick_params(axis="y", labelcolor="#2C7BE5")
    ax1.grid(alpha=0.25, linestyle="--")

    ax2 = ax1.twinx()
    ax2.bar(labels, habits, color="#34C38F", alpha=0.35, label="Habit Logs")
    ax2.set_ylabel("Habit Logs", color="#34C38F")
    ax2.tick_params(axis="y", labelcolor="#34C38F")

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    image = BytesIO()
    fig.savefig(image, format="png")
    plt.close(fig)
    image.seek(0)
    return image
