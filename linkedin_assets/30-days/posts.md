# LinkedIn 30-day plan — rewritten

## Day 01 · Tue 17.11 · hiring-signal

A click is not the finish line.

The part that decides whether an automation works is after the click:

1. What did the page say?
2. What changed?
3. How do we know it changed for the right reason?

I built opencode-chrome around observe → act → verify, because “the button was pressed” is not the same as “the task is done”.

What would make you trust a browser agent in production?

#AIAgents #Automation #Python

Visual: `images/01.png`
First comment: github.com/Mukller/opencode-chrome
Alt text: Anton Petnitsky post 01: hiring-signal

## Day 02 · Wed 18.11 · technical-lesson

HTTP 200 lied to me.

Mainsail opened. Nginx returned 200. Klipper was in error state because an RP2040 module had been disabled but still had active autoconfig blocks.

The system answering was not the system doing the work.

Before you touch a dashboard, ask the control plane what happened.

Which component do you trust first when the page loads?

#Klipper #EmbeddedSystems #Engineering

Visual: `images/02.png`
First comment: none
Alt text: Anton Petnitsky post 02: technical-lesson

## Day 03 · Thu 19.11 · portfolio-deep-dive

More generation did not make Botka better.

The useful part was the pipeline around it:

- reject duplicates and weak questions
- enforce answer rules before publication
- keep review before the learner
- remove anything we cannot explain cleanly

The unglamorous job was deciding what not to ship.

What input do you reject most often?

#Python #ContentPipeline #Education

Visual: `images/03.png`
First comment: none
Alt text: Anton Petnitsky post 03: portfolio-deep-dive

## Day 04 · Fri 20.11 · builder-product

A bot that cannot verify is an expensive clicker.

Obvious until you watch an agent failing:

- it opens the page
- it taps something
- it exits with “done”
- the intended action never happened

Automation needs an outcome condition. Otherwise the log is just theatre.

What proves an action actually worked for you?

#AIAgents #Reliability #Automation

Visual: `images/04.png`
First comment: none
Alt text: Anton Petnitsky post 04: builder-product

## Day 05 · Sat 21.11 · hiring-signal

I’m not interested in another “Python dev wanted” headline.

I’m looking for teams that own the place where things usually break:

- LLM pipelines with IDs, retries and failure states
- backend APIs connected to real operations
- Python automation inside a system people still use badly
- investigative debugging, not framework enthusiasm

My lane: backend, automation, agents, embedded-adjacent diagnostics.

Would your team own the broken pipeline nobody wants?

#Python #LLM #Backend

