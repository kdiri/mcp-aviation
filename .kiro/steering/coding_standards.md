# Coding Standards Guide

*Based on the Zen of Python principles, adapted for universal application*

## Core Principles

### 1. Clarity Over Cleverness
**Beautiful is better than ugly. Readability counts.**

Write code that is easy to read and understand. Prioritize clarity over showing off technical prowess.

```python
# Good
def calculate_total_price(items, tax_rate):
    """Calculate the total price including tax for a list of items."""
    subtotal = sum(item.price for item in items)
    tax_amount = subtotal * tax_rate
    return subtotal + tax_amount

# Avoid
def calc(i, t): return sum(x.p for x in i) * (1 + t)
```

**Test Example:**
```python
def test_calculate_total_price_clarity():
    """Test that the function name and behavior are self-documenting."""
    items = [Item(price=10.0), Item(price=20.0)]
    total = calculate_total_price(items, 0.08)
    assert total == 32.4  # 30 + 2.4 tax
```

### 2. Explicit Intent
**Explicit is better than implicit.**

Make your code's intentions clear. Avoid relying on implicit behavior or hidden assumptions.

```python
# Good
def send_notification(user, message, delivery_method="email"):
    if delivery_method == "email":
        send_email(user.email, message)
    elif delivery_method == "sms":
        send_sms(user.phone, message)

# Avoid
def send_notification(user, message, method=None):
    # Implicit default behavior - unclear what happens
    if method:
        # What if method is invalid?
        pass
```

**Test Example:**
```python
def test_explicit_delivery_method():
    """Test that delivery methods are explicitly specified."""
    user = User(email="test@example.com")
    
    # Should work with explicit method
    send_notification(user, "Hello", "email")
    
    # Should use explicit default
    send_notification(user, "Hello")  # Uses "email" by default
```

### 3. Simplicity First
**Simple is better than complex. Complex is better than complicated.**

Choose the simplest solution that works. When complexity is necessary, make it understandable rather than convoluted.

```python
# Good - Simple
def is_even(number):
    return number % 2 == 0

# Acceptable - Complex but clear
def validate_user_permissions(user, resource, action):
    if not user.is_active:
        return False
    
    required_permission = f"{resource}:{action}"
    return required_permission in user.permissions

# Avoid - Complicated
def check_perm(u, r, a):
    return u.active and f"{r}:{a}" in [p for p in u.perms if p.startswith(r)]
```

**Test Example:**
```python
def test_simple_even_check():
    """Test simple modulo operation for even numbers."""
    assert is_even(4) == True
    assert is_even(3) == False
    assert is_even(0) == True

def test_permission_validation_complexity():
    """Test that complex logic remains understandable."""
    user = User(is_active=True, permissions=["posts:read", "posts:write"])
    
    assert validate_user_permissions(user, "posts", "read") == True
    assert validate_user_permissions(user, "posts", "delete") == False
```

### 4. Flat Structure
**Flat is better than nested.**

Minimize deep nesting. Use early returns, guard clauses, and extraction methods to keep code readable.

```python
# Good
def process_order(order):
    if not order:
        return None
    
    if not order.is_valid():
        return handle_invalid_order(order)
    
    if order.requires_approval():
        return send_for_approval(order)
    
    return fulfill_order(order)

# Avoid
def process_order(order):
    if order:
        if order.is_valid():
            if not order.requires_approval():
                return fulfill_order(order)
            else:
                return send_for_approval(order)
        else:
            return handle_invalid_order(order)
    else:
        return None
```

**Test Example:**
```python
def test_flat_order_processing():
    """Test that order processing handles all cases without deep nesting."""
    # Test early return for None
    assert process_order(None) is None
    
    # Test invalid order path
    invalid_order = Order(valid=False)
    result = process_order(invalid_order)
    assert isinstance(result, InvalidOrderResult)
    
    # Test approval required path
    approval_order = Order(valid=True, needs_approval=True)
    result = process_order(approval_order)
    assert isinstance(result, ApprovalRequest)
```

