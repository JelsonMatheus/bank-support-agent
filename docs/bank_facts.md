# Bank facts — Orbis Bank (fictional)

Orbis Bank is a fictional digital bank used in this project. Every number and
rule in the knowledge base must come from this file. This file is a writing
reference and is not indexed by the agent.

## Company

- App-only bank. Accounts are in euros, for customers in the European Union.
- Every customer has one physical debit card.

## Support

- In-app chat: every day, 08:00–22:00 (Lisbon time).
- Email: support@orbisbank.example. Replies within 1 working day.
- A lost, stolen or compromised card should be frozen in the app straight away,
  then reported through the in-app chat, where it is handled as urgent.

## Card delivery

- The card is ordered automatically when the account is opened and is
  dispatched once identity verification is complete.
- Delivery takes 5–7 working days after dispatch, by standard post. There is no
  tracking number.
- The app shows the card status: Ordered, then Dispatched with the dispatch date.
- If the card hasn't arrived 10 working days after dispatch, the customer
  should contact support. The first replacement is free.

## Card activation

- The card must be activated in the app before its first use: Cards → Activate
  card, then enter the last 4 digits of the card number.
- Contactless payments work after the first payment made with chip and PIN.

## PIN

- The PIN can be viewed in the app: Cards → Show PIN (requires the passcode).
- The PIN is blocked after 3 incorrect attempts.
- To unblock it: Cards → Unblock PIN. It takes effect immediately and the PIN
  stays the same.

## Freezing a card

- A card can be frozen and unfrozen in the app at any time: Cards → Freeze
  card. It takes effect immediately.
- A frozen card declines all payments.

## Replacing a card

- A damaged or expired card can be replaced in the app: Cards → Replace card.
- A replacement for a damaged card costs €5. Replacements for expiring cards
  are sent automatically and are free.
- Replacement cards follow the same delivery times as new cards.

## Spending limits and card settings

- Daily card spending limit: €2,500 by default, adjustable in the app between
  €0 and €5,000 (Cards → Limits).
- Online payments can be switched on or off in Cards → Security.

## Declined card payments

- Common reasons: insufficient balance, card frozen, card not activated, PIN
  blocked, daily limit reached, online payments switched off, or the merchant
  declined the payment.
- When a merchant declines a payment, Orbis Bank can't see the merchant's
  reason.
- Declined payments are not charged. If a declined payment appears as pending,
  the amount is released within 7 days.

## Pending card payments

- A card payment shows as Pending until the merchant confirms it, usually
  within 1–3 working days.
- Hotels, car rentals and fuel stations can take up to 7 days and may place a
  temporary hold larger than the final amount.
- The final amount can differ from the pending amount.
- A pending amount the merchant doesn't confirm within 7 days is released
  automatically.
- Orbis Bank can't speed up or cancel a pending payment.

## Card payment fees

- Card payments in euros are free.
- Card payments in other currencies have a fee of 1% of the payment amount.
- Some merchants add their own surcharge. It is set by the merchant, not by
  Orbis Bank.
- Any fee is shown in the transaction details in the app.

## Top-ups

- Two ways to add money: a bank transfer to the customer's Orbis IBAN, or a
  debit card top-up in the app.
- Bank transfer top-ups are free. SEPA Instant transfers arrive in seconds;
  standard SEPA transfers arrive within 1 working day.
- Debit card top-ups are free up to €3,000 per calendar month, with a 0.5% fee
  above that. The maximum is €10,000 per calendar month.
- Card top-ups usually arrive instantly but can take up to 30 minutes.
- Credit cards are not accepted for top-ups. The card must be in the
  customer's own name.
- A card top-up can fail because the card issuer declined it, the 3-D Secure
  check failed, the card isn't in the customer's name, it is a credit card, or
  the monthly maximum was reached.
- A failed card top-up is not charged. If the customer's other bank shows a
  pending charge, that bank releases it, usually within 5 working days.
- If a bank transfer top-up hasn't arrived after 2 working days, the customer
  should contact support with proof of the transfer.

## Outgoing transfers

- Only SEPA transfers in euros are supported. Transfers are free.
- SEPA Instant transfers arrive within seconds, 24/7, if the recipient's bank
  supports them, up to €100,000 per transfer.
- Standard SEPA transfers sent before 15:00 (Lisbon time) on a working day
  arrive on the next working day. Transfers sent after 15:00, on weekends or on
  public holidays are processed on the next working day.
- A transfer can fail because the IBAN is invalid, the recipient's bank
  rejected it (for example, a closed account), or the balance was insufficient.
- Money from a failed transfer is returned to the account within 2 working days.

## Passcode

- The app is opened with a 6-digit passcode.
- To reset it: tap "Forgot passcode" on the login screen, open the link sent
  by email, confirm with the code sent by SMS, then choose a new passcode.
- A customer without access to their email or phone must contact support,
  which will verify their identity.

## Personal details

- Email and phone number can be changed in Settings → Personal details. A
  confirmation code is sent to the new email or phone.
- Name and address changes are requested in the app with a supporting
  document: an ID document for a name change, or proof of address dated within
  the last 3 months. Requests are reviewed within 2 working days.
- Date of birth can't be changed in the app; the customer must contact support.

## Handled by people only

- Refunds, charge disputes and duplicate charges.
- Fraud, unrecognised payments, and compromised, lost or stolen cards (beyond
  freezing the card in the app).
- Closing an account.

## Deliberately not covered

The knowledge base must not cover these topics, so that the agent's ability to
recognise uncovered questions can be tested: exchange rates, ATMs and cash
withdrawals, supported countries, age limits, and virtual cards.