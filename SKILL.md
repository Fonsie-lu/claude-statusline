---
name: biha-sn-refactor
description: Refactor a ServiceNow script (Script Include, Business Rule, Script Action, Scheduled Job, Fix Script, client script, UI Action) to be shorter, simpler, and more readable, aligned with the BitHawk coding standard (biha-sn-coding) - single-file scope, ES12 syntax always (warning when ES12 mode is unconfirmed), config objects only to collapse if/switch chains, large objects built by a helper at the end, info logs buffered and muted by default, table/field names inline, aggressive comment pruning (terse caveman-style wording, JSDoc only on public functions, no file headers), and a final ESLint --fix pass against the project config. Takes precedence over biha-sn-coding; a customer-specific refactor skill takes precedence over this one. Use when the user asks to refactor, clean up, modernize, optimize, or tidy a ServiceNow script.
---

# ServiceNow Script Refactoring

Refactor ServiceNow server-side and client-side scripts to a consistent, readable house style. Preserve behavior exactly — this is a refactor, not a rewrite. The only exceptions are anti-pattern fixes the user confirmed (see "Anti-patterns to fix on sight") and the logging changes in "Logging and error handling".

## Precedence

This skill runs on code written with `biha-sn-coding`. Load `biha-sn-coding` and the references that match the script type before you refactor: its platform facts (traps, APIs, scope rules) still apply. When rules conflict, the first source in this list wins:

1. A customer-specific refactor skill, where one exists.
2. This skill (`biha-sn-refactor`).
3. `biha-sn-coding` (and a customer-specific coding skill that supersedes it).

Example: `biha-sn-coding` allows ES5 when ES12 mode is off. This skill always enforces ES12, so ES12 wins in a refactor.

**Guiding principle: readable, concise, simple.** Every change must make the script shorter or easier to follow. Abstraction is a cost — a constant, wrapper, or config object has to earn its place by removing branching or duplication. When a style rule below and this principle disagree, the principle wins: prefer the plainer code and say why you left the pattern alone.

**Minor style preferences rank below this goal.** Rules such as `addQuery()` over `addEncodedQuery()` or one naming form over another are tie-breakers. Apply one only when the result is no longer and needs no new helper, wrapper, parameter or data reshaping. If it would, leave the code as it is: do not apply it, do not ask the user about it, and name it in the report in one line at most. Correctness fixes (the "Ask first" anti-patterns that change what a script reads, writes or deletes) are not minor style.

## Scope

**Refactor exactly one file: the one currently selected/open in the VS Code editor.** That single file is the entire edit scope — never modify, create, or rename any other file, even when the refactor makes a change elsewhere look obviously desirable. Other files may be _read_ for context (callers, Script Includes being invoked, shared constants), but if something outside the target file needs to change, report it to the user instead of doing it.

### Resolving the target file — do this before anything else

The user's prompt usually does **not** name the file. The VS Code extension reports the editor state separately in the context, as `<ide_selection>` (highlighted code, with its file path in the header) or `<ide_opened_file>` (the file the user just opened). Resolve the target in this order:

1. A file path written in the prompt itself (`/sn-refactor path/to/file.js`) — always wins.
2. The **most recent** `<ide_selection>` block in the context.
3. The **most recent** `<ide_opened_file>` notice.
4. **Fallback — VS Code's persisted editor state.** The extension sends a notice only when the user opens a file or changes the selection, so a file already open before the session started produces none. In that case run:

    ```bash
    python3 <skill base directory>/open-editor-files.py
    ```

    Use the absolute "Base directory for this skill" path, so the call works from any working directory. The script finds the workspace itself: it walks up from the current directory (then from its own directory) to the nearest folder VS Code has open. It prints the open files, most recently active first. Exactly one line → that is the target. Several lines → take the first, but name the others in the announcement line so the user can redirect. The state is flushed periodically and can lag the live editor by a few seconds, which is why it ranks below the live notices.

Non-obvious rules that decide the right answer:

