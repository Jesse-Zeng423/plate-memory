---
title: "Plate Memory: remembering a preference is only half the job"
published: false
tags: devchallenge, weekendchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01).*

<!-- DRAFT: complete the explicitly marked facts and real handover reaction before publication. -->

## What I Built

I built Plate Memory for Harold, my friend and roommate from high school, and a
big foodie. The tool reviews a menu against remembered food preferences before
I plan a meal with someone.

**[TO FILL WITH JESSE: one actual meal-planning situation Harold encountered, and
the preferences he agreed could be described publicly. Do not assign the synthetic
example's allergy or diet to him.]**

The question I wanted the tool to answer is small: does the preference I remember
actually apply to this meal?

I can remember something correctly and still use it at the wrong time. A weekday
habit may not apply on Saturday. An old note may need another conversation. A
keyword match alone cannot settle either question.

Plate Memory is a Python CLI with a local open-weight model and a deterministic
guard. It returns the memory action—`USE`, `IGNORE`, or `ASK`—along with a verdict
and a reason. It never certifies a dish as safe.

## Demo

The public examples use synthetic preferences, not Harold's actual profile.
Here is the key example: the same chicken dish, the same weekday-vegetarian
memory, two different meal dates.

| Meal date | Memory action | Explanation |
| --- | --- | --- |
| Friday, October 2 | USE | The preference applies on weekdays |
| Saturday, October 3 | IGNORE | The meal is outside that preference's declared scope |

The model extracts the chicken phrase; the food adapter creates the candidate.
The same extraction can be used in both cases. Python supplies the
meal date and applies the rule. The difference in the decision comes from the
guard's context, not from asking the model to change its mind.

```sh
git clone https://github.com/Jesse-Zeng423/plate-memory.git
cd plate-memory
python3 -m src.cli --menu examples/weekend.txt --date 2026-10-03 \
  --offline --demo-extraction examples/weekend.extraction.json
```

This command uses a **canned extraction fixture**, clearly labeled in the output,
so someone can inspect the full flow without downloading a model. For actual AI:

```sh
OLLAMA_NO_CLOUD=1 ollama serve
# In another terminal:
ollama pull gemma3:4b
python3 -m src.cli --menu examples/weekend.txt --date 2026-10-03
```

![Actual local Gemma run with a synthetic profile](https://raw.githubusercontent.com/Jesse-Zeng423/plate-memory/main/docs/demo.png)

The image renders an actual CLI transcript. The final local smoke run used Gemma
3 4B on an 8 GB Apple Silicon Mac. All four synthetic scenarios produced the
expected guard actions; the trace is in
[local-smoke-v11.json](https://github.com/Jesse-Zeng423/plate-memory/blob/main/docs/local-smoke-v11.json).
That is a small integration check, not an accuracy benchmark.

## Code

{% github Jesse-Zeng423/plate-memory %}

I started this new project during the challenge window. The generic guard is
reused from my earlier [Memory Applicability Guard](https://github.com/Jesse-Zeng423/memory-applicability-guard)
under MIT, with its exact commit and fingerprint recorded in the new repository.
The food adapter, local model integration, CLI, examples and integration tests
are the work for this challenge.

## How I Built It

Gemma 3 4B runs through Ollama on the local machine. Its job is to turn a menu
line into grounded food phrases. The response is a small JSON array of phrases
copied from that line; unmentioned ingredients are not accepted.

An earlier version asked the small model to match multiple remembered concepts
at once. It produced incorrect matches and too many uncertain candidates. I
kept those traces and narrowed the extraction task instead of hiding the errors.
The final food adapter maps extracted phrases through a limited, explicit
vocabulary table: chicken can be a candidate for a poultry rule, and coriander
leaves for a cilantro rule. Custom terms can also match literally.

The CLI rejects phrases absent from the source, duplicates, extra fields and
duplicate JSON keys. It attaches the original line as evidence. The model sees
only menu text, not the friend's preferences, dates or policy metadata.

The food adapter derives those fields from the local profile and the meal date,
then calls a generic Python engine. The engine understands memory items, task
context, applicability evidence and risk. It has no hard-coded food concepts.
This weekend's shell is specifically about planning a meal for a friend.

The guard keeps an explicit precedence: revoked permission comes first; high
risk requires human review; unresolved external facts need verification; an
out-of-scope or superseded record is ignored; a supported current record can be
used; uncertainty may require asking. The exact neutral contract is documented
in the repository.

That produces a useful distinction. `PASS` means a proposed memory action agrees
with the guard. It does not mean dinner is safe. A synthetic allergy record
escalates even when the model finds no matching ingredient: missing a match is
not proof that an allergen is absent.

The tests cover those boundaries, including invalid metadata and a simulated
model response trying to inject a guard verdict. The canned examples also run
from an unrelated working directory. Locally, 69 unittest tests passed, and
pytest reported 69 tests plus 43 subtests passed. The package fingerprint check
and all four canned examples also passed. CI status is linked in the repository's
[validation record](https://github.com/Jesse-Zeng423/plate-memory/blob/main/docs/validation.md).
These checks establish the behavior
of the rules and integration. They do not measure real-world extraction accuracy.

### Handing it to Harold

**[REAL TRIAL PLACEHOLDER: after Harold actually uses it, describe what menu he
tried, what helped or confused him, and his real response. Leave this unfilled
until the handover. Do not invent a quote or imply a trial already happened.]**

## Why Does Open Innovation Matter?

The personal profile stays on the computer. The model receives only menu text;
it does not receive profile terms, record IDs, the friend's name, remembered text,
dates or policy metadata. The rule engine runs locally too. Permission is checked
locally before a remembered record can influence a recommendation.

Once Ollama and the weights are downloaded, using the tool does not require a
cloud API or an API key. There is no per-call hosted inference bill, although
running the model still uses the laptop's memory and electricity. Open weights
make local inference practical, and the model name is configurable so the
extraction component can be replaced without rewriting the guard.

The Python code and Ollama are MIT-licensed. Gemma is open-weight under Google's
Gemma Terms; I am not claiming its weights have the code's MIT license.

For a tool about a friend's preferences, being able to inspect the rules and keep
the data local is part of its usefulness. It also makes the failure boundary
visible: the model can misread a menu, and the guard cannot verify that a person's
manually entered metadata is true. Ingredients and cross-contact need confirmation
with the preparer. This remains decision support, not medical or food safety advice.

## Prize Categories

Best Use of Gemma: local Gemma 3 4B extracts the grounded food phrases that feed
the food adapter. The local smoke-test record documents actual inference on four
synthetic menus.
