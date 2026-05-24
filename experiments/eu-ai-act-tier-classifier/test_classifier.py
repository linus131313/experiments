"""Tests for the EU AI Act tier classifier."""

import pytest
from classifier import classify


def test_social_scoring_is_unacceptable():
    result = classify(
        "A government platform that assigns trustworthiness scores to citizens "
        "based on their financial behaviour and social media activity."
    )
    assert result.tier == "Unacceptable"
    assert any("Art. 5" in c for c in result.citations)


def test_emotion_detection_in_school_is_unacceptable():
    result = classify(
        "An AI system that detects emotional states of students in a classroom "
        "to flag disengagement for teachers."
    )
    assert result.tier == "Unacceptable"
    assert "Art. 5(1)(f)" in result.citations


def test_emotion_detection_outside_school_not_unacceptable():
    # Emotion detection without workplace/school context should not be Unacceptable
    result = classify(
        "An emotion recognition system integrated into a consumer smartwatch "
        "to provide wellness recommendations."
    )
    assert result.tier != "Unacceptable"


def test_hiring_tool_is_high_risk():
    result = classify(
        "An AI system that screens job applicants and ranks candidates for interview "
        "selection based on CV and video interview analysis."
    )
    assert result.tier == "High"
    assert any("Annex III" in c for c in result.citations)


def test_credit_scoring_is_high_risk():
    result = classify(
        "A creditworthiness assessment tool used by a bank to approve or reject loan applications."
    )
    assert result.tier == "High"


def test_chatbot_is_limited_risk():
    result = classify(
        "A customer support chatbot that answers product questions and processes returns."
    )
    assert result.tier == "Limited"
    assert any("Art. 50" in c for c in result.citations)


def test_deepfake_generator_is_limited_risk():
    result = classify(
        "A tool that produces synthetic video and audio of public figures for satire."
    )
    assert result.tier == "Limited"
    assert any("Art. 50" in c for c in result.citations)


def test_image_classifier_is_minimal():
    result = classify(
        "A convolutional network that classifies images of cats vs dogs for a pet photo app."
    )
    assert result.tier == "Minimal"


def test_spam_filter_is_minimal():
    result = classify(
        "An email spam filter that uses a trained Naive Bayes classifier to separate "
        "junk mail from legitimate messages."
    )
    assert result.tier == "Minimal"


def test_confidence_reflects_match_count():
    # Two or more rule hits should raise confidence to 'high'
    result = classify(
        "An AI tool that screens job applicants for hiring decisions and also "
        "evaluates creditworthiness for employee benefit entitlement programs."
    )
    assert result.tier == "High"
    assert result.confidence == "high"
