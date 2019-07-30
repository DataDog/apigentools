# Contributing

First of all, thanks for contributing!

This document provides some basic guidelines for contributing to this repository.
To propose improvements, feel free to submit a PR.

## Submitting issues

* If you have a feature request, you should [contact support][2] so the request
can be properly tracked.
* If you think you've found an issue, please search the [Open Issues][1]
  section of this repository to see if it's known.
* If you can't find anything useful, please contact our [support][2] and
  provide a detailed report of the issue.
* Finally, you can open a Github issue.

## Pull Requests

Have you fixed a bug or added a new feature and want to share it? Many thanks!

In order to ease/speed up our review, here are some items you can check/improve
when submitting your PR:

* Have a [proper commit history](#commits) (we advise you to rebase if needed).
* Write tests for the code you wrote.
* Make sure that all tests pass locally.
* Summarize your PR with a meaningful title, [see later on this doc](#pull-request-title).

Your pull request must pass all CI tests before we will merge it. If you're seeing
an error and don't think it's your fault, it may not be! [Join us on Slack][3]
or send  us an email, and together we'll get it sorted out.

### Keep it small, focused

Avoid changing too many things at once. For instance if you're fixing two different
spec files at once, it makes reviewing harder and the _time-to-release_ longer.

### Pull Request title

The title must be concise but explanatory to assist in the triaging of open Pull Requests.

### Commit Messages

Please don't be this person: `git commit -m "Fixed stuff"`. Take a moment to
write meaningful commit messages.

The commit message should describe the reason for the change and give extra details
that will allow someone later on to understand in 5 seconds the thing you've been
working on for a day.

### Squash your commits

Please rebase your changes on `master` and squash your commits whenever possible,
it keeps history cleaner and it's easier to revert things. It also makes developers
happier!

[1]: https://github.com/DataDog/apigentools/issues
[2]: https://docs.datadoghq.com/help
[3]: https://datadoghq.slack.com
