# Deprecation notice for `ME0094/huntplan`

The package lives here now, in `packages/huntplan`. The old repository stays public for a
while, so it needs to say so: leaving two copies of the same code with two CI badges is how
they drift.

## Apply it

```console
$ gh repo view ME0094/huntplan --json defaultBranchRef -q .defaultBranchRef.name
$ gh api repos/ME0094/huntplan/contents/README.md --jq .content | base64 -d > /tmp/old-readme.md
$ # prepend the banner below to /tmp/old-readme.md, then:
$ gh api repos/ME0094/huntplan/contents/README.md \
    --method PUT \
    -f message="docs: this repository is deprecated; the package lives in cti-suite" \
    -f content="$(base64 -w0 /tmp/old-readme.md)" \
    -f branch=main
```

Then freeze it: archive the repository (Settings → Archive) or add a `FROZEN` file, and stop
pushing to it from any script.

## Banner

```markdown
> **Deprecated — this repository is read-only and no longer maintained.**
>
> HuntPlan is now part of [cti-suite](https://github.com/ME0094/cti-suite), in
> `packages/huntplan`, where it is kept in step with the rest of the cycle: the hunt plan
> cites the assessment it answers, and the product cites the hunt plan. The code here is a
> snapshot and does not receive the ATT&CK v18+ detection-strategy map, the stricter
> falsifiability checks or the MCP facade.
>
> Use `pip install -e packages/huntplan` from cti-suite, or `ctisuite-mcp`.
```