- **Only the newest editor notice counts.** `<ide_selection>` and `<ide_opened_file>` blocks from earlier turns are stale — the user has since moved to another file. Scan for the last one in the context, not the first one you happen to see.
- **Conversation history is not editor state.** A file discussed, written or refactored earlier in this session is _not_ the target unless the newest editor notice still points at it. This is the most common failure: re-refactoring the previous file while the user is looking at a new one.
- **A selection of lines still means the whole file.** The line range narrows nothing — see Workflow step 1.
- **Announce the target before the first edit:** open the reply with one line, `Refactoring <full path>`, so a mis-resolution is caught before anything is written.
- **Nothing from steps 1–4 → stop and ask** which file to refactor. Never guess, and never fall back to the last file touched in this session.

## Workflow

1. **Read the whole selected file first.** Never refactor from a fragment. If the user selected lines within the file, still read the full file to understand callers, `initialize`/`prototype` structure, and shared state — then refactor the whole file, not just the selected lines.
2. **Check ES12 evidence** — see "ES mode" below. The refactor always uses ES12. Before the first edit, state in the announcement line whether ES12 mode is confirmed: `Refactoring <path> (ES12)` or `Refactoring <path> (ES12, unconfirmed)`.
3. **Anti-pattern check.** List every anti-pattern in the file (see "Anti-patterns to fix on sight"). When at least one fix can change behavior, ask the user once, before the first edit, with one question that lists all of them. Recommend fixing them: that is the default answer. Fix only the ones the user confirms; leave the rest and name them in the report. Behavior-neutral fixes need no question.
4. **Refactor** applying every rule in "Rules" below.
5. **Comment pass.** Re-read every comment and JSDoc block left in the file and apply "Comments" and "JSDoc" below. Expect most inline comments and all private-function JSDoc to go. Then do a second pass: rewrite every survivor in the terse wording style ("Comments" below) with the fewest words that still carry the meaning. ESLint directives (`// eslint-disable-next-line ...`) and their reason comment stay.
6. **Lint** — the equivalent of VS Code's _ESLint: Fix all auto-fixable Problems_, using the project config (`eslint.config.mjs` at the workspace root: `standard` + Prettier + `jsdoc` + `servicenow` plugins). Run from the workspace root, not the skill directory:

    ```bash
    npx eslint --fix <file> && npx eslint <file>
    ```

    `--fix` applies Prettier formatting, `curly` braces, semicolons and quotes. Then fix every remaining warning or error by hand when the fix stays inside the target file and keeps behavior (JSDoc sentence case, `id-blacklist` names `e`/`err`/`error`/`cb`/`callback` — rename a caught `e` or `error` to `exception`, `servicenow/dont-use-gr-as-variablename`). Leave structural warnings (`complexity`, `max-statements`) alone unless the refactor already addresses them, and list them in the report. Finish with a clean second run, or report exactly what is left and why.
7. **Verify** nothing changed semantically:
    - Same public surface: do not change name, arguments or return type of top-level functions and public prototype methods.
    - Platform wrappers intact: the Business Rule `(function executeRule(current, previous) { ... })(current, previous);` wrapper, and the `(function () { ... })();` wrapper of program scripts (Script Action, Record Producer, Declarative Action). No top-level `return` outside them.
    - No `current.update()` introduced in a Business Rule.
    - `try`/`catch` blocks still sit at the same boundary: a refactor must not move a catch into a helper or drop one the entry point had.
    - Run the `biha-sn-coding` checklist (section 6, "Checklist Before Handing Code Over") on the result. Skip the ES12 item, which this skill overrides. Name every item that fails in the report, and say whether the refactor caused it or it was there before.
    - If a `<ClassName>_tests` ATF Script Include exists for the target, tell the user to run it. Otherwise suggest one for a non-trivial refactor.
    - Call out every behavior change: the confirmed anti-pattern fixes, the logging changes, and anything else you could not avoid.
