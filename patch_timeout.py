"""Clear stuck auto-connect UI and expose link callback status."""

import argparse
from pathlib import Path

from patch_gatt import replace_once


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    root = parser.parse_args().decoded
    base = root / "smali_classes33/com/freevisiontech/fvmobile"
    path = base / "fragment/FVPTZFragment.smali"
    text = path.read_text()
    marker = "    :sswitch_3\n    iput-boolean v9, p0, Lcom/freevisiontech/fvmobile/fragment/FVPTZFragment;->isConnected:Z"
    text = replace_once(text, marker, marker + """
    iput-boolean v9, p0, Lcom/freevisiontech/fvmobile/fragment/FVPTZFragment;->isAutoConnect:Z
    iget-object v6, p0, Lcom/freevisiontech/fvmobile/fragment/FVPTZFragment;->ptzMenuSwitcher:Lcom/freevisiontech/fvmobile/activity/FVHomeActivity$PtzMenuSwitcher;
    if-eqz v6, :compat_timeout_hint_done
    invoke-interface {v6}, Lcom/freevisiontech/fvmobile/activity/FVHomeActivity$PtzMenuSwitcher;->hideAutoConnectHint()V
    :compat_timeout_hint_done
""")
    path.write_text(text)
    path = base / "ViseBluetooth$2.smali"
    text = path.read_text()
    marker = '    const-string/jumbo v1, "onConnectionStateChange  status: "'
    # Report both status and state on every link callback. Existing locals are sufficient.
    text = replace_once(text, "    .line 154\n    const/4 v0, 0x2", """    iget-object v0, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth$2;->this$0:Lcom/freevisiontech/fvmobile/ViseBluetooth;
    invoke-virtual {v0, p2, p3}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->reportLinkState(II)V
    .line 154
    const/4 v0, 0x2""")
    path.write_text(text)
    path = base / "ViseBluetooth.smali"
    text = path.read_text()
    # This helper runs on the main Handler; Toasts from background callbacks are unreliable.
    text += """
.method public reportLinkState(II)V
    .locals 3
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "BLE link status="
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v1, ", state="
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    const-string v1, "FVCompatBLE"
    invoke-static {v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I
    new-instance v1, Lcom/freevisiontech/fvmobile/CompatBleToast;
    iget-object v2, p0, Lcom/freevisiontech/fvmobile/ViseBluetooth;->context:Landroid/content/Context;
    invoke-direct {v1, v2, v0}, Lcom/freevisiontech/fvmobile/CompatBleToast;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    invoke-virtual {p0, v1}, Lcom/freevisiontech/fvmobile/ViseBluetooth;->runOnMainThread(Ljava/lang/Runnable;)V
    return-void
.end method
"""
    path.write_text(text)
    (base / "CompatBleToast.smali").write_text(""".class public Lcom/freevisiontech/fvmobile/CompatBleToast;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.field private context:Landroid/content/Context;
.field private message:Ljava/lang/String;
.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/freevisiontech/fvmobile/CompatBleToast;->context:Landroid/content/Context;
    iput-object p2, p0, Lcom/freevisiontech/fvmobile/CompatBleToast;->message:Ljava/lang/String;
    return-void
.end method
.method public run()V
    .locals 3
    iget-object v0, p0, Lcom/freevisiontech/fvmobile/CompatBleToast;->context:Landroid/content/Context;
    if-eqz v0, :done
    iget-object v1, p0, Lcom/freevisiontech/fvmobile/CompatBleToast;->message:Ljava/lang/String;
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    :done
    return-void
.end method
""")
    yml = root / "apktool.yml"
    yml.write_text(yml.read_text().replace("versionCode: 247", "versionCode: 248").replace("2.4.5-a16-compat3", "2.4.5-a16-compat4"))
    print("Timeout UI fixed; main-thread link status diagnostics added.")


if __name__ == "__main__":
    main()
