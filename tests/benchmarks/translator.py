from dataproc.conf import Config
from dataproc.utils import Memit, Timeit
from dataproc.words.transformers.translators import translate_texts, translate_texts_bg


def small_corpus_es():
    with open(f"{Config.BASE_PATH}/tests/small_corpus_es.txt") as f:
        data = f.read()
    texts = data.split(".")
    return texts


@Memit
@Timeit
def measure_translation_simple():
    texts = small_corpus_es()
    _texts = translate_texts_bg(from_to="es-en", texts=texts, n_jobs=1)


@Memit
@Timeit
def measure_translation_bg():
    texts = small_corpus_es()
    _texts = translate_texts_bg(from_to="es-en", texts=texts, n_jobs=2)


if __name__ == "__main__":

    print("Running test with one proc")
    measure_translation_simple()
    print("Running test with two proc in bg")
    measure_translation_bg()
