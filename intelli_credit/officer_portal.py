"""
Officer Portal - Qualitative assessment interface for credit officers
Converts free-text notes into bounded score adjustments
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
import re

from data_models import OfficerNote, FlagCategory


# ============================================================================
# SENTIMENT DETECTION
# ============================================================================

# Keyword dictionaries for sentiment analysis
POSITIVE_KEYWORDS = [
    "strong", "excellent", "reliable", "good", "solid", "robust",
    "healthy", "stable", "improving", "growth", "positive", "trustworthy",
    "experienced", "capable", "sound", "adequate", "sufficient"
]

NEGATIVE_KEYWORDS = [
    "concern", "risk", "default", "weak", "poor", "inadequate",
    "insufficient", "declining", "deteriorating", "unstable", "volatile",
    "questionable", "doubtful", "risky", "problematic", "stressed",
    "overlevered", "aggressive", "warning", "red flag"
]


def detect_sentiment(note_text: str) -> str:
    """
    Detect sentiment in officer note using keyword matching.
    
    Args:
        note_text: Free-text note from credit officer
        
    Returns:
        "POSITIVE", "NEGATIVE", or "NEUTRAL"
    """
    if not note_text:
        return "NEUTRAL"
    
    # Convert to lowercase for matching
    text_lower = note_text.lower()
    
    # Count positive and negative keyword matches
    positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text_lower)
    negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text_lower)
    
    # Determine sentiment based on keyword counts
    if negative_count > positive_count:
        return "NEGATIVE"
    elif positive_count > negative_count:
        return "POSITIVE"
    else:
        return "NEUTRAL"


# ============================================================================
# NOTE PARSING AND ADJUSTMENT
# ============================================================================

def parse_note_to_adjustment(note_text: str, affected_c: str, manual_adjustment: Optional[float] = None) -> float:
    """
    Convert free-text note to bounded score adjustment.
    
    Rules:
    - If manual_adjustment provided, use it (already bounded by UI)
    - Otherwise, infer from sentiment:
      - NEGATIVE sentiment: -15 (moderate negative)
      - POSITIVE sentiment: +5 (moderate positive)
      - NEUTRAL sentiment: 0
    - Single note bounds: -25 to +10
    
    Args:
        note_text: Free-text note from credit officer
        affected_c: Which C is affected (CHARACTER, CAPACITY, etc.)
        manual_adjustment: Optional manual adjustment value from UI
        
    Returns:
        Bounded adjustment value (-25 to +10)
    """
    # If manual adjustment provided, use it (UI already enforces bounds)
    if manual_adjustment is not None:
        return max(-25.0, min(10.0, manual_adjustment))
    
    # Otherwise, infer from sentiment
    sentiment = detect_sentiment(note_text)
    
    if sentiment == "NEGATIVE":
        return -15.0
    elif sentiment == "POSITIVE":
        return 5.0
    else:
        return 0.0


def apply_officer_adjustments(
    base_scores: Dict[str, float],
    notes: List[OfficerNote]
) -> Dict[str, float]:
    """
    Apply bounded adjustments to base Five Cs scores.
    
    Rules:
    - Single note cap: -25 to +10
    - Total adjustment cap: -40 across all notes
    - If total < -40, scale all adjustments proportionally
    - Ensure adjusted scores remain within 10-100 bounds
    
    Args:
        base_scores: Dictionary with keys CHARACTER, CAPACITY, CAPITAL, COLLATERAL, CONDITIONS
        notes: List of OfficerNote objects
        
    Returns:
        Dictionary with adjusted scores (same keys as base_scores)
    """
    if not notes:
        return base_scores.copy()
    
    # Initialize adjusted scores
    adjusted_scores = base_scores.copy()
    
    # Group adjustments by affected C
    adjustments_by_c = {
        "CHARACTER": 0.0,
        "CAPACITY": 0.0,
        "CAPITAL": 0.0,
        "COLLATERAL": 0.0,
        "CONDITIONS": 0.0
    }
    
    # Accumulate adjustments for each C
    for note in notes:
        c_name = note.affected_c.value if isinstance(note.affected_c, FlagCategory) else note.affected_c
        adjustments_by_c[c_name] += note.adjustment
    
    # Calculate total adjustment
    total_adjustment = sum(adjustments_by_c.values())
    
    # If total adjustment exceeds -40, scale proportionally
    if total_adjustment < -40:
        scale_factor = -40.0 / total_adjustment
        for c_name in adjustments_by_c:
            adjustments_by_c[c_name] *= scale_factor
    
    # Apply adjustments to base scores
    for c_name, adjustment in adjustments_by_c.items():
        if c_name in adjusted_scores:
            adjusted_scores[c_name] = adjusted_scores[c_name] + adjustment
            # Ensure score remains within 10-100 bounds
            adjusted_scores[c_name] = max(10.0, min(100.0, adjusted_scores[c_name]))
    
    return adjusted_scores


# ============================================================================
# STREAMLIT UI FOR NOTE COLLECTION
# ============================================================================

def collect_officer_notes(company_name: str) -> List[OfficerNote]:
    """
    Streamlit UI for credit officers to add qualitative notes.
    
    Features:
    - Text area for free-text note input
    - Dropdown for affected C selection
    - Number input for adjustment (-25 to +10 bounds)
    - Add button to create note
    - Display existing notes with timestamps
    
    Args:
        company_name: Name of company being assessed
        
    Returns:
        List of OfficerNote objects
    """
    st.subheader(f"Officer Qualitative Assessment - {company_name}")
    
    # Initialize session state for notes if not exists
    if "officer_notes" not in st.session_state:
        st.session_state.officer_notes = []
    
    # Display instructions
    with st.expander("ℹ️ Instructions", expanded=False):
        st.markdown("""
        **Add qualitative notes to adjust credit scores:**
        
        - Write your assessment in the text area
        - Select which C (Character, Capacity, Capital, Collateral, Conditions) is affected
        - Specify adjustment: -25 to +10 points
        - Total adjustments capped at -40 across all notes
        - If total < -40, all adjustments scaled proportionally
        
        **Sentiment keywords:**
        - Positive: strong, excellent, reliable, good, solid, robust
        - Negative: concern, risk, default, weak, poor, inadequate
        """)
    
    # Form for adding new note
    with st.form("add_officer_note", clear_on_submit=True):
        st.markdown("### Add New Note")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            note_text = st.text_area(
                "Note Text",
                placeholder="Enter your qualitative assessment here...",
                height=100,
                help="Free-text note describing your assessment"
            )
        
        with col2:
            affected_c = st.selectbox(
                "Affected C",
                options=["CHARACTER", "CAPACITY", "CAPITAL", "COLLATERAL", "CONDITIONS"],
                help="Which credit dimension does this note affect?"
            )
            
            adjustment = st.number_input(
                "Score Adjustment",
                min_value=-25.0,
                max_value=10.0,
                value=0.0,
                step=1.0,
                help="Score adjustment: -25 (negative) to +10 (positive)"
            )
        
        submitted = st.form_submit_button("Add Note", use_container_width=True)
        
        if submitted:
            if not note_text.strip():
                st.error("Please enter note text")
            else:
                # Create new officer note
                new_note = OfficerNote(
                    note_text=note_text.strip(),
                    affected_c=FlagCategory[affected_c],
                    adjustment=adjustment,
                    timestamp=datetime.now().isoformat()
                )
                
                # Add to session state
                st.session_state.officer_notes.append(new_note)
                st.success(f"✅ Note added: {adjustment:+.1f} points to {affected_c}")
                st.rerun()
    
    # Display existing notes
    if st.session_state.officer_notes:
        st.markdown("### Existing Notes")
        
        # Calculate total adjustment
        total_adjustment = sum(note.adjustment for note in st.session_state.officer_notes)
        
        # Show warning if total exceeds -40
        if total_adjustment < -40:
            st.warning(f"⚠️ Total adjustment ({total_adjustment:.1f}) exceeds -40 cap. "
                      f"All adjustments will be scaled proportionally to -40.")
        
        # Display adjustment summary
        st.metric("Total Adjustment", f"{total_adjustment:+.1f} points")
        
        # Display notes in a table
        for idx, note in enumerate(st.session_state.officer_notes):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    sentiment = detect_sentiment(note.note_text)
                    sentiment_emoji = "😊" if sentiment == "POSITIVE" else "😟" if sentiment == "NEGATIVE" else "😐"
                    st.markdown(f"**{sentiment_emoji} {note.note_text}**")
                    st.caption(f"Added: {note.timestamp[:19]}")
                
                with col2:
                    st.markdown(f"**{note.affected_c.value}**")
                
                with col3:
                    color = "green" if note.adjustment > 0 else "red" if note.adjustment < 0 else "gray"
                    st.markdown(f":{color}[**{note.adjustment:+.1f}**]")
                
                # Delete button
                if st.button(f"🗑️ Delete", key=f"delete_note_{idx}"):
                    st.session_state.officer_notes.pop(idx)
                    st.rerun()
                
                st.divider()
    else:
        st.info("No officer notes added yet. Use the form above to add qualitative assessments.")
    
    return st.session_state.officer_notes


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_adjustment_summary(notes: List[OfficerNote]) -> Dict[str, float]:
    """
    Get summary of adjustments by C category.
    
    Args:
        notes: List of OfficerNote objects
        
    Returns:
        Dictionary mapping C name to total adjustment
    """
    summary = {
        "CHARACTER": 0.0,
        "CAPACITY": 0.0,
        "CAPITAL": 0.0,
        "COLLATERAL": 0.0,
        "CONDITIONS": 0.0
    }
    
    for note in notes:
        c_name = note.affected_c.value if isinstance(note.affected_c, FlagCategory) else note.affected_c
        summary[c_name] += note.adjustment
    
    return summary


def validate_adjustment_bounds(adjustment: float) -> bool:
    """
    Validate that adjustment is within bounds.
    
    Args:
        adjustment: Adjustment value to validate
        
    Returns:
        True if within bounds (-25 to +10), False otherwise
    """
    return -25.0 <= adjustment <= 10.0


def format_adjustment_display(adjustment: float) -> str:
    """
    Format adjustment for display with sign and color.
    
    Args:
        adjustment: Adjustment value
        
    Returns:
        Formatted string with sign
    """
    if adjustment > 0:
        return f"+{adjustment:.1f}"
    else:
        return f"{adjustment:.1f}"


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_sentiment_detection():
    """Test sentiment detection with sample notes"""
    test_cases = [
        ("Strong management team with excellent track record", "POSITIVE"),
        ("Concern about declining revenue and default risk", "NEGATIVE"),
        ("Company operates in manufacturing sector", "NEUTRAL"),
        ("Reliable cash flows and good collateral coverage", "POSITIVE"),
        ("Weak financial position with inadequate capital", "NEGATIVE"),
    ]
    
    print("Testing sentiment detection:")
    for note, expected in test_cases:
        result = detect_sentiment(note)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{note[:50]}...' -> {result} (expected {expected})")


def test_adjustment_application():
    """Test adjustment application with bounds"""
    base_scores = {
        "CHARACTER": 80.0,
        "CAPACITY": 70.0,
        "CAPITAL": 60.0,
        "COLLATERAL": 75.0,
        "CONDITIONS": 65.0
    }
    
    # Test case 1: Normal adjustments
    notes1 = [
        OfficerNote("Strong management", FlagCategory.CHARACTER, 5.0, datetime.now().isoformat()),
        OfficerNote("Revenue concerns", FlagCategory.CAPACITY, -10.0, datetime.now().isoformat()),
    ]
    
    adjusted1 = apply_officer_adjustments(base_scores, notes1)
    print("\nTest 1 - Normal adjustments:")
    print(f"CHARACTER: {base_scores['CHARACTER']} -> {adjusted1['CHARACTER']} (expected 85)")
    print(f"CAPACITY: {base_scores['CAPACITY']} -> {adjusted1['CAPACITY']} (expected 60)")
    
    # Test case 2: Exceeding -40 cap
    notes2 = [
        OfficerNote("Major concerns", FlagCategory.CHARACTER, -25.0, datetime.now().isoformat()),
        OfficerNote("Weak capacity", FlagCategory.CAPACITY, -25.0, datetime.now().isoformat()),
    ]
    
    adjusted2 = apply_officer_adjustments(base_scores, notes2)
    total_adj = sum(note.adjustment for note in notes2)
    print(f"\nTest 2 - Exceeding -40 cap (total: {total_adj}):")
    print(f"Adjustments should be scaled to -40 total")
    print(f"CHARACTER: {base_scores['CHARACTER']} -> {adjusted2['CHARACTER']}")
    print(f"CAPACITY: {base_scores['CAPACITY']} -> {adjusted2['CAPACITY']}")


if __name__ == "__main__":
    # Run tests
    test_sentiment_detection()
    test_adjustment_application()
