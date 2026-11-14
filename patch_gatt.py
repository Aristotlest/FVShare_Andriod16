"""Repair GATT lifecycle and expose connection-stage diagnostics."""

import argparse
from pathlib import Path


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Unexpected occurrence count: {old}")
    return text.replace(old, new)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    root = parser.parse_args().decoded
    base = root / "smali_classes33/com/freevisiontech/fvmobile"
    file = base / "ViseBluetooth.smali"
    text = file.read_text()
    old = "    invoke-virtual {p1, v1, p2, v2}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;"
    text = replace_once(text, old, """    const/4 p2, 0x0
    const/4 v3, 0x2
    invoke-virtual {p1, v1, p2, v2, v3}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;I)Landroid/bluetooth/BluetoothGatt;""")
    # Store the pending GATT so the existing timeout can actually close it.
    text = replace_once(text, "    move-result-object v1\n\n    monitor-exit p0\n\n    return-object v1", "    move-result-object v1\n\n    iput-object v1, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth;->bluetoothGatt:Landroid/bluetooth/BluetoothGatt;\n\n    monitor-exit p0\n\n    return-object v1")
    # Reuse a lightweight diagnostic UI with an explicit stage label.
    start = text.index(".method public reportScanFailure(I)V")
    method = text[start:]
    method = method.replace("reportScanFailure(I)V", "reportGattStage(I)V").replace("BLE scan failed, code=", "GATT stage/code=")
    method = method.replace("    sget-object v0, Lcom/freevisiontech/fvmobile/common/StateScan;->SCAN_DISSCAN:Lcom/freevisiontech/fvmobile/common/StateScan;\n    iput-object v0, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth;->scanState:Lcom/freevisiontech/fvmobile/common/StateScan;\n", "")
    text += method
    file.write_text(text)
    file = base / "ViseBluetooth$2.smali"
    text = file.read_text()
    # Cache refresh after discovery invalidates the service table being used.
    text = replace_once(text, "    invoke-virtual {v0}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->refreshDeviceCache()Z", "    # Keep the freshly discovered service table intact.")
    text = replace_once(text, "    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->discoverServices()Z", """    iget-object v0, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth$2;->this$0:Lcom/freevisiontech/fvmobile/ViseBluetooth;
    const/16 v1, 0x3e9
    invoke-virtual {v0, v1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->discoverServices()Z
    move-result v1
    if-nez v1, :cond_0
    const/16 v1, -0x3e9
    invoke-virtual {v0, v1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V""")
    marker = "    .line 182\n    :cond_0\n    if-nez p2, :cond_1"
    text = replace_once(text, marker, """    .line 182
    :cond_0
    iget-object v0, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth$2;->this$0:Lcom/freevisiontech/fvmobile/ViseBluetooth;
    invoke-virtual {v0, p2}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V
    if-nez p2, :cond_1""")
    file.write_text(text)
    yml = root / "apktool.yml"
    text = yml.read_text().replace("versionCode: 246", "versionCode: 247").replace("2.4.5-a16-compat2", "2.4.5-a16-compat3")
    yml.write_text(text)
    print("GATT lifecycle patch applied; stage 1001=link connected, -1001=discovery refused, 0=discovery success.")


if __name__ == "__main__":
    main()
