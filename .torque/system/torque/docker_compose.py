# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""DOCSTRING"""

import io
import os
import subprocess
import threading
import yaml

from torque import v1
from torque.v1.utils import load_and_render_yaml_from_package


class V1Provider(v1.provider.Provider):
    """DOCSTRING"""

    CONFIGURATION = {
        "defaults": {},
        "schema": {
            v1.schema.Optional("overrides"): dict
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._objects = load_and_render_yaml_from_package(
            "docker-compose",
            "compose.yaml",
            {
                "deployment_name": self.context.deployment_name
            }
        )

        self._lock = threading.Lock()

        with self as p:
            p.add_hook("apply", self._apply)
            p.add_hook("delete", self._delete)

    def _apply(self):
        """DOCSTRING"""

        def get_docker_compose_yaml(
            objects: dict
        ) -> str:
            yaml_dump = io.StringIO()
            yaml.safe_dump(
                objects,
                stream=yaml_dump,
                default_flow_style=False,
                sort_keys=False,
                width=float("inf")
            )
            docker_compose_yaml = (
                yaml_dump.getvalue()
                # Transform every "__template_start" and "__template_end" into YAML comment.
                .replace("__template_start: ", "# ")
                .replace("__template_end: ", "# ")
            )
            return docker_compose_yaml

        compose = f"{self.context.path()}/docker-compose.yaml"

        objects = v1.utils.resolve_futures(self._objects)
        objects = v1.utils.merge_dicts(objects, self.configuration.get("overrides", {}))

        docker_compose_yaml = get_docker_compose_yaml(objects)
        with open(compose, "w", encoding="utf8") as file:
            file.write(docker_compose_yaml)

        cmd = [
            "docker", "compose",
            "up", "-d",
            "--remove-orphans"
        ]

        print(f"+ {' '.join(cmd)}")
        subprocess.run(cmd, env=os.environ, cwd=self.context.path(), check=True)

    def _delete(self):
        """DOCSTRING"""

        cmd = [
            "docker", "compose",
            "down",
            "--volumes"
        ]

        print(f"+ {' '.join(cmd)}")
        subprocess.run(cmd, env=os.environ, cwd=self.context.path(), check=False)

    def add_object(self, section: str, name: str, obj: dict[str, object]):
        """DOCSTRING"""

        with self._lock:
            if section not in self._objects:
                self._objects[section] = {}

            self._objects[section][name] = obj

            return (section, name)

    def object(self, section: str, name: str) -> dict[str, object]:
        """DOCSTRING"""

        if section not in self._objects:
            raise v1.exceptions.RuntimeError(f"{section}: section not found")

        if name not in self._objects[section]:
            raise v1.exceptions.RuntimeError(f"{name}: object not found")

        return self._objects[section][name]

    def objects(self) -> dict[str, object]:
        """DOCSTRING"""

        return self._objects


repository = {
    "v1": {
        "providers": [
            V1Provider
        ]
    }
}
