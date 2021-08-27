# SHAWL
**Shawl** - this is a Selenium module wrapper that implements a mixture of **PageObject** and **PageElement** patterns. Describing the page structure and element locators in **.yaml** files, and methods for working with elements and pages are in the classes themselves.

### Structure 
- BaseClasses
  - **BasePage** - base class for implementing Your own classes according to a PageObject pattern.
  - **BaseElement** - base class for implementing Your own classes according to a PageElement pattern.
  - **BaseCollection** - base class for implementing Your own classes according to a PageElement pattern that should be a collection.
- Decorators
  - **check_server_error_after** - checks that there are no records with the specified level and message in the logs of the current WebDriver instance from the BasePage instance. If there is an entry, an AssertionError is triggered.
  - **catch_timeout_error** - returns the specified value (False by default) if a TimeoutException was raised during the execution of the method.

### Features of the framework
####Pages and elements description in .yaml files
You need to describe page with elements in .yaml file
Yaml's file structure:
```yaml
page_repr: Page description
first_awesome_element:
  element_type:
    selector: locator
    repr: element name or short representation that will be shown in allure
  another_type:
    selector: locator
    repr: element name or short representation that will be shown in allure
second_awesome_element:
  element_type:
    selector: locator
collections:
  first_awesome_collection:
    element_type:
      selector: locator
    another_type:
      selector: locator
page_strings:
  locator_pattern: //div//{}
  title_text: Some awesome text
```
When .yaml file will be processed `first_awesome_element_element_type` will be added to the instance of the `BaseElement`. Similarly, for all `first_awesome_collection`, with the only difference that instances of the `BaseCollection` class will be declared.

Also, the dictionary `page_strings` will be added to the page, in the same structure as it is described in .yaml file. This dictionary is perfect for storing static text
that you need to search for on a page or for storing certain patterns, whether it is a locator pattern or a message text on a page.

You can add text representations for elements and pages as an `repr` или `page_repr`, and they will be able to use in allure steps by `{0}`.

**Example**
```yaml
page_repr: Login Page
login:
  input:
    id: login
    repr: Login input field
```

```python
import allure
from shawl.core._base_page import BasePage
from shawl.core._base_element import BaseElement

class LoginPage(BasePage):
    
    @allure.step('Fill {0}')
    def fill_login_field(self, val: str):
        self.login_input.type_text(val)
```

As a result You will get allure message `Fill Login input field`.

####Selectors
As a selectors in .yaml file You need to use the same selectors as in selenium for a class By:
- id
- xpath
- link text
- partial link text
- name
- tag name
- class name
- css selector

#### Important things:
- .yaml's file name should be the same as a class that extends `BasePage`. For example - if You had a `class LoginPage(BasePage):` locators for it should be posted in `LoginPage.yaml`.
- .yaml's file name should be unique
- In .yaml file should exist class inheritor from `BaseElement` with name {Key name with capital letter}Element. For example for element `custom` should exist class `class CustomElement(BaseElement): pass`. In another case will be used `BaseElement` class.
- For tags key `collection` (3rd level key) should exist class inheritor `BaseCollection` named as {key name with capital letter}Collection. For example for element `custom` should exist class `class CustomCollection(BaseCollection): pass`. In another case will be used `BaseElement` class.

#### Framework configuration
Here should be part with information about configuration framework
- `source_yaml_path`: path to `project_root_path` to directory with .yaml files. Default value is `resources/dicts/pages`.
- `lazy_load_timeout`: seconds for lazy load `BaseElement.element`. Default value is `5`.
- `wait_timeout`: timeout for waiting appearance element on page. Default value is `5`.
- `project_root_path`: path to root directory. Default value is current directory.
- `use_package_init_first`: flag for searching `BaseElements` classes in current packedge `__init__.py` before searching in `elements_classes_module`. Get `True` or `False`
- `elements_classes_module`: BaseElements classes module name. Should be key from `sys.modules`. Default value - empty string