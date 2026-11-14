# LinkedIn 30-day plan — rewritten for 2026 algorithm

## Day 01 · Tue 17.11 · proof-first agents

A click is not the finish line.

One of my most repeated problems with browser automations is not the click itself. It is the lack of a condition that means the task succeeded.

An opencode-chrome agent can observe the DOM, take a deliberate action, and inspect the result to see whether the intended transition happened. That sounds boring, but it is the entire difference between automation that can be trusted and automation that merely produces logs.

I am interested in Python systems where the agent must explain what changed instead of closing a Jira task with ‘done’.

The practical test is not whether the pointer moved. It is whether the target state exists afterwards.

Which proof condition would make you trust an agent with an irreversible change?

#PythonBackend #AIEngineering #Automation

Visual: `images/01.png`
First comment: github.com/Mukller/opencode-chrome
Alt text: Anton Petnitsky post 01: proof-first agents

## Day 02 · Wed 18.11 · klipper false green

HTTP 200 lied to me.

Mainsail was loading. Nginx returned the right status. Klipper was in error state because RP2040 had been disabled earlier but its configuration blocks still remained active.

That taught me a useful rule: a page loading successfully proves nothing about the system doing the actual work.

It also taught me where to search first. Not always the UI. Not always the reverse proxy. Sometimes the first stop is the exact service in the failure path: Klipper, the MCU, Moonraker, a restart script, or the state file.

The dashboard is an interface. It is not the process.

When did your ‘healthy’ dashboard last hide the actual failure?

#Klipper #PythonBackend #Reliability

Visual: `images/02.png`
First comment: none
Alt text: Anton Petnitsky post 02: klipper false green

## Day 03 · Thu 19.11 · botka reject before scale

More generation did not make Botka better.

The meaningful improvement was the gate around it:

- source quality check
- duplicate rejection
- rule and explanation validation
- human review before publication
- deletion of anything we cannot explain cleanly

A learner does not get a better answer because I created more output. They get it because I removed the weak answer first.

The unglamorous work is why a technical content system should not be evaluated by how much it can generate. It should be evaluated by what it refuses to publish.

Which kind of content do you reject before it reaches a user?

#Education #PythonBackend #ContentOps

Visual: `images/03.png`
First comment: none
Alt text: Anton Petnitsky post 03: botka reject before scale

## Day 04 · Fri 20.11 · automation is not a click

A bot that cannot verify is an expensive clicker.

I have seen agents celebrate task completion after driving a browser to the exact place where nothing happened. The click was real. The result was imaginary.

That is why I keep coming back to three stages in every automation:

- observe the current state
- choose one specific action
- verify the transition happened

Python can automate the action. A reliable system has to automate the follow-up question: did it work?

Without that question, the agent only moves the pointer and writes a confident log line.

What would help you decide an automation finished correctly?

#AIEngineering #Reliability #PythonBackend

Visual: `images/04.png`
First comment: none
Alt text: Anton Petnitsky post 04: automation is not a click

## Day 05 · Sat 21.11 · Python ownership hiring

I’m not interested in another Python headline that could describe any graduate with Flask tutorials.

The work I want:

- backend services behind real operational flow
- Python LLM pipelines that include retries and failure states
- automation inside messy workflows
- debugging where business logic, data quality and humans collide

Frameworks are the easy part. What matters is understanding why the broken path exists and being able to own it once it reaches production.

Python is not a finish line. It is a practical language for solving a broken system.

If that is your team, send me a note about the role.

#Python #PythonBackend #LLMOps

