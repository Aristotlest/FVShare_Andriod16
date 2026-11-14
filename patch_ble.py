"""Patch legacy BLE discovery without changing GATT control protocols."""

import argparse
from pathlib import Path

from prepare_compat import replace_method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    root = parser.parse_args().decoded
    base = root / "smali_classes33/com/freevisiontech/fvmobile"
    vise = base / "ViseBluetooth.smali"
    text = vise.read_text()
    text = replace_method(text, "public getScanFileterList()Ljava/util/List;", """    .locals 1
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V
    return-object v0""")
    # Apply identical settings to the filtered and previously default scan paths.
    text = replace_method(text, "public startLeScan(Landroid/bluetooth/le/ScanCallback;)V", """    .locals 2
    invoke-virtual {p0}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->getScanFileterList()Ljava/util/List;
    move-result-object v0
    invoke-virtual {p0}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->buildScanSettings()Landroid/bluetooth/le/ScanSettings;
    move-result-object v1
    invoke-virtual {p0, v0, v1, p1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->startLeScan(Ljava/util/List;Landroid/bluetooth/le/ScanSettings;Landroid/bluetooth/le/ScanCallback;)V
    return-void""")
    # Surface asynchronous scan failures instead of silently showing an empty list.
    text += """
.method public reportScanFailure(I)V
    .locals 3
    sget-object v0, Lcom/freevisiontech/fvmobile/common/StateScan;->SCAN_DISSCAN:Lcom/freevisiontech/fvmobile/common/StateScan;
    iput-object v0, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth;->scanState:Lcom/freevisiontech/fvmobile/common/StateScan;
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "BLE scan failed, code="
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    const-string v1, "FVCompatBLE"
    invoke-static {v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I
    iget-object v1, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth;->context:Landroid/content/Context;
    if-eqz v1, :done
    const/4 v2, 0x1
    invoke-static {v1, v0, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    :done
    return-void
.end method
"""
    vise.write_text(text)
    model = base / "model/BluetoothLeDevice.smali"
    text = model.read_text()
    text = replace_method(text, "public getName()Ljava/lang/String;", """    .locals 2
    iget-object v0, p0, Lcom/freevisiontech/fvmobile/model/BluetoothLeDevice;->mRecordStore:Lcom/freevisiontech/fvmobile/model/adrecord/AdRecordStore;
    if-eqz v0, :cached
    invoke-virtual {v0}, Lcom/freevisiontech/fvmobile/model/adrecord/AdRecordStore;->getLocalNameComplete()Ljava/lang/String;
    move-result-object v1
    if-nez v1, :found
    invoke-virtual {v0}, Lcom/freevisiontech/fvmobile/model/adrecord/AdRecordStore;->getLocalNameShort()Ljava/lang/String;
    move-result-object v1
    if-nez v1, :found
    :cached
    iget-object v0, p0, Lcom/freevisiontech/fvmobile/model/BluetoothLeDevice;->mDevice:Landroid/bluetooth/BluetoothDevice;
    invoke-virtual {v0}, Landroid/bluetooth/BluetoothDevice;->getName()Ljava/lang/String;
    move-result-object v1
    :found
    return-object v1""")
    model.write_text(text)
    callback = base / "callback/scan/PeriodLScanCallback.smali"
    text = callback.read_text()
    marker = "    invoke-virtual {v3}, Landroid/bluetooth/le/ScanRecord;->getBytes()[B"
    if text.count(marker) != 1:
        raise ValueError("Unexpected scan callback")
    text = text.replace(marker, "    if-eqz v3, :goto_0\n\n" + marker)
    text += """
.method public onScanFailed(I)V
    .locals 1
    const/4 v0, 0x0
    iput-boolean v0, p0, Lcom/freevisiontech/fvmobile/callback/scan/PeriodLScanCallback;->isScanning:Z
    invoke-virtual {p0}, Lcom/freevisiontech/fvmobile/callback/scan/PeriodLScanCallback;->removeHandlerMsg()Lcom/freevisiontech/fvmobile/callback/scan/PeriodLScanCallback;
    iget-object v0, p0, Lcom/freevisiontech/fvmobile/callback/scan/PeriodLScanCallback;->viseBluetooth:Lcom/freevisiontech/fvmobile/ViseBluetooth;
    if-eqz v0, :done
    invoke-virtual {v0, p1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportScanFailure(I)V
    :done
    return-void
.end method
"""
    callback.write_text(text)
    yml = root / "apktool.yml"
    text = yml.read_text().replace("versionName: 2.4.5-a16-compat1", "versionName: 2.4.5-a16-compat2").replace("versionCode: 245", "versionCode: 246")
    yml.write_text(text)
    print("BLE patch applied: no hardware UUID filter, advertised name fallback, explicit scan failures.")


if __name__ == "__main__":
    main()
