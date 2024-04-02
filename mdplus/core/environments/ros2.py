from mdplus.core.environments.base import MdpEnvironment
from mdplus.util.parser.ros2_parser import Package


class Ros2Environment(MdpEnvironment):
    """
    ROS Environment parsing ROS 2 packages in the current workspace.
    """

    def __init__(self, workspace, name):
        super().__init__(workspace, name)

        self.packages = Package.getPackages(self.workspace.root_path)
        """ROS 2 packages found in the workspace."""
