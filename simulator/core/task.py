class Task:
    def __init__(self, id: int, size: int, workload: int, mobileNodeId: int) -> None:
        self._id = id
        self._size = size
        self._workload = workload
        self._mobileNodeId = mobileNodeId
    
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
                " workload:" + str(self._workload) + " mobileNodeId:" + str(self._mobileNodeId))