Visual: `images/05.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 05: Python ownership hiring

## Day 06 · Sun 22.11 · repo memory and agents

Context should survive the chat window.

A serious coding agent needs more than a vague reminder that work happened last week. It needs to inspect current reality:

- the tracked files
- the untracked diagnostic scripts
- the documented decisions
- the verification that failed yesterday
- the evidence that matters next

That is what repository memory is supposed to capture: not a diary, but the state that prevents the agent from redoing discoveries.

This is why I treat .github and design notes as real dependencies. They are part of the product input, not just recruiter decorations.

Where does your agent lose context most often?

#AIEngineering #Engineering #LLM

Visual: `images/06.png`
First comment: none
Alt text: Anton Petnitsky post 06: repo memory and agents

## Day 07 · Mon 23.11 · verify browser automation

Screenshots are not evidence.

They show a frozen view. They do not prove the action changed the application.

opencode-chrome exists because I wanted a browser tool that could inspect what an agent had actually done. 62 MCP tools were useful, but only if the agent could see the live DOM, target a specific node, and check the resulting state.

Control without verification is motion. Verification without control is measurement. The combination is automation.

The browser is still the worst place to pretend a task is simple.

Which browser action in your workflow would you trust an agent with first?

#AIEngineering #BrowserAutomation #MCP

Visual: `images/07.png`
First comment: github.com/Mukller/opencode-chrome
Alt text: Anton Petnitsky post 07: verify browser automation

## Day 08 · Tue 24.11 · voice-notes are not transcription

Whisper is a boundary, not a destination.

A voice-notes pipeline that ends at raw text is only storing the problem. The real work begins afterward:

- separating speakers
- removing likely hallucinations
- tagging tasks and decisions
- linking artifacts in Obsidian
- making the future search work without asking people to remember details

I made the pipeline for myself first because generic transcription could not answer the question I actually had: can I trust what it heard?

A bad note isn’t a failed file. It is an interrupted promise to you.

Which part of audio handling breaks first for you?

#VoiceNotes #AIEngineering #PythonBackend

Visual: `images/08.png`
First comment: none
Alt text: Anton Petnitsky post 08: voice-notes are not transcription

## Day 09 · Wed 25.11 · safalife operations

My Safalife automation could not fix the existing process by pretending it was a spec.

Operations showed up in every edge case:

- incomplete addresses
- partial phone numbers
- ad hoc dispatch changes
- Russian and Uzbek usage
- real workers making decisions under time pressure

A shipping product does not erase operational reality. It exposes where the human system was always flexible.

The most valuable engineering move was not another architecture layer. It was designing for missing and unreliable input.

Where does your ‘complete’ spec miss reality?

#Operations #Product #PythonBackend

Visual: `images/09.png`
First comment: none
Alt text: Anton Petnitsky post 09: safalife operations

## Day 10 · Thu 26.11 · voice-note quality gate

No model was the only bottleneck in voice notes.

A transcription model can produce polished paragraphs and still preserve nothing useful. It can get the words right while losing the context, the speaker, or the reason the note existed.

That is why the useful part of the pipeline was cleanup:

- hallucination filters
- segment deduplication
- speaker separation
- structured output
- a person checking whether it feels right

I stopped treating ‘AI wrote the note’ as an endpoint. It is an intermediate step with quality risk attached.

What do you improve before using an LLM output anywhere?

#AIEngineering #GarbageIn #PythonBackend

Visual: `images/10.png`
First comment: none
Alt text: Anton Petnitsky post 10: voice-note quality gate

## Day 11 · Fri 27.11 · green CI is not correct input

Green CI did not protect the system from garbage input.

I can get a batch of tests passing and still feed the application:

- malformed records
- incomplete order data
- stale configuration
- contradictory generated answers

Testing is evidence for the code you wrote. It is not a warranty for everything that enters the pipe.

Input validation matters because the happy test case taught the engineer almost nothing.

Which input does your pipeline handle worst?

#Testing #Python #Production

Visual: `images/11.png`
First comment: none
Alt text: Anton Petnitsky post 11: green CI is not correct input

## Day 12 · Sat 28.11 · service start order

Start order can decide a working system’s fate.

A network of six services can look broken for one boring reason: one service started before its dependency.

The failure pattern repeats everywhere:

- Velocity starts without the backend
- a backend starts before postgres
- a consumer accepts stale data because its dependency wasn’t warmed up
- a restart makes it look intermittent

Once I saw the pattern, I stopped saying ‘random’ and started asking what had to exist first.

Operationally, timing is part of the contract.

Which dependency still starts on hope?

#Backend #EmbeddedSystems #Reliability

Visual: `images/12.png`
First comment: none
Alt text: Anton Petnitsky post 12: service start order

## Day 13 · Sun 29.11 · delete weak content

Deleting weak content was the highest-leverage content work I did.

Not formatting it.
Not adding more examples.
Not ‘make it sound professional’.

The useful decision was rejection:

- duplicate questions
- ambiguous explanations
- misleading answers
- source data nobody can verify

Facturability beats volume. A learner is better served by one sound answer than by ten forgettable, confident screens.

Curation is not taste. It is guardrails.

What content reaches production before you review it?

#Education #ContentOps #PythonBackend

Visual: `images/13.png`
First comment: none
Alt text: Anton Petnitsky post 13: delete weak content

## Day 14 · Mon 30.11 · six services are one system

One Minecraft server can become six services easily.

Velocity handles traffic. Lobby, Survival, Limbo, Anarchy and Minigames split the behavior. Translation, authorization, ordering, restarts — they are all observable differently.

But the user does not experience six services. They experience one world that loads, fails to load, or never matches the doorway they expected.

Reliability here is not a single restart. It is knowing which service failed first and why the next one cannot recover.

Which system have you merged into one boundary too early?

#Backend #Reliability #Systems

Visual: `images/14.png`
First comment: none
Alt text: Anton Petnitsky post 14: six services are one system

## Day 15 · Tue 01.12 · ugly 80 percent hiring

I’m not looking for Python work that ends with nice screenshots.

The work I want:

- imported exports nobody wants to touch
- Python automation between two systems that never agreed on format
- the LLM endpoint that fails when the input is half-filled
- the support process entering users into a broken schema

Most of the value lies in the 80% that looks unimportant.

If your broken process requires someone to trace it without glamor, I would take that responsibility.

Which workflow is currently being held together manually?

#Python #PythonBackend #Hiring

Visual: `images/15.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 15: ugly 80 percent hiring

