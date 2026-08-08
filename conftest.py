"""Root pytest configuration.

Excludes the Selenium-based manual UI test (app/test_admin_ui.py) from the
automated test collection, since it requires the `selenium` package and a
browser driver that are not part of the default test dependencies.
"""
import os

# Files that should be skipped by pytest during collection.
# Applied relative to the project root.
collect_ignore = ["app/test_admin_ui.py"]
