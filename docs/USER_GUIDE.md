# User Guide

This guide walks through Magento CMS Sync screen by screen. Everything described here was
verified against the current code and against two real Magento 2.4.9 stores.

- [Before you start: a Magento API token](#before-you-start-a-magento-api-token)
- [Instances](#instances)
- [Compare Blocks and Compare Pages](#compare-blocks-and-compare-pages)
- [Diff viewer](#diff-viewer)
- [Sync wizard](#sync-wizard)
- [Sync page](#sync-page)
- [History](#history)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Typical workflows](#typical-workflows)
- [Limitations to know about](#limitations-to-know-about)

## Before you start: a Magento API token

Each instance needs the store's **base URL** (for example `https://shop.example.com`, without
`/rest`) and a **bearer token** with these permissions:

| Permission (ACL resource) | Admin label | Used for |
|---|---|---|
| `Magento_Backend::store` | Stores > Settings > All Stores | Connection test, store-view list |
| `Magento_Cms::block` | Content > Elements > Blocks | Read, create and update blocks |
| `Magento_Cms::page` | Content > Elements > Pages | Read pages |
| `Magento_Cms::save` | Content > Elements > Pages > Save Page | Create and update pages |

**Recommended: an Integration token.** In the Magento admin go to *System > Extensions >
Integrations*, add an integration, grant the resources above under *API*, save, then
*Activate* it and copy the **Access Token**. Integration tokens do not expire.

On Magento 2.4.4 and newer, integration tokens are rejected as bearer tokens until you enable
*Stores > Configuration > Services > OAuth > Consumer Settings > Allow OAuth Access Tokens to be
used as standalone Bearer tokens*.

**Alternative: an admin token.** `POST /rest/V1/integration/admin/token` with an admin
user's credentials returns a token immediately, but it expires (one hour by default on
recent versions, configurable in *Services > Magento Web API > JWT Authentication*), and it is
refused while two-factor authentication is enforced for that user. Use it for quick tests,
not for an instance you keep.

## Instances

*Instances* (Alt+1) lists the Magento stores the tool knows about.

**Add Instance** opens a form with the instance name (must be unique), the Magento URL, the
API token and an *Active* switch. The URL must be a valid absolute URL. **Edit** reopens the
same form; **Delete** asks for confirmation.

Each row shows:

- **Status**: the *Active* switch of the instance. It is informational; inactive instances
  can still be selected for comparisons.
- **Data**: two icons, *Blocks* and *Pages*. A badge on an icon is the number of items in
  the cached snapshot; hovering shows when it was last refreshed. **Clicking an icon fetches
  that content type from Magento again and replaces the snapshot.** Do this after content
  changes in Magento, because comparisons read the snapshots, not the live store.
- **Test Connection** (antenna icon) calls the store's `store/storeViews` endpoint with the
  token. "Connection test successful" means the URL and the token work; "Authentication
  failed" means the token was rejected; "HTTP error: 404" usually means the URL is not the
  Magento base URL.

Deleting an instance removes its cached snapshots and the history of syncs **from** it.
History entries where it was the destination remain and show "Unknown" as the destination.

## Compare Blocks and Compare Pages

*Compare Blocks* (Alt+2) and *Compare Pages* (Alt+3) work the same way.

1. Pick a **Source Instance** and a **Destination Instance**. The selection is shared between
   the two pages.
2. Click **Compare**. The comparison uses the cached snapshots of both instances. If an
   instance has no snapshot yet, it is fetched from Magento first; otherwise refresh it on the
   *Instances* page when you need current data.

The summary line reads "Total: X in source, Y in destination" followed by three counters:
items that are the **Same**, items that are **Different**, and items **Missing** in the
destination. Items that exist only in the destination are listed in the table (status
*Only in Destination*) but not counted in the chips.

| Row status | Meaning |
|---|---|
| Same | Present on both sides with identical compared fields |
| Different | Present on both sides, at least one compared field differs |
| Missing in Destination | Present in the source only; a sync will create it |
| Only in Destination | Present in the destination only; nothing to sync |

Which fields are compared is listed under [What counts as different](#what-counts-as-different).

- **Status Filter**: *All Items*, *Missing* (missing in destination), *Different*, *Same*.
  "Only in Destination" rows appear under *All Items*.
- **Search** matches the identifier and the titles on either side, case-insensitively.
- **View Details** (chevron) expands the row with the store views, active flag and, for
  pages, the page layout on each side, plus the names of the fields that differ.
- **View Diff** (eye) opens the [diff viewer](#diff-viewer); it is available for *Different*
  rows.
- **Checkboxes** appear on rows that can be synced: *Different* and *Missing in Destination*.
  The checkbox in the header selects every syncable item of the whole comparison, not just
  the filtered or visible rows. As soon as something is selected, a **Sync N items** button
  opens the [sync wizard](#sync-wizard).

The table is paginated client-side (25 rows by default).

### What counts as different

| Type | Compared fields |
|---|---|
| Blocks | `title`, `content`, `active`, `sort_order` |
| Pages | `title`, `content`, `content_heading`, `page_layout`, `meta_title`, `meta_keywords`, `meta_description`, `active`, `sort_order`, `layout_update_xml`, `custom_theme`, `custom_root_template`, `custom_layout_update_xml` |

Creation and update timestamps are ignored. Store-view assignment is compared only when the
Magento instance exposes it (stock Magento does not; see
[Limitations](#limitations-to-know-about)).

## Diff viewer

The diff viewer shows the fields that differ for one item, in three modes:

- **Table**: field, source value, destination value.
- **Split**: content fields side by side with a line diff. Red marks text present only in the
  source, green text present only in the destination. Other fields appear in a *Metadata
  Changes* table.
- **Unified**: a single word-level diff (removed words struck through in red, added words in
  green).

Empty values show as "(empty)" and booleans as Yes/No.

**Push to Destination** syncs this single item (create if it is missing, otherwise update)
after a confirmation that warns the destination content will be overwritten. The sync runs
in the background: the success message appears when the sync has been *started*. Check the
[History](#history) page for the result, then click *Compare* again.

## Sync wizard

Opened with **Sync N items** from a comparison page. Three steps:

1. **Select Items**: the selected items with the action that will be taken, *create* (green)
   or *update* (blue). Untick anything you do not want to sync. **Preview** is disabled when
   nothing is ticked.
2. **Preview Changes**: the number of items, creates and updates that will be sent. **Back**
   returns to the selection; **Execute Sync** starts the sync.
3. **Execute Sync**: progress while the sync runs, then "Sync completed successfully!" or
   "Sync failed: ..." with the per-item outcome ("Created page successfully", "Updated block
   successfully", or the error returned by Magento). **Done** closes the wizard.

What a sync does, per item:

- **create**: the source item is sent to the destination as a new block or page. Identifier,
  title, content and the other content fields are copied; the source's internal id and
  timestamps are not. On stock Magento the new item is assigned to all store views.
- **update**: the destination item with the same identifier is overwritten with the source's
  content fields, keeping the destination's own id.

The source data comes from the source's cached snapshot, so refresh the source instance
before syncing if it changed recently. The destination is read live during the sync and its
snapshot is refreshed automatically afterwards, so clicking *Compare* again shows the new
state without a manual refresh.

Closing the wizard (Cancel, Escape or clicking outside) does not stop a running sync; it
continues in the background and appears in the history.

## Sync page

*Sync* (Alt+4) is a dashboard that reloads every 5 seconds:

- **Active Syncs**: runs that are pending or in progress, with a progress bar and a details
  dialog (ids, instances, counts, timestamps, error message).
- **Today's statistics**: total syncs today, success rate, items synced, items failed.
- **Recent Syncs**: the five most recent completed or failed runs.
- **New Sync** takes you to *Compare Blocks*.

## History

*History* (Alt+5) lists the most recent 100 sync runs, newest first, with date, source and
destination, type, status, item counts and duration. Filters for status, type, source,
destination and date range are applied in the browser to those 100 records. **View Details**
shows the run's ids, timestamps, total items and error message.

**Export CSV** downloads the currently filtered rows as `sync-history-YYYY-MM-DD.csv` with the
columns Date, Source, Destination, Type, Status, Items Synced, Items Failed and Duration.
Values are not quoted, so instance names containing commas will shift columns.

The per-item messages of a run are available through the API
(`GET /api/history/{sync_id}`, see [API.md](API.md)).

## Keyboard shortcuts

Alt+1 to Alt+5 switch between Instances, Compare Blocks, Compare Pages, Sync and History
when the focus is not in a text field. Whether the browser and operating system pass the
combination through depends on the platform.

## Typical workflows

**Promote content from staging to production**

1. Register both stores. Test both connections.
2. Refresh *Pages* and *Blocks* on both instances.
3. *Compare Pages*, source = staging, destination = production. Review *Different* and
   *Missing* items; open the diff for anything surprising.
4. Select the items to promote, run the wizard, check the result step.
5. Repeat for *Compare Blocks*.

**Audit drift between two production stores**

Refresh both, compare, and use the *Different* filter and the diff viewer. Nothing is written
unless you start a sync.

## Limitations to know about

- **Identifiers must be unique per instance.** Magento permits the same identifier once per
  store view (multi-language setups often do this). Such pages collapse into one row, and an
  update may be refused by Magento with "A page URL key for specified store already exists".
- **Store views are not synchronised.** Stock Magento's REST API neither returns nor accepts
  store-view assignments for blocks and pages, so created items use the destination's default
  (all store views) and the *Store Views* rows in *View Details* show "All". Installs that
  extend the API with a `store_id` field are compared and mapped, but the mapping is not
  exposed in the UI.
- **No deletions.** Items that exist only in the destination are reported, never removed.
- **Snapshots, not live data.** Comparisons use cached content; refresh before deciding.
- **One backend process.** A sync runs inside the API process. If the backend is restarted
  while a sync runs, the history row stays "in progress"; run the sync again.
