# Handover to Harold

This is a local CLI prototype built for Jesse’s friend and roommate from high
school, Harold, who is a big foodie. No actual dietary profile has been supplied.

## Before the trial

1. Install Ollama and download Gemma using the README. Confirm a real local run
   works with the synthetic menu; the canned demo is a different mode.
2. Ask Harold which meal-planning situation is useful to him: ordering together,
   choosing what to cook, or comparing menus. Record the actual answer.
3. Copy the template to ignored `private/friend.json`. Remove every synthetic
   record. Add only preferences Harold wants the tool to remember and use.
4. Set the remembered scope and last-confirmed date together. Agree a freshness
   interval; do not treat the example 180 days as a health standard.
5. Paste a real menu using `--stdin`, choose the intended meal date, and review
   candidates, decision reasons and questions together. Do not publish the menu,
   profile or terminal output if it contains private facts.

## Questions for the trial

- Which task did Harold actually try?
- Did the date-dependent explanation make sense?
- Was any match missing, wrong or too vague?
- Were the questions useful, or did the tool ask too often?
- What would make this useful next time?

## Facts to add before DEV publication

- A real meal-planning problem, in Jesse’s own words.
- Only preferences or examples Harold agrees may be shared.
- What actually happened during the trial, including errors.
- A real reaction, quoted only if accurate and approved for public sharing.

Leaving feedback unfilled is more accurate than claiming a handover happened.
The DEV draft is not published automatically.
