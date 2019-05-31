# Roles

TODO: It is foreseen that new roles will be defined in relation to the notification features.

## Administrator

Can create new users and assign permissions.

## Secretariat Edit

Ozone Secretariat staff can:

* enter data on behalf of a Party that submits its information by means other than the online reporting tool (e.g. via e-mail)
* attach document(s) received from a Party to the corresponding version of the submission
* create new versions based on existing versions to make further changes to the submitted data under instructions from a Party
* change flags on existing versions
* maintain all tables under the Secretariat’s control - permissions granted "per-table" [^TODO1]
* review and process submissions
* change a submission's state as detailed in the [workflow specifications](workflow.md)
* send notifications and reminders to Parties

[^TODO1]: More details needed, it's possible to define more specialized roles, easier to assign and manage. That will be known once the data model is finished.

## Secretariat Read-Only

These Ozone Secretariat users can **view** all data reported by any party, but can't make any changes.

## Party Reporter

Party Reporters can:
* report data for ANY reporting cycle for which they have not previously submitted data (up to the current reporting period).
* add associated documents to a submission - these will be saved as files, tied to the specific version to which they were added.
* revise previous submissions - this will always create a new version of the revised submission (Note: revisions of data for baseline periods require a special approval).
* change a submission's state as detailed in the [workflow specifications](workflow.md)

Notes:

* Each reporter is assigned to a single Party
* There can be one or more reporters for one Party.
* Differentiating among party administrators, focal points, primary contacts, secondary contacts, etc. is not necessary [^TODO2]

[^TODO2]: That can be added as a secondary (low priority) requirement (different permissions within the Party role: read-only / read-write / submit data / create additional users)

## Party Read-Only

These users belong to one party and can **view** all data reported by their party. It's similar to the _Secretariat Read-Only_ role, but restricted to a single Party.

## Public users

Note: Public users won't have direct access to any part of the reporting system. Some of the data is published in the main website, but from a different database.