### 5. Breathing Room
**Sparse is better than dense.**

Use whitespace and formatting to make code more readable. Don't cram too much logic into single lines.

```python
# Good
def calculate_shipping_cost(weight, distance, shipping_class):
    base_rate = get_base_rate(shipping_class)
    weight_multiplier = calculate_weight_multiplier(weight)
    distance_multiplier = calculate_distance_multiplier(distance)
    
    return base_rate * weight_multiplier * distance_multiplier

# Avoid
def calc_ship(w,d,c):return get_base(c)*calc_weight(w)*calc_dist(d)
```

**Test Example:**
```python
def test_shipping_calculation_readability():
    """Test that shipping calculation is easy to follow and debug."""
    cost = calculate_shipping_cost(
        weight=5.0,
        distance=100,
        shipping_class="standard"
    )
    
    # Easy to verify each component
    expected_base = get_base_rate("standard")
    expected_weight = calculate_weight_multiplier(5.0)
    expected_distance = calculate_distance_multiplier(100)
    expected_total = expected_base * expected_weight * expected_distance
    
    assert cost == expected_total
```

### 6. Error Handling
**Errors should never pass silently. Unless explicitly silenced.**

Handle errors explicitly and meaningfully. When you do suppress errors, make it clear why.

```python
# Good
def load_user_config(user_id):
    try:
        with open(f"configs/{user_id}.json") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file for user {user_id} not found, using defaults")
        return get_default_config()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config for user {user_id}: {e}")
        raise ConfigurationError(f"Corrupted config file for user {user_id}")

# Acceptable - Explicitly silenced
def cleanup_temp_files():
    for temp_file in get_temp_files():
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass  # File already removed - this is expected
```

**Test Example:**
```python
def test_error_handling_explicit():
    """Test that errors are handled explicitly and meaningfully."""
    # Test missing file handling
    config = load_user_config("nonexistent_user")
    assert config == get_default_config()
    
    # Test corrupted file handling
    with pytest.raises(ConfigurationError):
        load_user_config("corrupted_config_user")

def test_explicit_error_silencing():
    """Test that silenced errors are documented and intentional."""
    # Should not raise even if files don't exist
    cleanup_temp_files()  # Should complete without exceptions
```

### 7. Avoid Ambiguity
**In the face of ambiguity, refuse the temptation to guess.**

When requirements or data are unclear, fail fast or ask for clarification rather than making assumptions.

```python
# Good
def parse_date_string(date_str, format_hint=None):
    if not date_str:
        raise ValueError("Date string cannot be empty")
    
    if format_hint:
        try:
            return datetime.strptime(date_str, format_hint)
        except ValueError:
            raise ValueError(f"Date '{date_str}' does not match format '{format_hint}'")
    
    # Try common formats, but be explicit about what we're trying
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date '{date_str}' with known formats")

# Avoid
def parse_date(d):
    # Guessing what format the user meant
    return datetime.strptime(d, "%Y-%m-%d")  # What if it's MM/DD/YYYY?
```

**Test Example:**
```python
def test_date_parsing_no_guessing():
    """Test that date parsing doesn't make dangerous assumptions."""
    # Clear success cases
    assert parse_date_string("2023-12-25") == datetime(2023, 12, 25)
    assert parse_date_string("12/25/2023") == datetime(2023, 12, 25)
    
    # Clear failure cases
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_date_string("")
    
    with pytest.raises(ValueError, match="Unable to parse"):
        parse_date_string("not a date")
    
    # Explicit format hint
    result = parse_date_string("25.12.2023", "%d.%m.%Y")
    assert result == datetime(2023, 12, 25)
```

### 8. One Obvious Way
**There should be one-- and preferably only one --obvious way to do it.**

Establish consistent patterns in your codebase. When multiple approaches are possible, choose one and stick with it.

