# Financial metric catalogue

All source amounts are signed `Decimal` values in major currency units, rounded
to two decimal places with `ROUND_HALF_EVEN`. A missing input is `None`; it is
not treated as zero. Monetary outputs use two decimal places and ratio outputs
use four decimal places, both with `ROUND_HALF_EVEN`.

| Metric | Formula | Unavailable when |
| --- | --- | --- |
| Net debt | `total debt − cash` | Total debt or cash is missing. |
| Debt / EBITDA | `total debt ÷ EBITDA` | Either input is missing, or EBITDA is zero or negative. |
| Net debt / EBITDA | `(total debt − cash) ÷ EBITDA` | A net-debt input is missing, or EBITDA is zero or negative. |
| Interest coverage | `EBITDA ÷ cash interest expense` | Either input is missing, or interest expense is zero or negative. |
| Current ratio | `current assets ÷ current liabilities` | Either input is missing, or current liabilities are zero or negative. |
| EBITDA margin | `EBITDA ÷ revenue` | Either input is missing, or revenue is zero or negative. |
| Simplified free cash flow | `EBITDA − cash interest expense − tax − capital expenditure` | Any input is missing. |

Negative EBITDA is permitted as a numerator: it reports a negative leverage,
coverage, or margin rather than silently suppressing financial distress. A
negative denominator is unavailable because the resulting ratio is not
meaningful for the intended credit interpretation.
