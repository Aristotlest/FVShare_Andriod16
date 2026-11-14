"""Prepare an ARM64 compatibility build from the original FVShare package."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile


def replace_method(text, signature, body):
    pattern = rf"(?m)^\.method {re.escape(signature)}\n.*?^\.end method"
    result, count = re.subn(pattern, f".method {signature}\n{body}\n.end method", text, flags=re.S)
    if count != 1:
        raise ValueError(f"Expected exactly one method: {signature}; found {count}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parent
    root = args.decoded
    candidate = args.candidate
    native_dir = root / "lib" / "arm64-v8a"
    names = ["libmodpng.so", "libmodft2.so", "libmodpdfium.so", "libjniPdfium.so", "libc++_shared.so"]
    report = {"pdfium_source": "https://github.com/appuraja1/PdfiumAndroid-16kb", "commit": "8037a684c47fec2e62ec3e9e89e616eac0d596dd", "native_libraries": {}}
    # Verify page alignment and the exported JNI entry points before replacement.
    declarations = (root / "smali_classes11/com/shockwave/pdfium/PdfiumCore.smali").read_text()
    symbols = subprocess.check_output(["nm", "-D", "--defined-only", str(candidate / "libjniPdfium.so")], text=True)
    for name in re.findall(r"^\.method private native (\w+)\(", declarations, re.M):
        if f"Java_com_shockwave_pdfium_PdfiumCore_{name}" not in symbols:
            raise ValueError(f"Missing JNI export: {name}")
    for name in names:
        data = (candidate / name).read_bytes()
        if data[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", data, 18)[0] != 183:
            raise ValueError(f"Not an ARM64 ELF: {name}")
        offset = struct.unpack_from("<Q", data, 32)[0]
        size, count = struct.unpack_from("<HH", data, 54)
        alignments = []
        for index in range(count):
            header = offset + index * size
            if struct.unpack_from("<I", data, header)[0] == 1:
                file_offset, address = struct.unpack_from("<QQ", data, header + 8)
                alignment = struct.unpack_from("<Q", data, header + 48)[0]
                if alignment < 16384 or (address - file_offset) % 16384:
                    raise ValueError(f"Not 16 KB compatible: {name}")
                alignments.append(alignment)
        shutil.copy2(candidate / name, native_dir / name)
        report["native_libraries"][name] = {"sha256": hashlib.sha256(data).hexdigest(), "alignments": alignments}
    # The candidate's SONAME/NEEDED names differ from the old packaging names.
    for old, alias in [("libmodpng.so", "libpng16.so"), ("libmodft2.so", "libfreetype.so"), ("libmodpdfium.so", "libpdfium.so")]:
        shutil.copy2(native_dir / old, native_dir / alias)
    # This build targets the user's ARM64 phone only.
    for directory in (root / "lib").iterdir():
        if directory.is_dir() and directory.name != "arm64-v8a":
            shutil.rmtree(directory)
    pdfium = root / "smali_classes11/com/shockwave/pdfium/PdfiumCore.smali"
    text = pdfium.read_text()
    marker = '    const-string/jumbo v0, "modpng"'
    if text.count(marker) != 1:
        raise ValueError("Unexpected Pdfium loader")
    if 'const-string/jumbo v0, "c++_shared"' not in text:
        text = text.replace(marker, '    const-string/jumbo v0, "c++_shared"\n\n    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n\n' + marker)
    text = replace_method(text, "public static getNumFd(Landroid/os/ParcelFileDescriptor;)I", "    .locals 1\n    invoke-virtual {p0}, Landroid/os/ParcelFileDescriptor;->getFd()I\n    move-result v0\n    return v0")
    pdfium.write_text(text)
    # Merge the complete local resource bundle; keep existing assets if identical.
    with zipfile.ZipFile(workspace / "FVShare_2.4.5_APKPure.xapk") as archive:
        with zipfile.ZipFile(io.BytesIO(archive.read("Android/obb/com.freevisiontech.fvmobile/main.245.com.freevisiontech.fvmobile.obb"))) as obb:
            for entry in obb.infolist():
                if entry.is_dir():
                    continue
                path = Path(entry.filename)
                if path.parts[0] != "assets" or ".." in path.parts:
                    raise ValueError(f"Unexpected OBB path: {path}")
                destination = root / path
                data = obb.read(entry)
                if destination.exists() and destination.read_bytes() != data:
                    report.setdefault("preserved_original_assets", []).append(str(path))
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
    resources = root / "smali_classes33/com/freevisiontech/fvmobile/utils/LocalResourceManager.smali"
    text = resources.read_text()
    # Success is based on an actually packaged resource, not an unconditional bypass.
    text = replace_method(text, "public static expansionFilesDelivered(Landroid/content/Context;)Z", '    .locals 1\n    const-string v0, "updateinfo.json"\n    invoke-static {p0, v0}, Lcom/freevisiontech/fvmobile/utils/LocalResourceManager;->isFileExistOnAssets(Landroid/content/Context;Ljava/lang/String;)Z\n    move-result v0\n    return v0')
    resources.write_text(text)
    splash = root / "smali_classes33/com/freevisiontech/fvmobile/activity/FVSplashActivity.smali"
    text = splash.read_text()
    old = '    const-string/jumbo v3, "android.permission.ACCESS_COARSE_LOCATION"'
    if text.count(old) != 1 and 'const-string/jumbo v3, "android.permission.ACCESS_FINE_LOCATION"' not in text:
        raise ValueError("Unexpected location permission request")
    splash.write_text(text.replace(old, '    const-string/jumbo v3, "android.permission.ACCESS_FINE_LOCATION"'))
    # Preserve target 28: raising it also requires a separate storage/media/BLE migration.
    yml = root / "apktool.yml"
    text = yml.read_text().replace("versionName: 2.4.5", "versionName: 2.4.5-a16-compat1")
    text += "- m4a\n- mp3\n- pdf\n- bin\n- ttf\n"
    yml.write_text(text)
    report["target_sdk"] = 28
    report["status"] = "prepared; runtime validation pending"
    (workspace / "compat-build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    shutil.copy2(candidate / "LICENSE", workspace / "docs/pdfium-candidate-LICENSE.txt")
    print("Compatibility modifications prepared; target SDK remains 28.")


if __name__ == "__main__":
    main()
