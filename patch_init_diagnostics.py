"""Expose service matching and notification setup without guessing UUIDs."""

import argparse
from pathlib import Path

from patch_gatt import replace_once


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    root = parser.parse_args().decoded
    base = root / "smali_classes33/com/freevisiontech/fvmobile"
    path = base / "ViseBluetooth.smali"
    text = path.read_text()
    text += """
.method public reportServiceMatch(Landroid/bluetooth/BluetoothGatt;)V
    .locals 5
    const/16 v0, -0xbb9
    sget-object v1, Lcom/freevisiontech/fvmobile/common/BleConstant;->SERVICE_UUID_CONFIG:Ljava/lang/String;
    if-eqz v1, :report
    invoke-static {v1}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;
    move-result-object v1
    invoke-virtual {p1, v1}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;
    move-result-object v1
    const/16 v0, -0xbba
    if-eqz v1, :report
    const/16 v0, 0xbb8
    invoke-virtual {v1}, Landroid/bluetooth/BluetoothGattService;->getCharacteristics()Ljava/util/List;
    move-result-object v1
    invoke-interface {v1}, Ljava/util/List;->iterator()Ljava/util/Iterator;
    move-result-object v1
    :loop
    invoke-interface {v1}, Ljava/util/Iterator;->hasNext()Z
    move-result v2
    if-eqz v2, :report
    invoke-interface {v1}, Ljava/util/Iterator;->next()Ljava/lang/Object;
    move-result-object v2
    check-cast v2, Landroid/bluetooth/BluetoothGattCharacteristic;
    invoke-virtual {v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getProperties()I
    move-result v2
    and-int/lit8 v3, v2, 0x8
    if-eqz v3, :notify
    or-int/lit8 v0, v0, 0x1
    :notify
    and-int/lit8 v3, v2, 0x10
    if-eqz v3, :loop
    or-int/lit8 v0, v0, 0x2
    goto :loop
    :report
    invoke-virtual {p0, v0}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V
    return-void
.end method
"""
    # 3000 has its two least significant bits clear: +1 WRITE, +2 NOTIFY.
    text = replace_once(text, "    invoke-virtual {p1, v0}, Landroid/bluetooth/BluetoothGatt;->writeDescriptor(Landroid/bluetooth/BluetoothGattDescriptor;)Z", """    invoke-virtual {p1, v0}, Landroid/bluetooth/BluetoothGatt;->writeDescriptor(Landroid/bluetooth/BluetoothGattDescriptor;)Z
    move-result v2
    if-eqz v2, :compat_subscribe_rejected
    const/16 v2, 0xfa1
    goto :compat_subscribe_report
    :compat_subscribe_rejected
    const/16 v2, -0xfa1
    :compat_subscribe_report
    invoke-virtual {p0, v2}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V""")
    path.write_text(text)
    path = base / "ViseBluetooth$2.smali"
    text = path.read_text()
    marker = "    invoke-static {v0, p1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->access$202(Lcom/freevisiontech/fvmobile/ViseBluetooth;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;"
    text = replace_once(text, marker, marker + "\n    invoke-virtual {v0, p1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportServiceMatch(Landroid/bluetooth/BluetoothGatt;)V")
    marker = "    .line 314\n    new-instance v0, Lcom/freevisiontech/fvmobile/utils/Event;"
    text = replace_once(text, marker, """    iget-object v0, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth$2;->this$0:Lcom/freevisiontech/fvmobile/ViseBluetooth;
    add-int/lit16 v1, p3, 0x7d0
    invoke-virtual {v0, v1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V
    .line 314
    new-instance v0, Lcom/freevisiontech/fvmobile/utils/Event;""")
    path.write_text(text)
    yml = root / "apktool.yml"
    yml.write_text(yml.read_text().replace("versionCode: 249", "versionCode: 250").replace("2.4.5-a16-compat5", "2.4.5-a16-compat6"))
    print("Service match and CCCD diagnostics added; protocol unchanged.")


if __name__ == "__main__":
    main()
