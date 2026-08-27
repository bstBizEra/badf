# Erratum — commit a074e91 (BADF-WP-0015) message

**What is wrong.** Line 31 of the commit message reads:

> WPs now carry , and the foreign resolver refuses a dossier whose target differs from its WP's repo.

**What it should read.** "WPs now carry `repository`, and the foreign resolver refuses …"

**Cause.** The message was passed through a shell heredoc that was not single-quoted at that
point; the backticked word was executed as a command substitution (`repository: command not
found`, bash line 98) and replaced with its empty output. The commit succeeded, CI passed, and
the merged code is correct — only the record is damaged.

**Why an erratum and not a rewrite.** The commit is on `main` under branch protection and is an
ancestor of later work. Rewriting history to repair a sentence would destroy the very property
the ledger and lockfile exist to provide. A claim that outlives its correction is the defect
class this repository keeps finding in itself; the remedy is a correction that is itself
recorded, findable, and lockfile-covered — which this file is.

**Verified on `main`:** `git log -1 --format=%B a074e919 | sed -n 31p`.