## Day 16 · Wed 02.12 · transcript fidelity

A transcript can sound polished and preserve nothing useful.

The words are not the lesson. A fluent answer can still lose:

- the decision that was made
- the assumption underneath it
- the weird exception the speaker remembered
- the speaker’s confidence in the result

When I write notes this way, the next reviewer is guessing, not working.

A polished sentence is not necessarily a faithful note.

What would you inspect before keeping a transcript?

#KnowledgeManagement #AIEngineering #PythonBackend

Visual: `images/16.png`
First comment: none
Alt text: Anton Petnitsky post 16: transcript fidelity

## Day 17 · Thu 03.12 · logs over screenshots

Screenshots don’t tell me why failure happened.

They show the final surface. They don’t show:

- the first error that occurred
- the timestamp where the application diverged
- the command that reproduced it
- the state that existed two minutes earlier

Logs are less pretty but closer to the system’s real conversation.

A screenshot can lie by being taken too late. A log cannot simply look successful if the problem is hidden there.

What would your first inquiry inspect?

#Debugging #Reliability #Backend

Visual: `images/17.png`
First comment: none
Alt text: Anton Petnitsky post 17: logs over screenshots

## Day 18 · Fri 04.12 · diff is risk report

A diff is a risk report.

I read it for:

- which invariant changed
- which side effect moved first
- who sees the regression
- why this dependency was touched now

AI-generated code raises the value of review because it increases the amount of plausible-looking change.

A clean commit message helps only if the diff can be read without pressure.

How do you read a diff in your team?

#CodeReview #Engineering #Git

Visual: `images/18.png`
First comment: none
Alt text: Anton Petnitsky post 18: diff is risk report

## Day 19 · Sat 05.12 · repo as proof hiring

A repository isn’t decoration.

It proves:

- how you run the project
- how you document tradeoffs
- how tests surface error conditions
- how you revert a wrong route

When nobody trusts your CV bullet, GitHub is the piece that shows what happens before or during production.

It doesn’t need to be huge. It needs clear documentation and working failure cases.

Which repository are you most proud of right now?

#GitHub #PythonBackend #Hiring

