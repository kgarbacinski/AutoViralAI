"""Prompts for post ranking and scoring."""

RANK_POSTS_SYSTEM = """\
You are an expert at predicting social media virality on Threads.
You evaluate posts on their potential to drive engagement, shares, and follower growth.

Score each post on a 0-10 scale where:
- 0-3: Low potential (generic, boring, no hook)
- 4-5: Average (decent but forgettable)
- 6-7: Good (strong hook, likely engagement)
- 8-9: Very good (share-worthy, drives conversation)
- 10: Exceptional (true viral potential)

Be critical and honest. Most posts are 4-6. A 10 is rare."""

RANK_POSTS_USER = """\
Score each of these Threads post variants on their viral potential.

## Posts to Evaluate

{variants}

## Scoring Criteria

For each post, evaluate:
1. **Hook strength** - Does the first line grab attention immediately?
2. **Emotional trigger** - Does it provoke curiosity, surprise, disagreement, or recognition?
3. **Shareability** - Would someone repost this to their followers?
4. **Conversation potential** - Does it invite replies and discussion?
5. **Authenticity** - Does it feel genuine, not AI-generated or generic?

## Target Audience

{audience_description}

## Instructions

For each post variant, provide:
- An ai_score (0-10, be critical)
- A brief reasoning explaining the score

Return scores for ALL variants."""
