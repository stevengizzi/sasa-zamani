"""Tests for scripts/backfill_labels.py."""

from unittest.mock import MagicMock, patch

from scripts.backfill_labels import backfill_telegram_labels


class TestBackfillLabels:
    """Tests for the backfill_telegram_labels function."""

    @patch("scripts.backfill_labels.generate_event_label")
    @patch("scripts.backfill_labels.get_db")
    def test_backfill_updates_label(
        self, mock_get_db: MagicMock, mock_generate: MagicMock
    ) -> None:
        """Backfill fetches telegram events, generates labels, and updates each row."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        fake_events = [
            {"id": "evt-1", "label": "old label one", "note": "I went to the park today"},
            {"id": "evt-2", "label": "old label two", "note": "Had coffee with a friend"},
        ]

        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.execute.return_value = MagicMock(data=fake_events)
        mock_db.table.return_value.select.return_value = select_chain

        update_chain = MagicMock()
        update_chain.eq.return_value = update_chain
        mock_db.table.return_value.update.return_value = update_chain

        mock_generate.side_effect = ["Park Visit Today", "Coffee With Friend"]

        backfill_telegram_labels()

        assert mock_generate.call_count == 2
        mock_generate.assert_any_call("I went to the park today")
        mock_generate.assert_any_call("Had coffee with a friend")

        assert mock_db.table.return_value.update.call_count == 2
        mock_db.table.return_value.update.assert_any_call({"label": "Park Visit Today"})
        mock_db.table.return_value.update.assert_any_call({"label": "Coffee With Friend"})

    @patch("scripts.backfill_labels.generate_event_label")
    @patch("scripts.backfill_labels.get_db")
    def test_backfill_skips_on_label_failure(
        self, mock_get_db: MagicMock, mock_generate: MagicMock
    ) -> None:
        """Backfill skips events where label generation fails and continues."""
        from app.segmentation import SegmentationError

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        fake_events = [
            {"id": "evt-1", "label": "old", "note": "note one"},
            {"id": "evt-2", "label": "old", "note": "note two"},
        ]

        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.execute.return_value = MagicMock(data=fake_events)
        mock_db.table.return_value.select.return_value = select_chain

        update_chain = MagicMock()
        update_chain.eq.return_value = update_chain
        mock_db.table.return_value.update.return_value = update_chain

        mock_generate.side_effect = [
            SegmentationError("API failed"),
            "Good Label",
        ]

        backfill_telegram_labels()

        assert mock_db.table.return_value.update.call_count == 1
        mock_db.table.return_value.update.assert_called_once_with({"label": "Good Label"})
