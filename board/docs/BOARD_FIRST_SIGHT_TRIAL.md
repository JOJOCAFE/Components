# Board First-Sight Trial

Status: ready for the human acceptance step. This is a five-minute usability
check for the local NOT-gate Board; it is not an electronics exam and collects
no participant names or personal details.

## Participants

Run separately with:

- one learner aged about 13–15; and
- one adult beginner with no electronics background.

Do not teach Component vocabulary or demonstrate the Board first. Ask the
participant to think aloud, but do not help unless they are stuck; record the
exact point where help became necessary.

## Setup

1. Start the local Board with the command in `board/README.md`.
2. Open the supplied NOT-gate example in a fresh browser profile or after
   clearing the Board's local draft/profile keys.
3. Keep this checklist with the observer, not on the learner's screen.

## Five-minute route

| Check | Prompt | Pass evidence |
| --- | --- | --- |
| Understand | “What do you think this small machine does?” | Explains that the NOT gate changes 0 to 1 and 1 to 0 in their own words. |
| Locate | “Show me its input and output.” | Points to `IN`/input and `OUT`/output. |
| Try | “What can you safely try now?” | Chooses **Try inversion** and describes the displayed result. |
| Change | “Make one connection change, but check it before you apply it.” | Sees the exact readable source preview and can Apply or Cancel deliberately. |
| Recover | Ask for an invalid connection, such as connecting an output where a second driver would conflict. | Reads the on-screen explanation, names one next action, and source stays unchanged. |
| Cancel | Start a pin connection, then press Escape. | Temporary guide/form disappears and the Board says nothing changed. |
| Keyboard | Tab to two pin anchors; use Enter or Space to start and finish a proposal. | Gets the same checked preview/apply route without a pointer. |

## Record only this result

```text
Participant: learner 13-15 | adult beginner
Completed all checks without a guide: yes | no
If no, first blocked check and exact wording/interaction:
One confusing label or step:
Suggested small change:
Observer/date:
```

The Board passes this human gate only when both participants complete the
route without a guide. If either needs help, revise the screen or wording and
repeat the same trial before adding Working Box, BOM, bus routing, or advanced
visual features.
