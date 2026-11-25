# Compassion Modules · Odoo 18

These addons manage children, sponsorships, sponsor letters and partner communications
for any Compassion office, and connect Odoo with GMC. Swiss and Nordic country addons
depend on them. They also serve the Polish office, which the Swiss deployment hosts.

## Dependencies and translations

Declare the addons you use in the manifest's `depends`. Odoo refuses a dependency cycle
between addons: check the whole chain before adding a dependency on another repository's
addon. Addons here can depend on Odoo Community (the Swiss deployment has no
Enterprise), OCA addons and `compassion-accounting`, whose addons already depend on some
here, but never on `compassion-website` or a country repository. Put new
country-specific behavior in a country extension. Existing exceptions include
`mis_builder_spn_info` (for Nordic reports) and Swiss text in the default data of
`partner_segmentation` and `partner_communication_compassion`, which also has a
migration that runs only where `partner_communication_switzerland` is installed.
`partner_communication_crm_phone` needs `base_phone`, which only the Swiss deployment
has. `sponsorship_reporting` needs `account_fiscal_year`, which only the Swiss
deployment has.

If the module has catalogs, update its existing locales. For its first catalogs,
identify installing countries from country-addon dependencies or deployment
configuration. Ask the maintainer if coverage is unclear. Switzerland uses `fr_CH`,
`de_DE`, `it_IT`. The Nordic countries use `sv_SE`, `nb_NO`, `da_DK`, `fi_FI`. The
Polish office, which the Swiss deployment hosts, uses `pl_PL`: add it when the module
shows text to the Polish office's sponsors.

## Where to find the rules

When a task changes code here, open the shared rule subjects it needs. If the toolkit
plugins are available, use their skills `code-rules:rules` and `odoo-rules:rules`;
otherwise fetch the published rules into a temporary folder:
`(d="$(mktemp -d)" && git clone -q --depth 1 --branch main https://github.com/CompassionCH/compassion-agent-toolkit.git "$d" && echo "$d")`.
There, each index is `plugins/<plugin>/skills/rules/SKILL.md`. If the sandbox blocks the
network, ask the user to run the command, or read the indexes online:
[code-rules](https://github.com/CompassionCH/compassion-agent-toolkit/blob/main/plugins/code-rules/skills/rules/SKILL.md)
[odoo-rules](https://github.com/CompassionCH/compassion-agent-toolkit/blob/main/plugins/odoo-rules/skills/rules/SKILL.md)

## Before opening a PR

Run `pre-commit run` on staged files, or `pre-commit install` to enable the hooks on
commit. CI covers static checks only. It runs
`SKIP=oca-gen-addon-readme pre-commit run --all-files --show-diff-on-failure --color=always`
and checks for untracked generated files. Run the affected Odoo tests separately.

Then run the rules review in `review.md`, linked from the code-rules index. Use the
`code-rules:rules-reviewer` subagent when the plugin is available; otherwise give a
fresh read-only session the published reviewer prompt,
`plugins/code-rules/agents/rules-reviewer.md` in that folder
([online](https://github.com/CompassionCH/compassion-agent-toolkit/blob/main/plugins/code-rules/agents/rules-reviewer.md)).
Only if neither is possible, say in the PR description that no rules review ran. Record
findings, coverage gaps and their disposition there.
