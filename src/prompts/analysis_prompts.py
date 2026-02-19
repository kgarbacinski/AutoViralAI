ANALYZE_PERFORMANCE_SYSTEM = """\
You are a data-driven social media strategist analyzing post performance.
Your goal is to identify what's working, what's not, and why.
Be specific and actionable in your insights."""

ANALYZE_PERFORMANCE_USER = """\
Analyze the performance of these recently published posts and their metrics.

## Posts and Metrics

{posts_with_metrics}

## Historical Pattern Performance

{pattern_performance}

## Current Strategy

{current_strategy}

## Instructions

Provide a structured analysis:

1. **Top Performers**: Which posts performed best and why?
2. **Underperformers**: Which posts fell flat and what went wrong?
3. **Pattern Insights**: Which content patterns are proving effective?
4. **Timing Insights**: Any correlation between posting time and performance?
5. **Content Pillar Analysis**: Which pillars drive the most engagement?
6. **Audience Signals**: What do replies/engagement tell us about what the audience wants?
7. **Actionable Recommendations**: 3-5 specific, concrete changes to improve performance.

Be honest about what's not working. Vague advice like "post better content" is useless.
Provide specific, testable hypotheses."""
