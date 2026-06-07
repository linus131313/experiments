"""Fairness and performance evaluation for the loan risk scorer."""

import logging

logger = logging.getLogger(__name__)


def compute_accuracy(y_true, y_pred):
    correct = sum(a == b for a, b in zip(y_true, y_pred))
    return correct / len(y_true) if y_true else 0.0


def disparate_impact_ratio(group_a_rate, group_b_rate):
    """Return the ratio of positive outcome rates between two groups."""
    if group_b_rate == 0:
        return float("inf")
    return group_a_rate / group_b_rate


def run_eval(y_true, y_pred, groups):
    acc = compute_accuracy(y_true, y_pred)
    logger.info("Accuracy: %.3f", acc)

    group_rates = {}
    for label in set(groups):
        indices = [i for i, g in enumerate(groups) if g == label]
        approved = sum(y_pred[i] == 1 for i in indices)
        group_rates[label] = approved / len(indices) if indices else 0.0

    labels = list(group_rates)
    if len(labels) >= 2:
        ratio = disparate_impact_ratio(group_rates[labels[0]], group_rates[labels[1]])
        logger.info(
            "Disparate impact ratio (%s vs %s): %.3f", labels[0], labels[1], ratio
        )
        if ratio < 0.8 or ratio > 1.25:
            logger.warning("Disparate impact outside acceptable range - review required")

    return {"accuracy": acc, "group_rates": group_rates}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    y_true = [1, 0, 1, 1, 0]
    y_pred = [1, 0, 0, 1, 0]
    groups = ["A", "B", "A", "B", "A"]
    results = run_eval(y_true, y_pred, groups)
    print(results)
