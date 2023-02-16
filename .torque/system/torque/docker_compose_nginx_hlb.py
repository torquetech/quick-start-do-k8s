# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""DOCSTRING"""

import hashlib

import jinja2

from torque import docker_compose
from torque import docker_compose_load_balancer
from torque import hlb
from torque import v1
from torque.v1.utils import load_and_render_template_from_package, load_and_render_yaml_from_package


class V1Provider(v1.provider.Provider):
    """DOCSTRING"""


class V1Implementation(v1.bond.Bond):
    """DOCSTRING"""

    PROVIDER = V1Provider
    IMPLEMENTS = hlb.V1ImplementationInterface

    CONFIGURATION = {
        "defaults": {
            "domain": "example.com"
        },
        "schema": {
            "domain": str
        }
    }

    @classmethod
    def on_requirements(cls) -> dict[str, object]:
        """DOCSTRING"""

        return {
            "dc": {
                "interface": docker_compose.V1Provider,
                "required": True
            },
            "lb": {
                "interface": docker_compose_load_balancer.V1Provider,
                "required": True
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._ingress_list = []

        with self.interfaces.dc as p:
            p.add_hook("apply-objects", self._apply)

    def _apply(self):
        """DOCSTRING"""

        ingress_list = [
            v1.utils.resolve_futures(i) for i in self._ingress_list
        ]

        domain = self.configuration["domain"]
        hosts = sorted(list({i.host for i in ingress_list}))

        self.interfaces.lb.add_entry(docker_compose_load_balancer.Entry(self.name,
                                                                        domain,
                                                                        hosts))

        conf = load_and_render_template_from_package(
            "docker-compose-nginx-hlb",
            "ingress.config",
            {
                "domain": domain,
                "hosts": hosts,
                "ingress_list": ingress_list
            }
        )
        conf_hash = hashlib.sha1(bytes(conf, encoding="utf-8"))

        local_conf = f"{self.context.path()}/{self.name}.conf"
        external_conf = f"{self.context.external_path()}/{self.name}.conf"

        with open(local_conf, "w", encoding="utf-8") as f:
            f.write(conf)

        self.interfaces.dc.add_object("configs", self.name, {
            "file": external_conf
        })

        service_config = load_and_render_yaml_from_package(
            "docker-compose-nginx-hlb",
            "service.yaml",
            {
                "component_name": self.name,
                "conf_hash": conf_hash.hexdigest()
            }
        )
        self.interfaces.dc.add_object("services", self.name, service_config)

    def add(self, ingress: hlb.Ingress):
        """DOCSTRING"""

        self._ingress_list.append(ingress)


repository = {
    "v1": {
        "providers": [
            V1Provider
        ],
        "bonds": [
            V1Implementation
        ]
    }
}
