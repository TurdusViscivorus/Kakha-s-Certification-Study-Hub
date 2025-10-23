"""Analytics service generating dashboards and reports."""
from __future__ import annotations

import datetime as dt
import io
from dataclasses import dataclass
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ..database import session_scope
from ..repositories.analytics_repository import AnalyticsRepository


@dataclass
class StudySummary:
    heatmap_path: str
    retention_curve_path: str
    radar_chart_path: str
    confidence_scatter_path: str


class AnalyticsService:
    def __init__(self, output_dir: str) -> None:
        self._output_dir = output_dir

    def _save_plot(self, fig, name: str) -> str:
        path = f"{self._output_dir}/{name}.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def generate_summary(self, user_id: int) -> StudySummary:
        with session_scope() as session:
            repo = AnalyticsRepository(session)
            study_days = repo.get_study_days(user_id)
            attempts = repo.get_recent_quiz_attempts(user_id)
        dates = [day.date for day in study_days]
        minutes = [day.minutes_spent for day in study_days]
        cards = [day.cards_reviewed for day in study_days]

        fig, ax = plt.subplots(figsize=(8, 2))
        ax.bar(dates, minutes)
        ax.set_title("Study Minutes")
        ax.set_ylabel("Minutes")
        heatmap_path = self._save_plot(fig, "study_heatmap")

        retention_days = range(1, len(cards) + 1)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(list(retention_days), cards)
        ax.set_title("Retention Curve")
        ax.set_xlabel("Day")
        ax.set_ylabel("Cards Reviewed")
        retention_path = self._save_plot(fig, "retention_curve")

        sections = {}
        for attempt in attempts:
            for response in attempt.responses:
                metadata = (
                    response.question.metadata_json
                    if response.question and response.question.metadata_json
                    else {}
                )
                section = metadata.get("section", "General")
                sections.setdefault(section, 0)
                sections[section] += 1
        fig = plt.figure(figsize=(5, 5))
        ax = fig.add_subplot(111, polar=True)
        labels = list(sections.keys()) or ["General"]
        values = list(sections.values()) or [1]
        angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
        values += values[:1]
        angles += angles[:1]
        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)
        ax.set_thetagrids([a * 180 / 3.14159 for a in angles[:-1]], labels)
        radar_path = self._save_plot(fig, "domain_radar")

        fig, ax = plt.subplots(figsize=(6, 4))
        accuracy = [float(attempt.score or 0) for attempt in attempts]
        confidence = [
            response.confidence or 0
            for attempt in attempts
            for response in attempt.responses
        ] or [0]
        ax.scatter(confidence[: len(accuracy)], accuracy)
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Accuracy")
        ax.set_title("Confidence vs Accuracy")
        scatter_path = self._save_plot(fig, "confidence_scatter")

        return StudySummary(
            heatmap_path=heatmap_path,
            retention_curve_path=retention_path,
            radar_chart_path=radar_path,
            confidence_scatter_path=scatter_path,
        )

    def export_weekly_pdf(self, user_id: int, output_path: str) -> None:
        summary = self.generate_summary(user_id)
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setTitle("Weekly Review")
        c.drawString(72, 720, "Weekly Study Summary")
        y = 660
        for label, path in [
            ("Study Heatmap", summary.heatmap_path),
            ("Retention Curve", summary.retention_curve_path),
            ("Domain Radar", summary.radar_chart_path),
            ("Confidence Scatter", summary.confidence_scatter_path),
        ]:
            c.drawString(72, y, label)
            y -= 14
            c.drawImage(path, 72, y - 180, width=400, height=180)
            y -= 200
        c.save()
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())
