from src.models import Sentence

TEST_SENTENCES = [
    Sentence(
        text="To be or not to be, that is the question.",
        normalized_text="to be or not to be that is the question",
        source="test.txt",
        offset=1,
    ),
    Sentence(
        text="Python is a programming language.",
        normalized_text="python is a programming language",
        source="python.txt",
        offset=2,
    ),
    Sentence(
        text="All that glitters is not gold.",
        normalized_text="all that glitters is not gold",
        source="test.txt",
        offset=2,
    ),
]