Visual: `images/19.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 19: repo as proof hiring

## Day 20 · Sun 06.12 · restart isn't repair

A restart is not a repair.

It clears one visible symptom and leaves the cause waiting:

- bad migration
- missing environment variable
- stale state file
- old parser handling new schema

Every restart buys time. None of it changed the code path.

If your reliability metric ignores the cause and only tracks process uptime, you don’t know whether the issue is fixed.

What did your last restart actually resolve?

#Operations #Backend #Reliability

Visual: `images/20.png`
First comment: none
Alt text: Anton Petnitsky post 20: restart isn't repair

## Day 21 · Mon 07.12 · failure as interface

Failure is part of the interface.

If your contract never says what happens with:

- invalid input
- timeout
- partial success
- unknown state

then the function doesn’t have a complete API. It has a wish.

I care about the error path because that is where real users meet the software.

Failure can’t disappear just because the happy case passes.

How do you describe failure before shipping?

#SRE #Backend #Testing

Visual: `images/21.png`
First comment: none
Alt text: Anton Petnitsky post 21: failure as interface

## Day 22 · Tue 08.12 · prompting isn't integration

Prompting is not integration.

I have seen spectacular prompts disappear on contact with:

- malformed input
- repetitive requests
- invalid JSON
- schema drift
- rate limits
- duplicate execution

An LLM chosen for language output is not an engineer for reliability.

The system around the model needs retries, identifiers, review and a way home for failure.

What part of your LLM path is still only a demo?

#LLMOps #Production #AIEngineering

Visual: `images/22.png`
First comment: none
Alt text: Anton Petnitsky post 22: prompting isn't integration

## Day 23 · Wed 09.12 · diagnostic before automation

Automation cannot rush diagnosis.

As Klipper taught me, the right order is:

- locate the service state instead of clicking ‘restart’
- verify the component you suspect first
- change one variable
- see which assumption still holds afterward

Do that before touching a repair path. Otherwise your system becomes a series of confident guesses.

Diagnosis is the part people try to skip because it isn’t entertaining.

What do you inspect before touching production?

#Klipper #Diagnostics #Backend

Visual: `images/23.png`
First comment: none
Alt text: Anton Petnitsky post 23: diagnostic before automation

## Day 24 · Thu 10.12 · content is database contract

Botka taught me that good learning content is a database contract.

If the schema does not match the answer logic, the learner meets the defect first:

- broken variants
- mismatch explanation
- reviewer unable to decide

A schema is not boring bureaucracy. It is where knowledge becomes useful multiple times without being remembered between incidents.

I’m interested in making the structure impossible to casually violate.

Where does content drift away from the schema in your process?

#Botka #DataModeling #PythonBackend

Visual: `images/24.png`
First comment: none
Alt text: Anton Petnitsky post 24: content is database contract

## Day 25 · Fri 11.12 · control is not correctness

opencode-chrome made me confront control versus correctness.

A modern agent can click a button. That is not the same problem as:

- did the intended field update
- did the request complete
- did the backend save it
- can someone prove it later

I learned that the browser is not the task. It is a boundary of observable state.

Safe automation ends with proof.

What can your agent verify after an irreversible action?

#AIEngineering #BrowserAutomation #PythonBackend

Visual: `images/25.png`
First comment: github.com/Mukller/opencode-chrome
Alt text: Anton Petnitsky post 25: control is not correctness

## Day 26 · Sat 12.12 · ask for Python reliability hiring

I’m not looking for ‘AI automation’ with no owner.

I want:

- LLM pipelines with recovery logic
- automation connected to real operations
- backend services with measurable error paths

Titles vary. What matters is being accountable for what happens after the happy path is broken.

If your team needs that kind of Python work, send me a note about the role.

#Python #Hiring #LLMOps

Visual: `images/26.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 26: ask for Python reliability hiring

## Day 27 · Sun 13.12 · one success is luck

One successful run can be luck.

A regular job is only regular when:

- retries don’t multiply side effects
- timeouts fail without corrupting state
- logs identify the incident
- the sequence can be replayed after release

This is where automation stops being clever and becomes operational.

What does your code do on attempt five, not attempt one?

#Automation #Backend #Reliability

Visual: `images/27.png`
First comment: none
Alt text: Anton Petnitsky post 27: one success is luck

## Day 28 · Mon 14.12 · ops is source code

Operations is the source code in an automated business.

Safalife made that painfully clear:

- users wrote missing values
- real exceptions arrived faster than specs
- dispatch decisions happened under pressure
- phone calls carried context the database never saw

A product built for this reality has to preserve the messy signal.

Automating operations means designing around what actually occurs.

Where does your spec miss operational truth?

#Operations #Product #PythonBackend

Visual: `images/28.png`
First comment: none
Alt text: Anton Petnitsky post 28: ops is source code

## Day 29 · Tue 15.12 · ownership over breadth hiring

One end-to-end process teaches you more than ten disconnected features.

Own the loop:

- trace the input source
- reproduce the incident
- identify the contract violation
- fix one boundary
- monitor the correction in reality

That makes review obvious to anyone who reads the commit.

Visible ownership beats scattered skill claims.

Which process can you own today, not next sprint?

#Python #Ownership #PythonBackend

Visual: `images/29.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 29: ownership over breadth hiring

## Day 30 · Wed 16.12 · 12 weeks to deliver

Hire for failure handling, not framework enthusiasm.

A credible first arc looks like:

1. map the environment
2. fix one recurring failure
3. own one operational boundary
4. make the outcome observable

That beats replacing an API simply because a newer framework exists.

Python, backend systems and LLM pipelines are useful only when failure modes are understood.

If you need a Python/backend engineer who owns the uncomfortable parts, send me a note.

#Python #Hiring #Backend

Visual: `images/30.png`
First comment: antonpetnitsky.com
Alt text: Anton Petnitsky post 30: 12 weeks to deliver
