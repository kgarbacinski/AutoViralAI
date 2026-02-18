"""Prompts for strategy adjustment in the learning pipeline."""

ADJUST_STRATEGY_SYSTEM = """\
You are a growth strategist optimizing a Threads account's content strategy.
Based on performance data and analysis, you update the strategy to improve results.
You balance exploration (trying new approaches) with exploitation (doubling down on what works)."""

ADJUST_STRATEGY_USER = """\
Update the content strategy based on the latest performance analysis.

## Performance Analysis

{analysis}

## Current Strategy

{current_strategy}

## All Pattern Performance Data

{all_pattern_performance}

## Account Niche

{niche_config}

## Instructions

Generate an updated ContentStrategy with:

1. **preferred_patterns**: Rank patterns by effectiveness (best first). Include at least 1-2
   newer/untested patterns for exploration.
2. **avoid_patterns**: Patterns that consistently underperform (at least 3 uses with poor results).
3. **optimal_posting_times**: Adjust based on any timing insights from the analysis.
4. **pillar_adjustments**: Adjust content pillar weights (positive = increase, negative = decrease).
   Changes should be small (-0.1 to +0.1) and always sum to ~0 across pillars.
5. **key_learnings**: 5-7 concise, actionable insights. Remove outdated learnings.

Remember:
- Don't over-rotate on small sample sizes (< 3 posts per pattern)
- Keep some exploration budget (don't completely abandon untested patterns)
- Be specific in learnings (bad: "engagement matters", good: "questions at the end
  drive 2x more replies than CTAs")"""
