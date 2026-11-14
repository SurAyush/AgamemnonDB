from storage.memtable import Memtable
from storage.sstable import SSTable

memtable = Memtable()

memtable.insert(101, [1.0, 0.0, 0.0])
memtable.insert(102, [0.0, 1.0, 0.0])
memtable.insert(103, [0.9, 0.1, 0.0])

sstable = SSTable(
    dimension=3,
    path="data/segments/segment_001.bin"
)

sstable.build(memtable)

results = sstable.search(
    query=[1.0, 0.0, 0.0],
    k=2
)

print(results)