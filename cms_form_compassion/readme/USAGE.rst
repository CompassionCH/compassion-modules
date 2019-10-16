The payment adds several routes for redirecting to payment providers after a form submission.

One route is /compassion/payment/<invoice_id> that can contain
following GET parameters:

* accept_url: the redirection url after successful payment
* decline_url: the redirection url after declined payment

The redirection page is /compassion/payment/validate

If no accept_url and decline_url were passed, it will render the default confirmation page,
otherwise it will redirect the user accordingly.

The second route is /compassion/payment/<transaction_id> and is similar to the first one,
except that one can use a transaction id instead of an invoice. The transaction should however
be connected to an invoice otherwise it will display an error.
