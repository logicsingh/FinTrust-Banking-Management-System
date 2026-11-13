import pytest
from pydantic import ValidationError

from backend.app import Customer, Money, Transfer


def test_money_requires_positive_account_and_amount():
    assert Money(account_id=1, amount=10.5).amount == 10.5
    with pytest.raises(ValidationError):
        Money(account_id=0, amount=10)
    with pytest.raises(ValidationError):
        Money(account_id=1, amount=0)


def test_money_rejects_non_finite_amounts():
    with pytest.raises(ValidationError):
        Money(account_id=1, amount=float("nan"))
    with pytest.raises(ValidationError):
        Money(account_id=1, amount=float("inf"))


def test_money_limits_description_length():
    with pytest.raises(ValidationError):
        Money(account_id=1, amount=10, description="x" * 251)


def test_transfer_requires_distinct_positive_account_ids_at_api_boundary():
    transfer = Transfer(from_account_id=1, to_account_id=2, amount=10)
    assert transfer.from_account_id != transfer.to_account_id
    with pytest.raises(ValidationError):
        Transfer(from_account_id=-1, to_account_id=2, amount=10)


def test_customer_validates_email_and_name_length():
    customer = Customer(full_name="Test Customer", email="test@example.com")
    assert customer.full_name == "Test Customer"
    with pytest.raises(ValidationError):
        Customer(full_name="A", email="test@example.com")
    with pytest.raises(ValidationError):
        Customer(full_name="Test Customer", email="not-an-email")



def test_money_uses_two_decimal_places():
    assert str(Money(account_id=1, amount="10.25").amount) == "10.25"
    with pytest.raises(ValidationError):
        Money(account_id=1, amount="10.257")
    with pytest.raises(ValidationError):
        Money(account_id=1, amount="1000000000000.00")


def test_transfer_uses_decimal_amounts():
    transfer = Transfer(from_account_id=1, to_account_id=2, amount="125.75")
    assert str(transfer.amount) == "125.75"
    with pytest.raises(ValidationError):
        Transfer(from_account_id=1, to_account_id=2, amount="125.756")
