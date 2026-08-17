# cfoforit-openmarketplace

## The firm's operating rules live in one place, not here

Every standing rule for how CFOforIT works with Claude — response style, the report contract,
how to write a task Steve can execute, what to do when a check goes red, which surface can
reach what — lives in **`CFOforIT/cfoforit-claude-plugins/CLAUDE.md`**. Read it there.

This file exists so a session working in this repo knows that. It deliberately does not copy
those rules: eight copies of one rule is the drift problem, not the fix.

## A correction about how we work gets written down, once

When Steve corrects a mistake about *how to work* — not feedback on a shipped asset, which
routes to the `feedback-loop` skill — the correction goes into
`cfoforit-claude-plugins/CLAUDE.md` under the section it belongs to, in the same session it
happened. Not into this file. One home, so the next session in any repo inherits it.

## What this repo is

The public plugin marketplace. Everything here is world-readable: no client name, no internal
path, no figure, no person's contact details. Content is mirrored from private repos by a sync
script, so confirm which side is authoritative before editing.
