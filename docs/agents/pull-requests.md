# Pull requests

Every PR follows these steps. CI's guard checks the title and scans for secrets.

1. **Ticket first.** There is a Linear issue for the work before the first commit. Branch
   from its Linear branch name.
2. **Push early.** Push the branch as soon as you commit, and open the PR as a **draft**.
3. **Title:** `type: summary (DAS-n)`, for example `feat: add menu (DAS-66)`.
4. **Body, before it leaves draft:**
   - Every acceptance criterion from the ticket, word for word, each with its proof: a
     test name, a `file:line`, or a CI run on the latest commit. Anything only a person
     can check says **Needs Dan's device** and what Dan should do.
   - Any existing test this PR weakens or deletes, and why.
   - The three doc questions, each answered: architecture.md updated? ADR added?
     GLOSSARY.md updated?
5. **Self-review.** Reread the whole diff against the ticket as a cold reviewer, and fix
   what you find. Run `check`.
6. **Ready.** Mark the PR ready, move the issue to **In Review**, and comment the PR link
   on the issue.
7. **Review rounds.** After each round of fixes, move the issue to In Progress and back to
   In Review.
8. **Merge** is Dan's. Squash-merge; the issue moves to Done.
