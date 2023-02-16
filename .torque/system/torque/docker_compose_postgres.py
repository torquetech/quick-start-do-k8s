# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""DOCSTRING"""

import hashlib

import jinja2

from torque import docker_compose
from torque import postgres
from torque import v1
from torque.v1.utils import load_and_render_yaml_from_package, load_and_render_template_from_package


class V1Provider(v1.provider.Provider):
    """DOCSTRING"""


class V1Implementation(v1.bond.Bond):
    """DOCSTRING"""

    PROVIDER = V1Provider
    IMPLEMENTS = postgres.V1ImplementationInterface

    CONFIGURATION = {
        "defaults": {
            "version": "14"
        },
        "schema": {
            "version": str
        }
    }

    @classmethod
    def on_requirements(cls) -> dict[str, object]:
        """DOCSTRING"""

        return {
            "dc": {
                "interface": docker_compose.V1Provider,
                "required": True
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._databases = {}
        self._users = {}

        with self.interfaces.dc as p:
            p.add_hook("apply-objects", self._apply)

    def _create_access(self, database: str, user: str):
        """DOCSTRING"""

        with self.context as ctx:
            if database not in self._databases:
                self._databases[database] = set()

            if user not in self._users:
                self._users[user] = ctx.secret(self.name, user)

            self._databases[database].add(user)

            return self._users[user]

    def _apply(self):
        """DOCSTRING"""

        image = f"postgres:{self.configuration['version']}"
        password = self._create_access("postgres", "postgres")

        local_sql_path = f"{self.context.path()}/{self.name}.sql"
        external_sql_path = f"{self.context.external_path()}/{self.name}.sql"

        sql = load_and_render_template_from_package(
            'docker-compose-postgres',
            'init.sql',
            {
                "databases": self._databases,
                "users": self._users
            }
        )
        sql_hash = hashlib.sha1(bytes(sql, encoding="utf-8"))

        with open(local_sql_path, "w", encoding="utf-8") as f:
            f.write(sql)

        self.interfaces.dc.add_object("volumes", self.name, {})

        self.interfaces.dc.add_object("configs", self.name, {
            "file": external_sql_path
        })

        service_init_config = load_and_render_yaml_from_package(
            'docker-compose-postgres',
            'service-init.yaml',
            {
                "image_name": image,
                "sql_hash": sql_hash.hexdigest(),
                "component_name": self.name,
                "password": password
            }
        )
        self.interfaces.dc.add_object(
            "services",
            f"{self.name}-init",
            service_init_config
        )

        service_config = load_and_render_yaml_from_package(
            'docker-compose-postgres',
            'service.yaml',
            {
                "image_name": image,
                "component_name": self.name,
                "password": password,
                "sql_hash": sql_hash.hexdigest(),
            }
        )
        self.interfaces.dc.add_object("services", self.name, service_config)

    def auth(self, database: str, user: str) -> v1.utils.Future[postgres.Authorization]:
        """DOCSTRING"""

        return v1.utils.Future(postgres.Authorization(database,
                                                      user,
                                                      self._create_access(database, user)))

    def service(self) -> v1.utils.Future[postgres.Service]:
        """DOCSTRING"""

        return v1.utils.Future(postgres.Service(self.name, 5432, {
            "sslmode": "disable"
        }))


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