8. **Sync note.** `eslint --fix` writes the file outside the editor, so sn-scriptsync does not see it. Tell the user to save the file in VS Code or push it with `update_record`. Remind them that the per-script ES12 toggle (`sys_es_latest_script`) does not travel in update sets.
9. **Report** briefly: what changed, anything suspicious you found but deliberately left alone (latent bugs, dead code, anti-patterns the user did not confirm, coding-standard violations outside the refactor's reach), and any change that would be needed in _another_ file — named but not made — so the user can decide.
10. **ES12 warning.** When ES12 mode is unconfirmed (see "ES mode"), end the output with the warning block defined there. It is always the last element of the reply.

## Rules

### ES mode

**Always refactor to ES12 syntax.** This is the first main rule. It applies to every script type, including Fix Scripts and global background scripts, and to files that are ES5 today. It overrides the ES5 fallback in `biha-sn-coding` (`references/es-compatibility.md`): never rewrite to ES5 during a refactor.

An ES12-only construct in a script without ES12 mode fails at runtime. So check for evidence, but never fall back to ES5 because evidence is missing. Evidence, in this order:

1. **The file already uses ES12-only syntax** (`const`/`let`, `??`, `?.`, destructuring, spread, `for...of`) and works → ES12 mode is confirmed.
2. **Instance check.** Query `sys_es_latest_script` for the record read-only (sn-scriptsync Agent API `query_records` if it runs, otherwise the project's instance access).
3. **Client-side scripts** run in the browser, not Rhino → ES12 is confirmed, except in code that must support legacy browsers.
4. **Record created on Xanadu or later.** Since Xanadu every new script has ES12 mode on by default. A record created after the instance ran Xanadu, and never moved by an XML update set, counts as confirmed. A record that arrived through an update set does not: the toggle imports as `false`.

**No evidence → enforce ES12 anyway**, and end the output with this warning as the last element:

```markdown
> **Warning: ES12 mode unconfirmed.** `<path>` now uses ES12 syntax (`const`/`let`, `??`, `?.`, ...), but no evidence shows ES12 mode is on for this record. Enable the ES12 toggle on the record (`sys_es_latest_script`) before you run it, or the script fails at runtime. The toggle does not travel in update sets.
```

Fix Scripts and global background scripts normally run without ES12 mode: for these, the warning is almost always required.

ES12 syntax rules:

- `const` by default, `let` where reassigned. Never `var`. Never `const` for a reassigned loop counter (Rhino throws).
- Use spread, destructuring, `Object.entries`/`values`, `??`, `?.` where they make the code shorter or clearer.
- **Iterate arrays with Array methods**: `forEach`, `map`, `filter`, `find`, `some`, `every`, `reduce`. Keep an existing Array method call; never rewrite it to a loop. Use `for...of` only for a concrete reason: the loop must `break`, `continue` or `return` from the enclosing function, or it iterates something that is not an array (a `Map`, a `Set`, a string). When you write a `for...of`, state the reason in the report. "ES12 allows it" is not a reason. Template literals, arrow functions and `Array.prototype.includes` also work without ES12 mode: they never count as ES12 evidence, and they do not trigger the warning on their own.
- **Exception:** the top-level class declaration stays `var MyClass = Class.create();` (and `var MyAjax = Class.create(); MyAjax.prototype = Object.extendsObject(...)`). `const`/`let` go inside method bodies.

### Syntax and structure

- Declare functions as **`function name() {}` declarations**, never `const name = () => {}`. Anonymous inline `function () {}` is acceptable only where a callback is genuinely unavoidable.
- **Keep the platform structure.** Nothing may leak into global scope:
    - **Script Include:** keep `Class.create()` + `prototype`. Helpers become `_private` prototype methods (or static `ClassName.method` functions for stateless utilities), never loose top-level functions. `type: 'ClassName'` stays last.
    - **Business Rule:** all code, including helper function declarations, lives inside the `executeRule` wrapper.
    - **Program scripts** (Script Action, Record Producer, Declarative Action, Scheduled Job, Fix Script): everything inside one `(function () { ... })();`.
    - **Client Script / UI Policy script:** keep the platform entry function (`onLoad`, `onChange`, `onSubmit`, `onCellEdit`); declare helpers inside it.
- **Order by execution inside that container:** constants/config objects → entry logic → helpers in the order they are called → builder functions last. Hoisting makes this valid and it reads top-down.
- Keep it **concise**. Guard clauses and early returns instead of nested `if`. Delete dead code and redundant temp variables.
- Every `if` body takes braces, even a one-line early return (`curly: all` in the project lint config): `if (!newValue) { return; }`, which Prettier expands to three lines.

### Comments

**Prune hard. The default for every comment is to delete it.** Names and structure carry the meaning. Comment only **non-obvious behavior** (the code does something a reader would not expect from the line itself, e.g. a platform quirk) or **non-obvious intention** (why code that looks unnecessary or wrong is there).

- **Test for every comment:** without it, would a competent ServiceNow developer misread the line or "fix" it into a bug? No → delete.
- **Keep**, for example: `// Outlook <hr> above quoted text.` on a regex that strips `<hr>` (why strip it at all), `// Reply <style> blocks reset P margins.` on an inline style (why not plain `<p>`), a workaround for a platform bug, a race condition.
- **Delete background and context**, even when true and useful elsewhere:
    - where a value comes from or which environment needs it (`// Second address: relay target on sub-production.`),
    - which ACL, rule or record a value mirrors or feeds (`// Same states as comments write ACL.`, `// Notification "BiHa - RITM closed".`),
    - what a well-named function guards against (`// Out-of-office mail loops` inside `isAutoReply()`),
    - anything the reader can look up on the instance (state codes, property meaning, event consumers).
    Background like this belongs in the record's description or the implementation docs, not the code.
- **One short line**, about 60 characters at most. Never two lines. A file of a few hundred lines typically keeps zero to three comments.
- **Terse wording, caveman style** — applies to inline comments and to JSDoc text alike:
    - Drop articles (a/an/the), filler (just, simply, basically, actually), hedging and pleasantries.
    - Fragments are fine. Short synonyms (fix, not "implement a solution for").
    - Technical terms, table, field, API and record names stay exact. No invented abbreviations (`cfg`, `impl`, `req`), no arrows (`→`).
    - Never drop `not`, `never`, `no` or `only`: they flip the meaning.
    - Before: `// Outlook puts a horizontal rule above the quoted original; it only adds noise.` After: `// Outlook <hr> above quoted text.`
- **Delete** comments that:
    - restate or narrate the code (`// query the user`, `// Strips the hr tag`),
    - repeat what a constant, function or variable name already says, even partly (`// awaiting caller` above `HOLD_REASON_AWAITING_CALLER`),
    - explain a value the reader can look up (a state code, a property's meaning),
    - mark sections (`// --- helpers ---`), hold commented-out code, or describe a data format.
- **No file header.** Record name, type, table and trigger live on the record itself. Delete header blocks such as `/** BiHa Update Incident — inbound email action ... */`.
- When a comment is needed to explain _what_ a block does, rename a variable or extract a named function instead.
- Kept comments: empty line before, space after `//`.
- ESLint directives (`// eslint-disable-next-line <rule>`) are not comments to prune. Keep each one together with the comment that says why it is there.

### Config objects to replace branching

A config object exists for **one** reason: to collapse an `if`/`else if` chain or a `switch` that maps a value to a value or behavior. That is the trigger. No other motive justifies one.

- Replace such a chain with a frozen lookup object, or a `Map` when keys are non-strings or insertion order matters. Declare it at the top of its container as an `UPPER_SNAKE_CASE` constant and look up with a fallback (`CONFIG[key] ?? CONFIG.DEFAULT`).
- Keep real conditional _logic_ as `if`. Only dispatch/mapping becomes a table. Two branches that already read clearly stay `if`/`else` — a two-entry lookup object is longer than the code it replaced.
- **Do not** introduce a config object to group unrelated values, to "centralize settings", or as a namespace. That is overhead, not structure.

```javascript
// Before — dispatch chain
function getRouting(category) {
    if (category === 'network') {
        return { group: 'Network Support', priority: '2' };
    } else if (category === 'hardware') {
        return { group: 'Field Services', priority: '3' };
    } else if (category === 'software') {
        return { group: 'Application Support', priority: '3' };
    }
    return { group: 'Service Desk', priority: '4' };
}

// After — lookup table (ES12)
const CATEGORY_ROUTING = Object.freeze({
    network: { group: 'Network Support', priority: '2' },
    hardware: { group: 'Field Services', priority: '3' },
    software: { group: 'Application Support', priority: '3' },
    DEFAULT: { group: 'Service Desk', priority: '4' }
});

function routeIncident(grIncident) {
    const routing = CATEGORY_ROUTING[grIncident.getValue('category')] ?? CATEGORY_ROUTING.DEFAULT;
    grIncident.setValue('assignment_group', routing.group);
    grIncident.setValue('priority', routing.priority);
}
```

### Large objects come from a function

An object literal with **more than 5 attributes** does not sit inline in the middle of logic. Assign it from a builder call, and put the builder **last** in its container: at the end of the wrapper function, or as the last `_build…` method before `type` in a Script Include prototype.

```javascript
var BiHaSupplierSync = Class.create();
BiHaSupplierSync.prototype = {
    initialize: function () {},

    /**
     * Sends incident to supplier.
     * @param {GlideRecord} grIncident - Incident to send.
     */
    syncIncident: function (grIncident) {
        const payload = this._buildIncidentPayload(grIncident);
        this._postToSupplier(payload);
    },

    // ... other working methods ...

    _buildIncidentPayload: function (grIncident) {
        return {
            number: grIncident.getValue('number'),
            sys_id: grIncident.getUniqueValue(),
            short_description: grIncident.getValue('short_description'),
            category: grIncident.getValue('category'),
            priority: grIncident.getValue('priority'),
            caller: grIncident.getDisplayValue('caller_id'),
            opened_at: grIncident.getValue('opened_at'),
            work_notes: grIncident.work_notes.getJournalEntry(1)
        };
    },

    type: 'BiHaSupplierSync'
};
```

This keeps the top of the file about what the script _does_ and pushes bulk data assembly out of the reader's way.

### Table and field names stay inline

- Write table and field names **directly** as string literals: `new GlideRecord('incident')`, `grIncident.getValue('assignment_group')`. Do not add a new `TABLE`/`FIELD` constants block — it adds a lookup hop and makes queries harder to read.
- **Keep existing class-level constants** (`BiHaServiceUtils.FIELD_NAME`) that are part of a Script Include's public surface or are used by several methods — other scripts may read them.
- Extract a literal into a named constant **only when it earns it**:
    - a **state/choice code** whose meaning is not obvious from context (`const STATE_RESOLVED = '6';`),
    - a **property name or endpoint** read in more than one place,
    - a value repeated **three or more times** where a typo would be silent.
- **sys_ids, URLs, user names:** The coding standard forbids hardcoding them. If a System Property for the value already exists, read it with `gs.getProperty()`. Otherwise extract the value into one named constant (`…_SYS_ID`) and report in the final summary that it must move to a System Property — creating the property is outside the single-file scope.
- **Allowed exception, from `biha-sn-coding`:** a justified hardcoded sys_id stays inline with `// eslint-disable-next-line servicenow/no-hardcoded-sysids` and a comment that says why. Keep an existing one as it is. Add a new one only when the project lint setup accepts suppression directives (check `eslint.config.mjs` and the hooks first: some projects reject them) and the reason is real, for example an OOB record whose sys_id is the same on every instance.
- A field name used once, or twice in adjacent lines, stays a literal.
- Same test for numbers: extract a magic number when the name explains something the digits don't (`const RETRY_LIMIT = 3;`), not on principle.

### Naming

camelCase, `UPPER_SNAKE_CASE` constants, `is`/`has`/`can` booleans, `…SysId` suffix for sys_id variables, plural arrays, `_underscorePrefix` for private Script Include methods, no cryptic abbreviations. Rename only local variables and private members — public names are part of the surface (Workflow step 7).

For Glide objects, the 2-letter prefix plus a PascalCase name works as follows. Never a bare `gr`/`ga`:

| Class | Prefix | Name from | Example |
|---|---|---|---|
| `GlideRecord`, `GlideRecordSecure` | `gr` | table | `const grIncident = new GlideRecord('incident');` |
| `GlideAggregate` | `ga` | table, or table + purpose | `const gaIncidentCount = new GlideAggregate('incident');` |
| `GlideAjax` | `ga` | Script Include (scope dropped) | `const gaBiHaBaseAjax = new GlideAjax('global.BiHaBaseAjax');` |
| `GlideDateTime`, `GlideDate` | `gd` | purpose | `const gdOpenedAt = new GlideDateTime(...);` |
| other `GlideXXX` | `g` + next word's initial | purpose | `GlideElement` → `ge…`, `GlideFilter` → `gf…` |

- Table name → PascalCase: `sys_user_group` → `grSysUserGroup`, `cmdb_ci_server` → `grCmdbCiServer`. Drop the custom prefix only: `u_` and `x_<vendor>_<app>_` (`x_biha_siam_ticket` → `grSiamTicket`).
- Two instances of one table in the same scope → add a role qualifier: `grIncidentParent`, `grIncidentChild`.
- `gs` is the global `GlideSystem` — never use it as a prefix (`GlideSysAttachment` → `saIncident`).
- Function parameters that receive a Glide object follow the same rule: `function routeIncident(grIncident)`. Business Rule and UI Action entry points keep the platform names `current` / `previous`.

### Avoid callbacks

- Prefer straight-line, synchronous code. Replace callback-passing helpers with functions that return a value the caller uses. There is no event loop server-side, so never introduce `Promise`/`async` code.
- Server-side: use `while (grIncident.next())` loops rather than callback-per-record helpers.
- Client-side: `getReference(field)` without a callback is synchronous and blocks — prefer `GlideAjax` with a Script Include, and if the platform forces asynchrony (`getXMLAnswer`, `g_form.getReference`), keep the callback as thin as possible and delegate to a named `function` declaration immediately.
- Array `forEach`/`map`/`filter`/`reduce` callbacks are fine and preferred over loops (see "ES mode") — the rule targets control-flow callbacks, not functional array methods.

### GlideRecord access

- Read and write fields with **`getValue()` / `setValue()`**, never dot access (`grIncident.state`, `grIncident.state = '6'`). Display values with `getDisplayValue()`.
- **String normalization:** `getValue()` already gives the value to compare or store; never add `+ ''` or `.toString()` to it. For a value already in hand that must become a JS string (a GlideElement from a dot-walk, a Java object from an API), use `value + ''`. Prefer it over `value.toString()`. Never `String(value)`. Guard `null` first: `null + ''` gives the string `'null'`.
- **sys_id:** `getUniqueValue()`, never `.sys_id`, `.sys_id.toString()` or `getValue('sys_id')`.
- **Journal fields** (`comments`, `work_notes`, any journal/journal_input field) keep dot access: `grIncident.work_notes = …`, `grIncident.comments.getJournalEntry(1)`. `setValue()` silently writes nothing on them.
- **Boolean fields** return `'0'`/`'1'`: compare `getValue('active') === '1'`. Never rewrite to `=== true` or `typeof` checks — values read from ServiceNow are `java.lang.String` and `typeof` returns `'object'`.
- `getValue()` returns `null` for empty fields. Use `??` only where `''` and `null` already mean the same thing in the existing code.
- **Existence check:** `setLimit(1)` + `hasNext()`. **Single-record read:** `get()` wrapped in `if`, or `setLimit(1)` + `if (grRecord.next())`.
- Prefer chained `addQuery()` over `addEncodedQuery()`, except for relative dates and complex OR/AND chains. Write field names inline as literals. This is a minor style preference (see "Guiding principle"): keep `addEncodedQuery()` when the switch would need a helper or a reshaped data structure, for example when encoded queries are stored as data that drives a loop. Rewriting an existing encoded query can change its result (`^OR`, `^NQ`, an invalid field that the platform drops): treat it as a behavior-changing anti-pattern fix and ask first (Workflow step 3).

### JSDoc

Pruning JSDoc means **fewer words, not fewer public blocks**.

- **Public surface keeps JSDoc:**
    - Script Include: every public prototype method and every static `ClassName.method` function.
    - Wrapper scripts (Business Rule, IIFE program script, inbound email action, client script): the top-level entry function(s) the wrapper calls directly. They say what the script does.
- **Private and inline functions get none.** Delete JSDoc on private `_methods`, on helpers that only other functions call, and on inline closures. The project lint config has `jsdoc/require-jsdoc` off, so this stays clean. A helper whose name cannot carry its meaning gets a better name; one fact that still needs saying becomes one inline comment.
- **Wording:** the terse style from "Comments" above. Summary is one line, about 80 characters at most, starts with a capital letter and ends with a period (`jsdoc/require-description-complete-sentence`): `Applies email reply to request item.`, not `Applies every enrichment step to the request item the reply refers to.` No second sentence, no prose paragraph.
- **Tags:**
    - `@param {Type} name - description` for each parameter. Description is a short fragment (`- Incident to send.`); drop it when name and type already say everything.
    - `@returns {Type} description`, description a short fragment or dropped. Omit `@returns {void}`.
    - `@throws {Type}` where it throws. No `@private`, `@example` or `@author`.

```javascript
/**
 * Sends incident to supplier.
 * @param {GlideRecord} grIncident - Incident to send.
 * @returns {boolean} True when supplier accepted.
 */
syncIncident: function (grIncident) {
```

### Logging and error handling

These rules follow `biha-sn-coding` (`references/logging-error-br.md`). Two additions: info logging is muted by default, and info lines are buffered in an array and printed once at the end.

#### Base rules (every script)

- **Scoped scripts:** `gs.debug` / `gs.info` / `gs.warn` / `gs.error`, written to `sys_log_appscope`. Verbosity is controlled by the `<scope>.logging.verbosity` property. Replace `gs.log` / `gs.print`, which do not work in a scoped app.
- **Global scripts:** keep `gs.log` / `gs.info`, or `GSLog` where property-driven levels are wanted. Do not convert working `gs.log(message, source)` calls just for style — the `source` argument changes how syslog rows are filtered.
- **Service Portal server scripts:** keep `$sp.log()`.
- **Build every log message as one string, chained with `+`**, the logger functions below included: `gs.info('Incident ' + number + ': ' + shortDescription)`, `logInfo(table + ': ' + count + ' records')`. No `{0}` placeholders, no template literals. Objects go through `JSON.stringify(obj, null, 2)`. Log identifiers and counts, never full records or credentials.
- **Info logging is muted by default.** Warnings and errors are always printed, immediately, never gated by a flag and never buffered.
- **Throw low, catch high.** Do not add `try`/`catch` to lower-layer helpers. Catch at the boundary only: Ajax method, BR entry, UI controller. There, log with `gs.error` and return a Result Object (`status` / `message` / `data`) or a user-friendly message. Keep existing catches. One that only swallows an error a caller needs is a behavior-changing anti-pattern: ask first (Workflow step 3).
- No logger in client-side scripts: keep `console.log` / `console.warn` / `console.error` with several arguments.

#### Choosing the logger (server-side only)

Take the first row that matches. Measure line counts on the file **as it was before the refactor**, blank lines and comments included.

| Condition | Logging |
|---|---|
| The script already uses a logging class (`BiHaLog`, `GSLog`, a project logger) | **Keep it.** Route every info line through it and add no second logger. `BiHaLog` already collects lines into one entry and is muted at info level by default (`biha.base.log.level`, commonly `warn`): leave the level alone. Add `log.setLevel('info')` only when the script's purpose is an info report. Make its write happen in a `finally` at the end of the entry logic, because collected lines are lost on an exception. |
| No logging class, no info-level log statements, file under 400 lines | No logger. Base rules only. Do not add new info-level logging. |
| No logging class, with info-level log statements (`gs.info`, `gs.debug`, `gs.log`, `gs.print`), or file 400 lines or more | **Buffered logger:** `LOG_ENABLED` flag + `logInfo` / `logWarn` / `logError` + `flushLog`, as in the example below. Existing info/debug calls become `logInfo`. The entry logic (top-level entry function, or the wrapper body) calls `flushLog` once at its end, in a `finally`. Only a file of 400 lines or more may add new `logInfo` lines, at key decision points. |

Logger rules:

- **One `LOG_ENABLED` flag for the whole script**, declared first in its container: `const LOG_ENABLED = false;` at the top of the IIFE or `executeRule` wrapper, or `LOG_ENABLED: false,` as the first prototype entry of a Script Include (read as `this.LOG_ENABLED`).
- **The default is always `false`.** When the script already wrote info/debug logs unconditionally, those now stay silent until the flag is switched on: list them in the report as a behavior change.
- `LOG_ENABLED` gates `logInfo` only. `logWarn` / `logError` print immediately with `gs.warn` / `gs.error`, flag or not.
- Each logger function takes exactly one parameter: the finished `message` string. No rest parameters, no placeholder replacement.
- `logInfo` pushes `LOG_PREFIX + ' ' + message` into `logLines`. `logWarn` / `logError` print `LOG_PREFIX + ' ' + message`.
- Buffered output: one `gs.info` (`gs.log` with a source in global scripts that already use it) with the lines joined by `\n`. Flush once per run, never per loop iteration. Reset the buffer after flushing.
- Placement: logger functions sit **last** in their container, after the builders. In a Script Include they are private methods (`_logInfo`, `_logWarn`, `_logError`, `_flushLog`) and the buffer is set in `initialize` (`this._logLines = [];`).

```javascript
(function () {
    const LOG_ENABLED = false;
    const LOG_PREFIX = '[BiHa-ImportSuppliers]';
    const logLines = [];

    importSuppliers();

    /**
     * Imports pending supplier rows.
     */
    function importSuppliers() {
        try {
            // ... logic calling logInfo / logWarn / logError ...
        } finally {
            flushLog();
        }
    }

    // ... helpers, builders ...

    function logInfo(message) {
        if (LOG_ENABLED) {
            logLines.push(LOG_PREFIX + ' ' + message);
        }
    }

    function logWarn(message) {
        gs.warn(LOG_PREFIX + ' ' + message);
    }

    function logError(message) {
        gs.error(LOG_PREFIX + ' ' + message);
    }

    function flushLog() {
        if (logLines.length === 0) {
            return;
        }

        gs.info(logLines.join('\n'));
        logLines.length = 0;
    }
})();
```

## Anti-patterns to fix on sight

Prefer fixing an anti-pattern over leaving it. Some fixes keep behavior and need no question. Others can change what the script reads, writes or deletes: list those for the user in Workflow step 3, recommend the fix, and apply only the confirmed ones. Unconfirmed ones go into the report.

**Fix without asking (behavior stays the same):**

- `getRowCount()` used just to test existence → `setLimit(1)` + `hasNext()`. `GlideRecord` loops that only count → `GlideAggregate`.
- Repeated `gs.getProperty('x')` calls → read once into a constant.
- Field read by dot access or implicit conversion (`grRecord.field`, `grRecord.field + ''`, `grRecord.field.toString()`) → `getValue('field')`, where only the value is used (not `.changes()`, `.getRefRecord()` or another GlideElement method). An empty field gives `null` from `getValue()` but `''` from `+ ''`: write `getValue('field') ?? ''` where the code compares with `''` or calls a string method. A value already in hand → `value + ''` (see "GlideRecord access"). `gs.info(array)` → `gs.info(array.join(','))`.
- Hardcoded sys_ids, URLs, user names → see "Table and field names stay inline".

**Ask first (behavior can change):**

- `gs.nil(grRecord)` used as a null test on a GlideRecord object — it never fires. Fix: `grRecord === null`. The guard then fires for the first time.
- Queries built by string concatenation → chained `addQuery` calls. An existing `addEncodedQuery()` → chained `addQuery` calls, only when the rewrite keeps the script as short (see "Guiding principle"); otherwise leave it and do not ask. Both can change the result set (`^OR`, `^NQ`, an invalid field the platform drops).
- `new GlideRecord()` inside a loop → hoist or restructure the query. A GlideRecord is a single-row cursor: a reused object can point at the wrong row.
- Unbounded queries that need only a few rows → `setLimit()`. Rows beyond the limit are no longer processed. A deliberate full sweep stays unbounded, with a one-line why.
- A `try`/`catch` that only swallows an error a caller needs.

**Never rewrite:**

- `gs.nil(value)` into `??` or optional chaining: `gs.nil()` also treats `''` as empty and `??` does not. `gs.nil()` stays for field values and GlideElements.

## Over-abstraction to avoid

These make a script longer without making it clearer. Do not add them, and remove them when you find them (unless they are public surface):

- A new `TABLE`/`FIELD` constants block wrapping names that were already readable.
- A config object holding unrelated values, or one with a single entry.
- A wrapper function called from exactly one place that adds no name-worthy meaning.
- A constant whose name just restates its value (`const INCIDENT = 'incident';`).
- A `Map` where a plain object literal would do.

If a refactor step would add lines without removing a branch, a duplication, or a genuine ambiguity, skip it.
