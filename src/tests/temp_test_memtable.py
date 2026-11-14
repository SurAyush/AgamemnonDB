from storage.memtable import Memtable

db = Memtable()

# Insert vectors
db.insert(
    101,
    [1.0, 0.0, 0.0],
    {"title": "Vector A"}
)

db.insert(
    102,
    [0.0, 1.0, 0.0],
    {"title": "Vector B"}
)

db.insert(
    103,
    [0.9, 0.1, 0.0],
    {"title": "Vector C"}
)

# Search
results = db.search(
    query=[1.0, 0.0, 0.0],
    k=2
)

for result in results:
    print(result)

# Delete
print("Deleted:", db.delete(103))

# Search again
print(db.search([1.0, 0.0, 0.0], k=5))

print("Memtable size:", len(db))