```python
# Good - Consistent pattern for data access
class UserRepository:
    def get_user_by_id(self, user_id):
        return self._query_single("SELECT * FROM users WHERE id = ?", user_id)
    
    def get_user_by_email(self, email):
        return self._query_single("SELECT * FROM users WHERE email = ?", email)
    
    def get_users_by_status(self, status):
        return self._query_multiple("SELECT * FROM users WHERE status = ?", status)

# Avoid - Multiple inconsistent patterns
class UserRepository:
    def get_user_by_id(self, user_id):
        cursor.execute("SELECT * FROM users WHERE id = ?", user_id)
        return cursor.fetchone()
    
    def find_by_email(self, email):  # Different naming
        return User.objects.filter(email=email).first()  # Different ORM
    
    def getUsersByStatus(self, status):  # Different case
        with open('users.json') as f:  # Different storage
            users = json.load(f)
            return [u for u in users if u['status'] == status]
```

**Test Example:**
```python
def test_consistent_repository_pattern():
    """Test that all repository methods follow the same pattern."""
    repo = UserRepository()
    
    # All methods should follow the same interface pattern
    user = repo.get_user_by_id(123)
    assert isinstance(user, (User, type(None)))
    
    user = repo.get_user_by_email("test@example.com")
    assert isinstance(user, (User, type(None)))
    
    users = repo.get_users_by_status("active")
    assert isinstance(users, list)
```

### 9. Timing and Implementation
**Now is better than never. Although never is often better than *right* now.**

Balance urgency with quality. Ship working code, but don't rush to the point of creating technical debt.

```python
# Good - Ship MVP with clear extension points
class PaymentProcessor:
    def __init__(self):
        # Start with basic credit card processing
        self.processors = {
            'credit_card': CreditCardProcessor()
        }
    
    def process_payment(self, payment_method, amount):
        if payment_method not in self.processors:
            raise ValueError(f"Unsupported payment method: {payment_method}")
        
        return self.processors[payment_method].process(amount)
    
    def add_payment_method(self, method_name, processor):
        """Extension point for future payment methods"""
        self.processors[method_name] = processor

# Avoid - Overengineering for theoretical future needs
class PaymentProcessor:
    def __init__(self):
        # Complex plugin system for payments we don't support yet
        self.plugin_manager = PluginManager()
        self.payment_gateway_factory = PaymentGatewayFactory()
        self.transaction_middleware_chain = MiddlewareChain()
        # ... 200 more lines of setup
```

**Test Example:**
```python
def test_payment_processor_mvp():
    """Test that MVP payment processor works and is extensible."""
    processor = PaymentProcessor()
    
    # Core functionality works
    result = processor.process_payment('credit_card', 100.00)
    assert result.success == True
    
    # Extension point works
    processor.add_payment_method('paypal', MockPayPalProcessor())
    result = processor.process_payment('paypal', 50.00)
    assert result.success == True

def test_no_premature_optimization():
    """Test that we don't over-engineer for theoretical needs."""
    processor = PaymentProcessor()
    
    # Should be simple enough to understand quickly
    assert len(processor.__dict__) <= 3  # Keep it simple
    assert hasattr(processor, 'add_payment_method')  # But extensible
```

### 10. Explainable Implementation
**If the implementation is hard to explain, it's a bad idea.**

Your code should be simple enough to explain to a colleague. If it requires extensive documentation to understand, consider refactoring.

```python
# Good - Easy to explain
def calculate_monthly_payment(principal, annual_rate, years):
    """Calculate monthly mortgage payment using standard formula."""
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    
    if monthly_rate == 0:
        return principal / num_payments
    
    factor = (1 + monthly_rate) ** num_payments
    return principal * (monthly_rate * factor) / (factor - 1)

# Avoid - Hard to explain
def calc_pmt(p, r, y):
    mr = r/12
    n = y*12
    return p*(mr*(1+mr)**n)/((1+mr)**n-1) if mr else p/n
```