Visual: `images/05.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 05: hiring-signal

## Day 06 · Sun 22.11 · builder-product

Context should survive the chat window.

If the agent starts from “what were we doing again?”, your repository is not ready for automation.

My preferred loop:

- inspect current state
- save real discoveries
- verify against code
- make next session start from evidence

Repo memory is not cosmetic book-keeping. It is the operating system for follow-up work.

Where do your agents usually lose context?

#AgentWorkflow #Python #OpenClaw

Visual: `images/06.png`
First comment: none
Alt text: Anton Petnitsky post 06: builder-product

## Day 07 · Mon 23.11 · technical-proof

“opencode-chrome” made me stop trusting screenshots as evidence.

Screenshots show a frozen view. Agents need proof one event changed the application.

The loop that works:

- read the live state
- act on a specific element
- check the resulting state
- log what changed

That is how browser automation becomes debuggable instead of hopeful.

Which tool would you trust with a production action?

#BrowserAutomation #AI #MCP

Visual: `images/07.png`
First comment: github.com/Mukller/opencode-chrome
Alt text: Anton Petnitsky post 07: technical-proof

## Day 08 · Tue 24.11 · technical-proof

Whisper is a boundary, not a destination.

My voice-notes pipeline only became useful after the text got:

- speaker separation
- timestamp cleanup
- hallucination removal
- topic extraction
- Obsidian-ready output

Transcribing more is easy. Making it retrievable later is the hard bit.

What stops your audio notes from becoming useful knowledge?

#LocalAI #VoiceNotes #Whisper

Visual: `images/08.png`
First comment: none
Alt text: Anton Petnitsky post 08: technical-proof

## Day 09 · Wed 25.11 · product-story

My courier app learned from the user before I asked the spec to describe everything.

Ops reality:

- abandoned fields
- partial addresses
- phone-first interaction
- Russian and Uzbek usage
- orders nobody wanted to automate

A polished UI cannot save a workflow that ignores the people running it.

Where does your process depend on tribal knowledge?

#Safalife #Product #Operations

Visual: `images/09.png`
First comment: none
Alt text: Anton Petnitsky post 09: product-story

## Day 10 · Thu 26.11 · technical-proof

No model was ever the only bottleneck in voice notes.

Whisper gave noisy text. Full context was still missing. Speaker separation changed the usefulness of everything downstream.

Before asking a model to think, first build the notes a human would want to read later.

Storage without review is just an audio archive.

What part of transcription fails for you?

#VoiceNotes #LLM #DataPipeline

Visual: `images/10.png`
First comment: none
Alt text: Anton Petnitsky post 10: technical-proof

## Day 11 · Fri 27.11 · technical-lesson

Green CI did not protect me from garbage input.

A suite can pass perfectly and still send:

- malformed records
- incomplete order data
- stale feature flags
- invalid LLM output

Tests prove code paths. Input quality is a separate problem.

CI is a filter, not a warranty.

Where does your clean pipeline meet dirty input?

#Testing #Python #CI

Visual: `images/11.png`
First comment: none
Alt text: Anton Petnitsky post 11: technical-lesson

## Day 12 · Sat 28.11 · technical-lesson

Start order can break a working system.

If one service starts before the thing it depends on, the failure looks random afterwards.

Minecraft network, Klipper, and ordinary APIs all hit the same rule:

- dependency stays down
- consumer retries around stale state
- logs point at the obvious victim

A restart can hide timing defects.

Which service usually starts before it should?

#Backend #EmbeddedSystems #Debugging

Visual: `images/12.png`
First comment: none
Alt text: Anton Petnitsky post 12: technical-lesson

## Day 13 · Sun 29.11 · builder-product

Deleting weak questions was the highest-leverage content work.

Not fixing grammar.
Not adding examples.
Not choosing a prettier template.

Defining what fails review — duplicates, ambiguity, unreadable prompts — protected every learner from the weakest output.

Curation is engineering, not taste.

What gets rejected most in your pipeline?

#EdTech #ContentOps #Python

Visual: `images/13.png`
First comment: none
Alt text: Anton Petnitsky post 13: builder-product

## Day 14 · Mon 30.11 · technical-proof

One Minecraft server can easily become six services.

Velocity. Lobby. Survival. Limbo. Anarchy. Minigames.

If one starts late, or the wrong port is unavailable, players blame the whole system.

Reliability is having one predictable path from login to the thing they wanted.

It was never just a restart.

How many services does your stack start from scratch?

#Minecraft #Systems #Reliability

Visual: `images/14.png`
First comment: none
Alt text: Anton Petnitsky post 14: technical-proof

## Day 15 · Tue 01.12 · hiring-signal

I’m not looking for the glamorous version of Python work.

I want:

- the API whose failures nobody wants to explain
- the import that fails only in production
- the bot that handles odd input 
- the workflow stuck between two tools

The useful work begins where the demo ends.

Can your process survive ugly inputs?

#Python #Backend #Automation

Visual: `images/15.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 15: hiring-signal

## Day 16 · Wed 02.12 · technical-lesson

A transcript can look polished and still be useless.

Well-formatted paragraphs can hide:

- the wrong speaker
- missing decisions
- invented details
- searches nobody can find later

Before trusting AI notes, inspect whether they preserve ownership and context.

Storage is cheap. Reusable understanding is rare.

What would you read before keeping one transcript?

#VoiceNotes #DataQuality #AI

Visual: `images/16.png`
First comment: none
Alt text: Anton Petnitsky post 16: technical-lesson

## Day 17 · Thu 03.12 · technical-proof

Screenshots don’t tell me why failure happened.

I need the sequence:

- first error in the log
- timestamp before the user noticed
- command that reproduced it
- invariant that changed

If your debugging is screenshots first, you’re recording outcomes, not finding root cause.

Where does your next incident usually start?

#Debugging #Logs #Reliability

Visual: `images/17.png`
First comment: none
Alt text: Anton Petnitsky post 17: technical-proof

## Day 18 · Fri 04.12 · builder-product

A diff is a risk report.

I don’t only ask what changed. I ask:

- which invariant broke
- who sees the side effect first
- why this dependency moved
- what tests can’t describe

AI-generated code makes this review useful, not optional.

How do you read diffs in your team?

#CodeReview #Engineering #Git

Visual: `images/18.png`
First comment: none
Alt text: Anton Petnitsky post 18: builder-product

## Day 19 · Sat 05.12 · hiring-signal

A repository isn’t decoration.

I expect it to show:

- how I run the project
- what state it reproduces
- where the sharp edges live
- how contributions fail

The repo is the work sample when nobody trusts your résumé bullet.

Which repository are you most proud of?

#GitHub #Python #OpenSource

