

from mdplus.core.environments.base import MdpEnvironment
from mdplus.util.parser.ros2_parser import Package


class Ros2Environment(MdpEnvironment):
    def __init__(self, workspace, name):
        super().__init__(workspace, name)

        self.packages = Package.getPackages(self.workspace.root_path)