**Test Example:**
```python
def test_explainable_mortgage_calculation():
    """Test mortgage calculation with clear, explainable logic."""
    # Standard 30-year mortgage at 5% APR
    payment = calculate_monthly_payment(
        principal=300000,
        annual_rate=0.05,
        years=30
    )
    
    # Should be approximately $1610.46
    assert abs(payment - 1610.46) < 0.01
    
    # Zero interest case (easy to verify)
    payment = calculate_monthly_payment(120000, 0.0, 10)
    assert payment == 1000.0  # 120000 / (10 * 12)

def test_implementation_explanation():
    """Test that the implementation matches the explanation."""
    # The formula should be clear enough that we can verify it manually
    # P * (r * (1+r)^n) / ((1+r)^n - 1)
    p, r, n = 1000, 0.01, 12
    
    expected = p * (r * (1 + r)**n) / ((1 + r)**n - 1)
    actual = calculate_monthly_payment(p, r * 12, 1)  # Convert to annual rate
    
    assert abs(actual - expected) < 0.001
```

### 11. Namespaces and Organization
**Namespaces are one honking great idea -- let's do more of those!**

Use modules, classes, and namespaces to organize code logically. Avoid polluting the global namespace.

```python
# Good - Clear namespace organization
from payments.processors import CreditCardProcessor, PayPalProcessor
from payments.validators import validate_credit_card, validate_paypal_account
from payments.exceptions import PaymentError, InsufficientFundsError

class PaymentService:
    def __init__(self):
        self.processors = {
            'credit_card': CreditCardProcessor(),
            'paypal': PayPalProcessor()
        }

# Avoid - Polluted namespace
from payments import *  # Imports everything
import json, os, sys, datetime, requests  # All in global scope

def process_payment(method, amount):
    # Unclear where functions come from
    if validate_card(get_card_info()):
        return charge_card(amount)
```

**Test Example:**
```python
def test_clear_namespacing():
    """Test that imports and organization are clear and contained."""
    # Should be able to trace where functionality comes from
    processor = payments.processors.CreditCardProcessor()
    validator = payments.validators.validate_credit_card("4111111111111111")
    
    assert hasattr(payments.processors, 'CreditCardProcessor')
    assert hasattr(payments.validators, 'validate_credit_card')
    assert hasattr(payments.exceptions, 'PaymentError')

def test_no_namespace_pollution():
    """Test that we don't pollute the global namespace."""
    import payments
    
    # Should use explicit imports, not import *
    with pytest.raises(NameError):
        validate_credit_card("test")  # Should require payments.validators.
```

## Testing Standards

All code changes must include corresponding tests that verify:

1. **Happy path functionality** - The code works as intended
2. **Edge cases** - Boundary conditions and unusual inputs
3. **Error conditions** - Proper error handling and failure modes
4. **Standards compliance** - The code follows these principles

### Test Naming Convention
```python
def test_<functionality>_<specific_case>():
    """Test description explaining what we're verifying."""
```

### Example Test Structure
```python
def test_user_authentication_success():
    """Test that valid credentials authenticate successfully."""
    # Arrange
    user = create_test_user("test@example.com", "secure_password")
    
    # Act
    result = authenticate_user("test@example.com", "secure_password")
    
    # Assert
    assert result.is_authenticated == True
    assert result.user.email == "test@example.com"
```

## Code Review Checklist

When reviewing code, ensure it follows these principles:

- [ ] Code is readable and self-documenting
- [ ] Intent is explicit, not implicit
- [ ] Solution is as simple as possible
- [ ] Nesting is minimal
- [ ] Proper spacing and formatting
- [ ] Errors are handled explicitly
- [ ] No dangerous assumptions or guessing
- [ ] Consistent patterns are used
- [ ] Implementation is explainable
- [ ] Proper namespace organization
- [ ] Comprehensive tests included

## Conclusion

These standards are living guidelines meant to improve code quality and maintainability. When in doubt, choose clarity over cleverness, and always consider the next developer who will read your code—including your future self.

Remember: "Code is read much more often than it is written." Make it count.


Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!