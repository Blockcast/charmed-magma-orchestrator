# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import PropertyMock, patch

from ops.testing import Harness

from charm import MagmaOrc8rMetricsdCharm


class TestCharm(unittest.TestCase):
    @patch(
        "charm.KubernetesServicePatch",
        lambda charm, ports, additional_labels, additional_annotations: None,
    )
    def setUp(self):
        self.harness = Harness(MagmaOrc8rMetricsdCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_given_initial_status_when_get_pebble_plan_then_content_is_empty(self):
        initial_plan = self.harness.get_container_pebble_plan("magma-orc8r-metricsd")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")

    @patch("charm.MagmaOrc8rMetricsdCharm._namespace", new_callable=PropertyMock)
    def test_given_pebble_ready_when_get_pebble_plan_then_plan_is_filled_with_orc8r_service_content(  # noqa: E501
        self, patch_namespace
    ):
        namespace = "whatever"
        patch_namespace.return_value = namespace
        expected_plan = {
            "services": {
                "magma-orc8r-metricsd": {
                    "override": "replace",
                    "summary": "magma-orc8r-metricsd",
                    "startup": "enabled",
                    "command": "/usr/bin/envdir "
                    "/var/opt/magma/envdir "
                    "/var/opt/magma/bin/metricsd "
                    "-run_echo_server=true "
                    "-logtostderr=true "
                    "-v=0",
                    "environment": {
                        "SERVICE_HOSTNAME": "magma-orc8r-metricsd",
                        "SERVICE_REGISTRY_MODE": "k8s",
                        "SERVICE_REGISTRY_NAMESPACE": namespace,
                    },
                }
            },
        }
        container = self.harness.model.unit.get_container("magma-orc8r-metricsd")
        self.harness.charm.on.magma_orc8r_metricsd_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("magma-orc8r-metricsd").to_dict()
        self.assertEqual(expected_plan, updated_plan)
