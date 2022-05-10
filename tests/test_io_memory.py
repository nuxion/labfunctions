from labfunctions.io import MemoryStore


def test_io_memory_store():

    ms = MemoryStore()
    ms["test"] = "hi"
    ms2 = MemoryStore()

    assert id(ms) == id(ms2)
    assert ms["test"] == ms2["test"]
