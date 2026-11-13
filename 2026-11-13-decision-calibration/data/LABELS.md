# Label rule

All 80 messages are synthetic. I wrote them for a made-up payments app called Pennyroll. The merchant names
(GADGETHUB, STRMFLX, SHOPLY, QUICKEATS and others) are invented too. There are no real customers, transactions or people.

**Question:** Is the customer asking for money back or contesting a charge (a refund request, a dispute, a
chargeback or a reversal), stated or clearly implied?

- **Yes (1):** the customer wants money returned to them or a charge reversed. This counts even when they never say
  "refund", for example "I've never had that service, what is this?" about a charge on their statement.
- **No (0):** anything else. That includes:
  - asking about a refund that is already approved or pending
  - withdrawing a dispute
  - stopping future payments only
  - general questions about how disputes work
  - sending money to someone else
- **Difficulty:**
  - `easy` items say it outright.
  - `hard` items are implied yes cases, or no cases that use refund and charge words.
- **Split:** 20 items in each of easy-yes, easy-no, hard-yes and hard-no.

One person wrote and labelled every item, and there was no second labeller. Some hard items are arguable: m048, m058
and m071 are the ones I would expect people to disagree on.
