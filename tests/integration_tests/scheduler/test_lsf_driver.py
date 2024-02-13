import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Set

import pytest

from ert.scheduler import Driver, LsfDriver
from ert.scheduler.event import FinishedEvent, StartedEvent


@pytest.fixture(autouse=True)
def mock_lsf(pytestconfig, monkeypatch, tmp_path):
    if pytestconfig.getoption("lsf"):
        # User provided --lsf, which means we should use the actual LSF
        # cluster without mocking anything.""
        return

    bin_path = Path(__file__).parent / "bin"

    monkeypatch.setenv("PATH", f"{bin_path}:{os.environ['PATH']}")
    monkeypatch.setenv("PYTEST_TMP_PATH", str(tmp_path))
    monkeypatch.setenv("PYTHON", sys.executable)


async def poll(driver: Driver, expected: Set[int], *, started=None, finished=None):
    poll_task = asyncio.create_task(driver.poll())
    completed = set()
    try:
        while True:
            # await poll_task
            event = await driver.event_queue.get()
            if isinstance(event, StartedEvent):
                if started:
                    await started(event.iens)
            elif isinstance(event, FinishedEvent):
                if finished is not None:
                    await finished(event.iens, event.returncode, event.aborted)
                completed.add(event.iens)
                if completed == expected:
                    break
    finally:
        poll_task.cancel()


@pytest.mark.timeout(5)
@pytest.mark.integration_test
async def test_submit(tmp_path):
    driver = LsfDriver()
    await driver.submit(0, f"echo test > {tmp_path}/test")
    await poll(driver, {0})

    assert (tmp_path / "test").read_text(encoding="utf-8") == "test\n"


async def test_submit_something_that_fails():
    driver = LsfDriver()
    finished_called = False

    async def finished(iens, returncode, aborted):
        assert iens == 0
        assert returncode == 1
        assert aborted is True
        nonlocal finished_called
        finished_called = True

    await driver.submit(0, "exit 1")
    await poll(driver, {0}, finished=finished)

    assert finished_called


@pytest.mark.timeout(5)
async def test_kill():
    driver = LsfDriver()
    aborted_called = False

    async def started(iens):
        nonlocal driver
        await driver.kill(iens)

    async def finished(iens, returncode, aborted):
        assert iens == 0
        assert returncode == 1  # LSF cant get returncodes
        assert aborted is True

        nonlocal aborted_called
        aborted_called = True

    await driver.submit(0, "sleep 3")
    await poll(driver, {0}, started=started, finished=finished)
    assert aborted_called


@pytest.mark.parametrize("runpath_supplied", [(True), (False)])
async def test_lsf_info_file_in_runpath(runpath_supplied, tmp_path):
    driver = LsfDriver()
    os.chdir(tmp_path)
    if runpath_supplied:
        await driver.submit(0, "exit 0", runpath=str(tmp_path))
    else:
        await driver.submit(0, "exit 0")

    await poll(driver, {0})

    if runpath_supplied:
        assert json.loads(
            (tmp_path / "lsf_info.json").read_text(encoding="utf-8")
        ).keys() == {"job_id"}

    else:
        assert not Path("lsf_info.json").exists()


async def test_job_name():
    driver = LsfDriver()
    iens: int = 0
    await driver.submit(iens, "sleep 99", name="my_job_name")
    jobid = driver._iens2jobid[iens]
    bjobs_process = await asyncio.create_subprocess_exec(
        "bjobs",
        jobid,
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await bjobs_process.communicate()
    assert "my_job_name" in stdout.decode()


@pytest.mark.parametrize(
    "actual_returncode, returncode_that_ert_sees",
    [
        ([0, 0]),
        ([1, 1]),
        ([2, 1]),
        ([255, 1]),
        ([256, 0]),  # return codes are 8 bit.
    ],
)
async def test_lsf_driver_masks_returncode(actual_returncode, returncode_that_ert_sees):
    """actual_returncode is the returncode from job_dispatch.py (or whatever is submitted)

    The LSF driver is not picking up this returncode, it will only look at the
    status the job obtains through bjobs, which is success/failure.
    """
    driver = LsfDriver()

    async def finished(iens, returncode, aborted):
        assert iens == 0
        assert returncode == returncode_that_ert_sees
        assert aborted == (returncode_that_ert_sees != 0)

    await driver.submit(0, f"exit {actual_returncode}")
    await poll(driver, {0}, finished=finished)
