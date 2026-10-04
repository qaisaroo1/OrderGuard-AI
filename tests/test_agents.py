import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from core.agents import MultiAgentCoordinator
from core.pipeline import LegalExtractionPipeline
from core.schemas import LegalActionMap


class MultiAgentCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = MultiAgentCoordinator(api_key="test-key")
        self.empty_map = LegalActionMap(
            metadata=LegalExtractionPipeline()._get_mock_action_map().metadata,
            actions=[],
        )
        self.action_map = LegalExtractionPipeline()._get_mock_action_map()
        self.coordinator.client = Mock()

    @staticmethod
    def response_for(action_map):
        return SimpleNamespace(parsed=action_map, text=action_map.model_dump_json())

    def test_returns_empty_result_without_spending_a_second_model_call(self):
        self.coordinator.client.models.generate_content.return_value = (
            self.response_for(self.empty_map)
        )

        result = self.coordinator._run_ai_pipeline(
            "The respondent shall file a reply within 14 days.",
            use_mock_fallback=False,
        )

        self.assertEqual(result.actions, [])
        self.assertEqual(result.total_obligations, 0)
        self.coordinator.client.models.generate_content.assert_called_once()

    def test_empty_result_does_not_trigger_additional_model_calls(self):
        self.coordinator.client.models.generate_content.return_value = (
            self.response_for(self.empty_map)
        )

        result = self.coordinator._run_ai_pipeline(
            "The respondent shall file a reply within 14 days.",
            use_mock_fallback=False,
        )

        self.assertEqual(result.actions, [])
        self.assertEqual(result.total_obligations, 0)
        self.coordinator.client.models.generate_content.assert_called_once()

    def test_empty_result_does_not_turn_into_unrelated_demo_data(self):
        self.coordinator.client.models.generate_content.return_value = (
            self.response_for(self.empty_map)
        )

        result = self.coordinator._run_ai_pipeline(
            "The respondent shall file a reply within 14 days.",
            use_mock_fallback=True,
        )

        self.assertEqual(result.actions, [])
        self.coordinator.client.models.generate_content.assert_called_once()
