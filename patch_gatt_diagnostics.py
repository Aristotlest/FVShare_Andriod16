"""Keep diagnostic Toasts off the Bluetooth callback thread."""

import argparse
from pathlib import Path

from prepare_compat import replace_method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    root = parser.parse_args().decoded
    path = root / "smali_classes33/com/freevisiontech/fvmobile/ViseBluetooth.smali"
    text = path.read_text()
    text = replace_method(text, "public reportGattStage(I)V", """    .locals 3
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "GATT stage/code="
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    const-string v1, "FVCompatBLE"
    invoke-static {v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I
    new-instance v1, Lcom/freevisiontech/fvmobile/CompatBleToast;
    iget-object v2, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth;->context:Landroid/content/Context;
    invoke-direct {v1, v2, v0}, Lcom/freevisiontech/fvmobile/CompatBleToast;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    invoke-virtual {p0, v1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->runOnMainThread(Ljava/lang/Runnable;)V
    return-void""")
    path.write_text(text)
    yml = root / "apktool.yml"
    yml.write_text(yml.read_text().replace("versionCode: 248", "versionCode: 249").replace("2.4.5-a16-compat4", "2.4.5-a16-compat5"))
    print("GATT stage diagnostics now dispatched to the main thread.")


if __name__ == "__main__":
    main()
