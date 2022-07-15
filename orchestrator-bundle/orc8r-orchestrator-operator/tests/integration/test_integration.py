#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
from pathlib import Path
from typing import Union

import pytest
import yaml
from pytest_operator.plugin import OpsTest  # type: ignore[import]  # noqa: F401

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
CERTIFIER_METADATA = yaml.safe_load(Path("../orc8r-certifier-operator/metadata.yaml").read_text())
ACCESSD_METADATA = yaml.safe_load(Path("../orc8r-accessd-operator/metadata.yaml").read_text())
APPLICATION_NAME = "orc8r-orchestrator"
CHARM_NAME = "magma-orc8r-orchestrator"
CERTIFIER_APPLICATION_NAME = "orc8r-certifier"
CERTIFIER_CHARM_NAME = "magma-orc8r-certifier"
CERTIFIER_CHARM_FILE_NAME = "magma-orc8r-certifier_ubuntu-20.04-amd64.charm"
ACCESSD_APPLICATION_NAME = "orc8r-accessd"
ACCESSD_CHARM_NAME = "magma-orc8r-accessd"
ACCESSD_CHARM_FILE_NAME = "magma-orc8r-accessd_ubuntu-20.04-amd64.charm"


class TestOrchestrator:
    @pytest.fixture(scope="module")
    @pytest.mark.abort_on_fail
    async def setup(self, ops_test):
        await self._deploy_postgresql(ops_test)
        await self._deploy_prometheus_cache(ops_test)
        await self._deploy_orc8r_certifier(ops_test)
        await self._deploy_orc8r_accessd(ops_test)

    @staticmethod
    async def _deploy_postgresql(ops_test):
        await ops_test.model.deploy("postgresql-k8s", application_name="postgresql-k8s")
        await ops_test.model.wait_for_idle(apps=["postgresql-k8s"], status="active", timeout=1000)

    @staticmethod
    async def _deploy_prometheus_cache(ops_test):
        await ops_test.model.deploy(
            "prometheus-edge-hub",
            application_name="orc8r-prometheus-cache",
            channel="edge",
            trust=True,
        )

    async def _deploy_orc8r_accessd(self, ops_test):
        accessd_charm = self._find_charm("../orc8r-accessd-operator", ACCESSD_CHARM_FILE_NAME)
        if not accessd_charm:
            accessd_charm = await ops_test.build_charm("../orc8r-accessd-operator/")
            resources = {
                f"{ACCESSD_CHARM_NAME}-image": ACCESSD_METADATA["resources"][
                    f"{ACCESSD_CHARM_NAME}-image"
                ]["upstream-source"],
            }
        await ops_test.model.deploy(
            accessd_charm,
            resources=resources,
            application_name=ACCESSD_APPLICATION_NAME,
            trust=True,
        )
        await ops_test.model.wait_for_idle(
            apps=[ACCESSD_APPLICATION_NAME], status="blocked", timeout=1000
        )
        await ops_test.model.add_relation(
            relation1=ACCESSD_APPLICATION_NAME, relation2="postgresql-k8s:db"
        )
        await ops_test.model.wait_for_idle(
            apps=[ACCESSD_APPLICATION_NAME], status="active", timeout=1000
        )

    async def _deploy_orc8r_certifier(self, ops_test):
        certifier_charm = self._find_charm(
            "../orc8r-certifier-operator", CERTIFIER_CHARM_FILE_NAME
        )
        if not certifier_charm:
            certifier_charm = await ops_test.build_charm("../orc8r-certifier-operator/")
        resources = {
            f"{CERTIFIER_CHARM_NAME}-image": CERTIFIER_METADATA["resources"][
                f"{CERTIFIER_CHARM_NAME}-image"
            ]["upstream-source"],
        }
        await ops_test.model.deploy(
            certifier_charm,
            resources=resources,
            application_name=CERTIFIER_APPLICATION_NAME,
            config={"domain": "example.com"},
            trust=True,
        )
        await ops_test.model.wait_for_idle(
            apps=[CERTIFIER_APPLICATION_NAME], status="blocked", timeout=1000
        )
        await ops_test.model.add_relation(
            relation1=CERTIFIER_APPLICATION_NAME, relation2="postgresql-k8s:db"
        )
        await ops_test.model.wait_for_idle(
            apps=[CERTIFIER_APPLICATION_NAME], status="active", timeout=1000
        )

    @pytest.fixture(scope="module")
    @pytest.mark.abort_on_fail
    async def build_and_deploy(self, ops_test, setup):
        charm = await ops_test.build_charm(".")
        resources = {
            f"{CHARM_NAME}-image": METADATA["resources"][f"{CHARM_NAME}-image"]["upstream-source"],
        }
        await ops_test.model.deploy(
            charm, resources=resources, application_name=APPLICATION_NAME, trust=True
        )

    @pytest.mark.abort_on_fail
    async def test_wait_for_blocked_status(self, ops_test, setup, build_and_deploy):
        await ops_test.model.wait_for_idle(apps=[APPLICATION_NAME], status="blocked", timeout=1000)

    async def test_relate_and_wait_for_idle(self, ops_test, setup, build_and_deploy):
        await ops_test.model.add_relation(
            relation1=APPLICATION_NAME, relation2="orc8r-certifier:magma-orc8r-certifier"
        )
        await ops_test.model.add_relation(
            relation1=APPLICATION_NAME, relation2="orc8r-prometheus-cache:metrics-endpoint"
        )
        await ops_test.model.add_relation(
            relation1=APPLICATION_NAME, relation2="orc8r-accessd:magma-orc8r-accessd"
        )
        await ops_test.model.wait_for_idle(apps=[APPLICATION_NAME], status="active", timeout=1000)

    @staticmethod
    def _find_charm(charm_dir: str, charm_file_name: str) -> Union[str, None]:
        for root, _, files in os.walk(charm_dir):
            for file in files:
                if file == charm_file_name:
                    return os.path.join(root, file)
        return None
