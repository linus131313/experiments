"""Tests for the rag-robustness-eval experiment."""

import unittest
from corpus import DOCUMENTS, QUERIES
from noise import char_noise, word_drop, truncate
from retriever import TFIDFRetriever, recall_at_k, mean_recall_at_k


class TestNoiseFunctions(unittest.TestCase):

    def test_char_noise_length_preserved(self):
        text = "Hello world this is a test sentence."
        noisy = char_noise(text, rate=0.5, seed=1)
        self.assertEqual(len(noisy), len(text))

    def test_char_noise_zero_rate_unchanged(self):
        text = "No noise should happen here."
        self.assertEqual(char_noise(text, rate=0.0), text)

    def test_word_drop_reduces_words(self):
        text = "one two three four five six seven eight nine ten"
        noisy = word_drop(text, rate=0.5, seed=7)
        self.assertLess(len(noisy.split()), len(text.split()))

    def test_truncate_shortens_text(self):
        text = "A" * 100
        self.assertEqual(len(truncate(text, 0.5)), 50)
        self.assertEqual(truncate(text, 1.0), text)


class TestRetriever(unittest.TestCase):

    def setUp(self):
        self.retriever = TFIDFRetriever()
        self.retriever.index(DOCUMENTS)

    def test_baseline_recall_high(self):
        score = mean_recall_at_k(self.retriever, QUERIES, k=5)
        self.assertGreaterEqual(score, 0.8, "Baseline recall@5 should be at least 0.8")

    def test_recall_at_k_perfect(self):
        self.assertEqual(recall_at_k(["a", "b", "c"], ["a", "b"]), 1.0)

    def test_recall_at_k_miss(self):
        self.assertEqual(recall_at_k(["x", "y"], ["a"]), 0.0)

    def test_heavy_char_noise_degrades_recall(self):
        noisy = {k: char_noise(v, rate=0.5) for k, v in DOCUMENTS.items()}
        noisy_retriever = TFIDFRetriever()
        noisy_retriever.index(noisy)
        baseline = mean_recall_at_k(self.retriever, QUERIES, k=5)
        degraded = mean_recall_at_k(noisy_retriever, QUERIES, k=5)
        self.assertLessEqual(degraded, baseline)

    def test_heavy_word_drop_degrades_recall(self):
        noisy = {k: word_drop(v, rate=0.7) for k, v in DOCUMENTS.items()}
        noisy_retriever = TFIDFRetriever()
        noisy_retriever.index(noisy)
        baseline = mean_recall_at_k(self.retriever, QUERIES, k=5)
        degraded = mean_recall_at_k(noisy_retriever, QUERIES, k=5)
        self.assertLessEqual(degraded, baseline)


if __name__ == "__main__":
    unittest.main()
