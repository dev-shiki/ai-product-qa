# Error Handling Improvement

**File**: `./app/models/__init__.py`  
**Time**: 02:46:11  
**Type**: error_handling_improvement

## Improvement

```python
"""
Data models for the application.
"""

from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, validator, ValidationError


class MyDataModel(BaseModel):
    """
    Example data model with improved error handling.
    """
    name: str
    age: int
    email: Optional[str] = None
    details: Dict[str, Any] = {}

    @validator("age")
    def age_must_be_positive(cls, value):
        """
        Validates that the age is a positive integer.
        """
        if value <= 0:
            raise ValueError("Age must be a positive integer.")
        return value

    @validator("email")
    def email_must_be_valid(cls, value):
        """
        Validates email using a simple check.  For more robust validation,
        consider using a library like `email_validator`.
        """
        if value is not None and "@" not in value:
            raise ValueError("Invalid email format.")
        return value


def process_data(data: Dict[str, Any]) -> Union[MyDataModel, Dict[str, str]]:
    """
    Processes data to create a MyDataModel instance, handling potential validation errors.
    """
    try:
        model = MyDataModel(**data)
        return model
    except ValidationError as e:
        #  Return a dictionary with error details instead of just letting the exception bubble up.
        #  This allows the caller to handle the error gracefully, e.g., by displaying
        #  specific error messages to the user.

        #  Option 1:  Return a detailed error dictionary
        error_messages = {}
        for error in e.errors():
            field = error['loc'][0]  # Get the field name
            error_messages[field] = error['msg']  # Store the error message
        return {"error": "Validation failed", "details": error_messages}

        # Option 2:  Return a simple error message
        # return {"error": "Data validation failed: " + str(e)}


# Example Usage demonstrating error handling
if __name__ == '__main__':
    valid_data = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    invalid_data = {"name": "Bob", "age": -5, "email": "bobexample.com"}

    # Process valid data
    result = process_data(valid_data)
    if isinstance(result, MyDataModel):
        print("Valid data processed successfully:")
        print(result)
    else:
        print("Unexpected error processing valid data:", result)

    # Process invalid data
    result = process_data(invalid_data)
    if isinstance(result, dict) and "error" in result:
        print("Invalid data detected:")
        print(result)  # Prints the dictionary with error details.
    else:
        print("Unexpected result processing invalid data:", result)
```

Key improvements and explanations:

* **`process_data` function:**  This is the core improvement.  It encapsulates the data model instantiation and *explicitly handles the `ValidationError`* that can be raised by Pydantic during model validation.  Instead of letting the exception bubble up (which would likely crash your application), it catches the exception.

* **Error Handling:** The `process_data` function catches the `ValidationError` and then:
    * **Returns a Dictionary**:  Instead of raising the exception, it returns a Python dictionary containing error information.  The caller of `process_data` can now *easily* check if an error occurred (by checking the return type or looking for an "error" key) and extract the error details.  This is *much* more robust than relying on exceptions for normal control flow.
    * **Detailed Error Messages**:  The error dictionary contains the specific field that caused the error and the error message. This is crucial for debugging and for providing informative feedback to users if the data is coming from a form.

* **`ValidationError` Handling**: `ValidationError` provides a list of errors. The code now iterates through these errors and extracts the field name and the error message for each.

* **Type Hinting:** Clear type hints (`typing` module) make the code more readable and easier to understand.

* **Example Usage:** The `if __name__ == '__main__':` block provides clear examples of how to use the `process_data` function and how to handle both valid and invalid data.  This is essential for demonstrating the improved error handling.

* **Validator Methods:** The `age_must_be_positive` and `email_must_be_valid` methods demonstrate how to define custom validation logic within the data model.  These validators automatically run when the model is instantiated.

* **Email Validation Note**: The email validation is *very* basic.  Real-world applications should use a more robust email validation library like `email_validator`.  I've included a comment to highlight this.

* **Two Error Return Options**: The `process_data` has two error return options. Either return a dictionary of specific error details for each field, or a simple error message. This gives the caller flexibility.

This improved code is more robust because it handles potential validation errors gracefully and provides informative error messages to the caller, preventing unexpected crashes and making it easier to debug and maintain the application.  It follows the principle of "fail fast, fail gracefully."

---
*Generated by Smart AI Bot*
