from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import BotEngine
from app.mini_app import create_app

# Mark this file as a selenium test
pytestmark = pytest.mark.selenium


@pytest.fixture(scope="module")
def chrome_driver():
    """Fixture to initialize and quit the Selenium Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without opening a browser window
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


@pytest.fixture
def app(tmp_path):
    """Fixture to create a Flask app instance with a pre-configured engine."""
    storage_path = tmp_path / "test_ui_db.json"
    engine = BotEngine(storage_path=str(storage_path))

    # Create an admin user
    admin_profile = engine.register_user(1, "Admin UI User")
    admin_profile.admin = True

    # Create a regular user with a pending withdrawal for testing
    user_profile = engine.register_user(101, "Test User")
    user_profile.withdrawals.append({
        "request_id": "req-101-1",
        "user_id": 101,
        "amount": 50.0,
        "status": "pending",
        "unique_code": "TESTCODE123"
    })
    engine.save()

    # Create the Flask app with this engine
    flask_app = create_app(engine)
    flask_app.config.update({"TESTING": True})
    return flask_app


def test_admin_dashboard_loads_data(live_server, chrome_driver):
    """
    Tests if the admin dashboard loads initial data correctly.
    """
    live_server.start()
    chrome_driver.get(live_server.url + "/admin")

    # Wait for the stats grid to be populated
    wait = WebDriverWait(chrome_driver, 10)
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#stats-grid .card .value"), "1")) # Wait for Active Users to be > 0

    # Check if key components are loaded
    assert "Admin Dashboard" in chrome_driver.title
    assert "Active Users" in chrome_driver.find_element(By.ID, "stats-grid").text
    assert "Pending Withdrawals" in chrome_driver.page_source
    assert "All Users" in chrome_driver.page_source

    # Check if the pending withdrawal is in the table
    pending_table = chrome_driver.find_element(By.ID, "pending-withdrawals-table")
    assert "req-101-1" in pending_table.text
    assert "50.00" in pending_table.text


def test_admin_approves_withdrawal_via_ui(live_server, chrome_driver):
    """
    Tests the full UI flow of approving a withdrawal.
    """
    live_server.start()
    chrome_driver.get(live_server.url + "/admin")
    wait = WebDriverWait(chrome_driver, 10)

    # 1. Open the approval modal
    approve_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#pending-withdrawals-table .button")))
    approve_button.click()
    modal = wait.until(EC.visibility_of_element_located((By.ID, "approvalModal")))
    assert modal.is_displayed()

    # 2. Enter the code and approve
    code_input = modal.find_element(By.ID, "verification-code")
    code_input.send_keys("TESTCODE123")
    modal.find_element(By.ID, "modal-approve-btn").click()

    # 3. Handle the alert and wait for the modal to disappear
    wait.until(EC.alert_is_present())
    alert = chrome_driver.switch_to.alert
    assert "approved" in alert.text.lower()
    alert.accept()
    wait.until(EC.invisibility_of_element_located((By.ID, "approvalModal")))

    # 4. Verify the table is now empty
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pending-withdrawals-table tbody"), "No pending withdrawals."))
    assert "No pending withdrawals." in chrome_driver.find_element(By.ID, "pending-withdrawals-table").text