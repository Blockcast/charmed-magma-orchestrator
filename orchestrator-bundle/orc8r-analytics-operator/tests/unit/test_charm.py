# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import PropertyMock, patch

from ops.testing import Harness

from charm import MagmaOrc8rAnalyticsCharm


class TestCharm(unittest.TestCase):
    @patch("charm.KubernetesServicePatch", lambda charm, ports, additional_labels: None)
    def setUp(self):
        self.harness = Harness(MagmaOrc8rAnalyticsCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_given_initial_status_when_get_pebble_plan_then_content_is_empty(self):
        initial_plan = self.harness.get_container_pebble_plan("magma-orc8r-analytics")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")

    @patch("charm.MagmaOrc8rAnalyticsCharm._namespace", new_callable=PropertyMock)
    def test_given_pebble_ready_when_get_pebble_plan_then_plan_is_filled_with_orc8r_service_content(  # noqa: E501
        self, patch_namespace
    ):
        namespace = "whatever"
        patch_namespace.return_value = namespace
        expected_plan = {
            "services": {
                "magma-orc8r-analytics": {
                    "override": "replace",
                    "summary": "magma-orc8r-analytics",
                    "startup": "enabled",
                    "command": "/usr/bin/envdir "
                    "/var/opt/magma/envdir "
                    "/var/opt/magma/bin/analytics "
                    "-logtostderr=true -v=0",
                    "environment": {
                        "SERVICE_REGISTRY_MODE": "k8s",
                        "SERVICE_REGISTRY_NAMESPACE": namespace,
                    },
                }
            },
        }
        container = self.harness.model.unit.get_container("magma-orc8r-analytics")
        self.harness.charm.on.magma_orc8r_analytics_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("magma-orc8r-analytics").to_dict()
        self.assertEqual(expected_plan, updated_plan)
