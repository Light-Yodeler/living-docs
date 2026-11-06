# Feature Catalog: [Project Name]

Catalog of application features, their triggers, exact rules, implementing files, and configuration keys. Every feature has a permanent `FEAT-NN` ID that is never reused or renumbered.

---

## Module 1: [Module Name, e.g., Authentication & Rate Limiting]

### FEAT-01: [Feature Name]
* **Purpose:** [Problem solved for the user or operator, in one or two sentences.]
* **Trigger:** [When it runs: request to endpoint X, cron/interval every Y seconds, CLI command Z.]
* **Behavior & Rules:**
  1. [Concrete step or condition, including exact formulas, thresholds, status codes, and default values from code.]
  2. [...]
* **Touchpoints:**
  * [Layer, e.g., Backend]: `path/to/file.ts` (`functionName()`)
  * [Layer, e.g., Frontend / CLI]: `path/to/file.ts`
* **Configuration:** `SETTING_KEY` (default: `[value]`), [where it is configured].
* **Known Limitations:** [Omit this line if none. State gaps honestly, e.g., rate limiter state is in-memory and resets on process restart.]

---

## Module 2: [Module Name]

### FEAT-02: [Feature Name]
* **Purpose:**
* **Trigger:**
* **Behavior & Rules:**
* **Touchpoints:**
* **Configuration:**
