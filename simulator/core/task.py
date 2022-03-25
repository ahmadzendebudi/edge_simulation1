class Task:
    def __init__(self, size: int, workload: int, nodeId: int) -> None:
        self._size = size
        self._workload = workload
        self._nodeId = nodeId
    
    def setup(self, id: int) -> None:
        self._id = id
        
    def id(self):
        return self._id
    def size(self):
        return self._size
    def workload(self):
        return self._workload
    def mobileNodeId(self):
        return self._mobileNodeId
    
    def __str__(self) -> str:
        return ("Task//id:" + str(self._id) + " size:" + str(self._size) +
                " workload:" + str(self._workload) + " nodeId:" + str(self._mobileNodeId))