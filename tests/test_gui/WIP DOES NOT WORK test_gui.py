from pytestqt import qtbot
import pytest

from pagos.gui.maingui import Main


def test_main(qtbot):
    M = Main()

    with qtbot.waitSignal(M.right.datatable.changed, timeout=10000) as blocker:
        M.importdata(
            providedpath="/home/stanley/Code/repos/PAGOS/PAGOS/TEMP DATA FOR TESTING.csv"
        )

    assert M.filename
