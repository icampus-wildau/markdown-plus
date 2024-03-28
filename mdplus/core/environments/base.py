from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mdplus.core.documents.structure import Workspace


class MdpEnvironment():
    def __init__(self, workspace: Workspace, name: str):
        self.workspace = workspace
        self.name = name
        


