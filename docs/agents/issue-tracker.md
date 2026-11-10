# Issue tracker: Linear

Work for this repo lives in Linear, workspace **dassoft**, team **DASSoft** (key `DAS`),
under the **Agentic Workflows** initiative (project **dstack**). The team holds Dan's other products too, so always
scope to this initiative.

## Structure

- **Initiative** = the product.
- **Project** = a release that is worth having on its own. Its description links the spec.
- **Issue** = one PR. Every issue belongs to exactly one project and is assigned to Dan.
- **Statuses:** Backlog (not ready), Todo (ready), In Progress, In Review, Done, Canceled.
  Where a skill says to apply `ready-for-agent`, set status **Todo**.
- Order work with Linear's native **blocked by** relation. An issue is ready when all its
  blockers are Done.

## When a skill says "publish a spec"

Write it to `docs/specs/<linear-project-slug>.md`, commit it in that project's first PR,
and link it from the Linear project description. Specs are not Linear issues.

## When a skill says "publish tickets"

Create each ticket as a Linear issue in the release's project, status Todo, assigned to
Dan, with its acceptance criteria and the check chosen for each. Create blockers first and
link them with **blocked by**.

## When a skill says "fetch the ticket"

Get the issue by identifier (`DAS-123`) with its description, comments and relations.
State its title before starting.

## Working a ticket

- Branch from the issue's Linear branch name.
- **In Progress** when you start; **In Review** when the PR leaves draft; back to
  **In Progress** while you fix review changes, then **In Review** again (see
  pull-requests.md). Dan's merge moves it to **Done**.
- New ideas found mid-build become new issues in the right project.

## Closing a release

When the last issue in a project is Done:

1. Update `docs/architecture.md` from the code as it is now.
2. Add an ADR for any hard-to-reverse choice the release made without one.
3. Update `GLOSSARY.md` with new terms.
4. Mark the spec final.
5. Remove the release's scratch planning files.
6. Post a Linear project update: what shipped, what changed along the way, lessons.
