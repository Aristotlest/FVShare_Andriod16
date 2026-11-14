"""Select a unique known Freevision service from the discovered GATT table."""

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
.method public selectKnownService(Landroid/bluetooth/BluetoothGatt;)V
    .locals 7
    sget-object v0, Lcom/freevisiontech/fvmobile/common/BleConstant;->SERVICE_UUIDS:[Ljava/lang/String;
    const/4 v1, 0x0
    const/4 v2, 0x0
    const/4 v3, 0x0
    :loop
    array-length v4, v0
    if-ge v1, v4, :selected
    aget-object v4, v0, v1
    invoke-static {v4}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;
    move-result-object v5
    invoke-virtual {p1, v5}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;
    move-result-object v5
    if-eqz v5, :next
    add-int/lit8 v2, v2, 0x1
    move-object v3, v4
    :next
    add-int/lit8 v1, v1, 0x1
    goto :loop
    :selected
    const/4 v4, 0x1
    if-ne v2, v4, :ambiguous
    sput-object v3, Lcom/freevisiontech/fvmobile/common/BleConstant;->SERVICE_UUID_CONFIG:Ljava/lang/String;
    sput-object v3, Lcom/freevisiontech/fvmobile/utils/BlePtzParasConstant;->GET_CURRENT_PTZ_UUID:Ljava/lang/String;
    const/16 v4, 0x1389
    invoke-virtual {p0, v4}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V
    return-void
    :ambiguous
    const/16 v4, -0x1389
    if-eqz v2, :report
    const/16 v4, -0x138a
    :report
    invoke-virtual {p0, v4}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportGattStage(I)V
    return-void
.end method
"""
    path.write_text(text)
    path = base / "ViseBluetooth$2.smali"
    text = path.read_text()
    marker = "    invoke-virtual {v0, p1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportServiceMatch(Landroid/bluetooth/BluetoothGatt;)V"
    text = replace_once(text, marker, "    invoke-virtual {v0, p1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->selectKnownService(Landroid/bluetooth/BluetoothGatt;)V\n" + marker)
    path.write_text(text)
    yml = root / "apktool.yml"
    yml.write_text(yml.read_text().replace("versionCode: 250", "versionCode: 251").replace("2.4.5-a16-compat6", "2.4.5-a16-compat7"))
    print("Unique known service selection added before service initialization.")


if __name__ == "__main__":
    main()
