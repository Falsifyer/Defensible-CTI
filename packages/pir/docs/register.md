# Register format

One JSON file, versioned next to the product that uses it. The validator never touches the network.

```json
{
  "version": "1.0",
  "requirements": [
    {
      "id": "PIR-001",
      "question": "Which actors target the energy sector supply chain?",
      "decision": "Which suppliers enter the quarterly watch plan.",
      "consumer": "Intelligence team",
      "priority": "high",
      "deadline": "2026-12-31",
      "status": "open",
      "eei": [
        {
          "id": "EEI-001",
          "question": "Are there documented campaigns against suppliers in the sector?",
          "indicators": [
            {"value": "campaigns published in the quarter", "source": "B2"}
          ]
        }
      ]
    }
  ]
}
```

| Field | Required | What is checked |
|---|---|---|
| `id` | yes | unique within the register |
| `question` | yes | not empty; ends in `?` (medium) |
| `decision` | yes | not empty: **the rule that defines the product** |
| `consumer` | yes | not empty: who decides |
| `priority` | yes | `high`, `medium` or `low` |
| `deadline` | no | ISO `YYYY-MM-DD`; in the past with `status != answered` warns |
| `status` | no | `answered` waives the deadline warning |
| `eei[]` | yes | at least one, each with a `question` |
| `eei[].indicators[]` | yes | each with `value` and `source` on the Admiralty scale |

The Admiralty grade is written `A-F` + `1-6` (source reliability and information credibility). `B2` is
a usually reliable source with probably true information; `Z9` is not accepted, and neither is leaving
it empty, because then there is no way to know when the indicator is answered.
