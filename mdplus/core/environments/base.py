from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdplus.core.documents.structure import Workspace


class MdpEnvironment:
    """
    Base class for environments.
    Environments store stuff for your workspace, that can be used by multiple generators.

    Inside your generator you can use an environment like:
    ```python
    env = self.workspace.get_environment("env_name", env_class=YourMdpEnvironmentClass)
    ```
    """

    def __init__(self, workspace: Workspace, name: str):
        """Create a new environment.

        Parameters
        ----------
        workspace : Workspace
            The parent workspace.
        name : str
            The name of the environment.
        """
        self.workspace = workspace
        self.name = name