Visual: `images/19.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 19: hiring-signal

## Day 20 · Sun 06.12 · technical-lesson

A restart is not repair.

It clears one visible symptom. It does not remove:

- the bad migration
- the missing env var
- the stale state
- the incorrect config file

Every restart buys time but does not change the underlying code path.

What did your last restart actually fix?

#Backend #Operations #Debugging

Visual: `images/20.png`
First comment: none
Alt text: Anton Petnitsky post 20: technical-lesson

## Day 21 · Mon 07.12 · builder-product

Failure is part of the interface.

If nobody defines:

- invalid input
- timeout behaviour
- partial success
- unknown state

then the agent cannot fail predictably, and nobody can recover safely.

Good automation describes what breaks, not just what works.

How do you specify failure in your systems?

#Automation #Reliability #SRE

Visual: `images/21.png`
First comment: none
Alt text: Anton Petnitsky post 21: builder-product

## Day 22 · Tue 08.12 · builder-product

Prompting is not integration.

A beautiful example with one prompt does not solve production concerns:

- rate limits
- invalid output
- retries
- schema changes
- recurring failures

The model owns language. The system must own behavior.

What part of your LLM workflow is still only a demo?

#LLM #Production #Engineering

Visual: `images/22.png`
First comment: none
Alt text: Anton Petnitsky post 22: builder-product

## Day 23 · Wed 09.12 · technical-proof

Automation cannot rush diagnosis.

Usually the fastest route is:

- get the error
- find the first thing that diverged
- change one variable
- see which condition stopped matching

Speed arrives after you stop solving the wrong symptom.

What do you investigate before touching the code?

#Klipper #Debugging #Python

Visual: `images/23.png`
First comment: none
Alt text: Anton Petnitsky post 23: technical-proof

## Day 24 · Thu 10.12 · technical-lesson

Good learning content is a database contract.

If the question and explanation don’t match the schema, the learner meets the bug before the engineer does.

A stable contract means:

- testable input
- explicit output
- reviewable explanation

Python cannot fix what the content model never clarifies.

Who owns content schema in your pipeline?

#Botka #DataModeling #Python

Visual: `images/24.png`
First comment: none
Alt text: Anton Petnitsky post 24: technical-lesson

## Day 25 · Fri 11.12 · technical-proof

opencode-chrome made me confront control versus correctness.

I can command an agent to click, but I still need to know:

- did the right page change
- did the intended field set
- did the operation persist

That last proof is the product, not the button action.

What can your automation prove after the click?

#AIAgents #Chrome #Automation

Visual: `images/25.png`
First comment: github.com/Mukller/opencode-chrome
Alt text: Anton Petnitsky post 25: technical-proof

## Day 26 · Sat 12.12 · hiring-signal

I’m not looking for “AI automation” with no useful owner.

I want Python work with one clear mandate:

- LLM pipelines with recovery
- backend services with measurable failure states
- operations automation tied to current users

The work combines backend judgment and proof of reliability.

Which one does your team actually need?

#Python #LLM #Hiring

Visual: `images/26.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 26: hiring-signal

## Day 27 · Sun 13.12 · builder-product

One successful run is luck.

An integration is durable only when:

- retries don’t create duplicate side effects
- timeouts fail safely
- logs identify context
- verification survives redeploys

 automation needs repetition, not performance on a lucky Tuesday.

What does your code do on attempt five?

#Automation #Backend #Reliability

Visual: `images/27.png`
First comment: none
Alt text: Anton Petnitsky post 27: builder-product

## Day 28 · Mon 14.12 · product-story

Operations is the source code in an automated business.

In Safalife, you cannot automate what the field already does manually:

- incomplete details
- manual route exceptions
- phone-only confirmations
- workflows users know better than the spec

Design the software around those flaws or don’t call it reliable.

Where does your spec miss real operations?

#Safalife #Product #Operations

Visual: `images/28.png`
First comment: none
Alt text: Anton Petnitsky post 28: product-story

## Day 29 · Tue 15.12 · technical-proof

One end-to-end process teaches you more than ten random features.

Own the loop — from weird input to recovery.

- understand who enters data
- find the break point
- rewrite one contract
- watch the fix in real use

That path is visible to every reviewer.

Which process can you own end-to-end?

#Python #Ownership #Engineering

Visual: `images/29.png`
First comment: none
Alt text: Anton Petnitsky post 29: technical-proof

## Day 30 · Wed 16.12 · hiring-signal

Hire for failure handling, not framework enthusiasm.

First 90 days should look like:

1. Map production paths
2. Fix one recurring failure
3. Own a subsystem
4. Leave it observable

That’s backend judgment, not CV decoration.

If you need Python ownership, I’m glad to talk.

#Python #Backend #Hiring

Visual: `images/30.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 30: hiring-signal
