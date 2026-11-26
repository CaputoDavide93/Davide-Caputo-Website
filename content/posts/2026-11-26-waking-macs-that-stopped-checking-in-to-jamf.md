---
title: Waking Macs that stopped checking in
summary: A small tool that redeploys the Jamf framework on quiet Macs, why it previews first, why it never retries the redeploy, and where the logic lives now.
tags: jamf, macos, mdm, python
---

Some Macs go quiet: MDM commands queue and nothing happens. A Mac that sleeps through its check-ins, or whose Jamf framework has gone stale, stops acting on policies and commands. The Jamf Pro API has a call that redeploys the framework, but for forty Macs that means forty computer ID lookups and forty requests by hand, with no preview and no tally of which ones took. Jamf WakeUp Call is the small Python tool I wrote to do that for me.

## Three ways to pick targets

You give it a dynamic group, a single serial number or a file of serials with one per line. It looks the computers up, shows you the list, sends the commands and prints one result per computer, with the command UUID Jamf Pro returns.

## Dry run first

The tool has a dry run that lists what would happen and sends nothing. Every mode also asks yes or no before it sends, unless you pass --skip-confirmation. The README is firm that a first test should never be on production Macs, and suggests trying one serial first:

```
python3 -m src.main C02EXAMPLE001 --dry-run
python3 -m src.main --group-id 42 --dry-run
python3 -m src.main --group-id 42
```

The first line previews one computer, the second previews a group and sends nothing, and the third asks for confirmation and then sends.

## Reads retry, the redeploy does not

Reads retry up to 3 times with backoff on 429 and 5xx responses over HTTPS. The redeploy POST is never retried. The reason is simple: that way no command is sent twice. If a redeploy fails, the failure shows up as a line in the results rather than a silent second attempt.

## It only queues the command

The tool never talks to a Mac directly. It asks Jamf Pro to queue the redeploy, and Jamf Pro delivers it as an MDM command over APNs the next time the Mac is reachable. It cannot see whether a Mac received the command, so a Mac that stays offline, or cannot reach Apple's push service, still does not wake until it can. That is the one trade-off I would want anyone to know before they use it.

## Where the logic lives now

This repository is superseded. The same wake-up and redeploy logic now lives in Jamf-Snipe-IT-Suite as the wakeup module, with retries and SSM-backed credentials. The README says to use that for new work, and that the original repository is kept for reference and receives fixes only.
