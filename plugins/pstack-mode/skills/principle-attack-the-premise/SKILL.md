---
name: principle-attack-the-premise
description: "Apply when two or more fixes that share one premise have failed the same gate, a sweep of settings stops short of the target, or you explain the remaining failures as a limit of the tool. Write the premise down and test it directly before you write another fix that assumes it."
disable-model-invocation: true
---

# Attack the Premise

When two or more fixes that share one premise have failed the same gate, suspect the premise, not the fixes. A sweep of settings that stops short of the target counts, because each setting is a fix that failed. So does a remaining failure that you explain as a limit of the tool, because the limit usually holds only on the path the fixes share.

- Write the premise down: the one sentence every failed fix assumed.
- Test it before the next fix. Find an observation that would come out differently if the premise were false, and make it. Look at how the failures are distributed, not only at how large they are.
- If you judged results against another source of the same value, such as a second screen, file, or API that you used as ground truth, test that source as the answer first. You already trust it more than the path you are fixing.
- If the evidence contradicts the premise, look for what the failures share that it did not predict. If one part always lands on the losing side, change what puts it there instead of adding a mechanism that cleans up after it.

Do not start the next fix before the premise is written down and tested.
