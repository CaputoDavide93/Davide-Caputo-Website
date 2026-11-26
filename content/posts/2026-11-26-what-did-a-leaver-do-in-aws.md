---
title: What did a leaver do in AWS?
summary: Why I wrote a read-only tool that collects a leaver's CloudTrail activity across every account into one offline report, and where its limits are.
tags: aws, cloudtrail, offboarding, security, python
---

When an engineer leaves, someone has to answer one question: did they leave anything behind, and did they touch anything on the way out? In AWS that means searching CloudTrail in every account and region, reading request parameters for trust policies, public snapshots and new keys, and working out what still exists. By hand it is slow, and it is easy to miss an account. I wrote AWS Offboarding Audit to do that review in one run.

## What it collects and checks

The tool discovers every account your IAM Identity Center sign-in reaches and collects the person's CloudTrail events from each one. It flags the changes that can give lasting access or destroy something. The built-in checks cover:

- external trust
- wildcard policies
- public resources
- long-lived keys
- open security groups
- destructive lifecycle rules
- logging changes

It also separates activity during the notice period from activity after the last working day. An optional step checks whether a flagged change still exists.

## Read-only by design

Every AWS call the project makes reads state and none changes it. The README lists them all. They are the IAM Identity Center calls ListAccounts, ListAccountRoles and GetRoleCredentials, CloudTrail LookupEvents and GetTrailStatus, a handful of Describe, Get, List and Head calls for IAM, EC2, RDS, KMS, Lambda and S3, and the CloudTrail Lake StartQuery and GetQueryResults pair. The README says there is no Create, Put, Delete, Update, Terminate, Modify, Attach, Detach or Revoke call anywhere in the code, so running it cannot alter, disable or delete anything in your accounts.

Three things do reach beyond AWS: the TrailDiscover catalogue, which is downloaded at a pinned commit and checked by SHA-256 (and skipped with --no-enrich), an external AI service that is used only if you pass --analyze, and Google Fonts, which the browser fetches when it opens the report.

## The 90-day limit

By default the tool works from CloudTrail Event History, which holds 90 days of management events only. Longer ranges and data events need CloudTrail Lake. This matters when you plan an offboarding: the evidence you can see is the evidence that is still there.

## Ratings are not verdicts

The dashboard gives each item a review priority from 1 to 10. Those ratings are priorities for a human to look at. They are not findings of intent, and the plain-language assessments do not claim to infer why someone did something.

## One offline file

The output is one HTML report that opens locally, with Markdown and JSON alongside. It starts in plain English for HR or an IT lead, and a switch reveals the technical detail. You can see a fully synthetic example in the repository before you run anything.

A real run starts with a preflight, which lists the accounts and writes the plan without querying CloudTrail:

```
aws sso login --sso-session <your-session-name>
.venv/bin/python src/aws_offboarding_dashboard.py --config audit-config.yaml --preflight
```

When the account list is right, you drop --preflight and add --user, --notice-date, --last-day and --out. If a collection is interrupted, --resume carries on from the checkpoint.

The code is on GitHub as AWS-Offboarding-Audit.
