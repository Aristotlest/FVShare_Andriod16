# FVShare Android 16 兼容适配

FVShare 2.4.5 的非官方 ARM64 兼容测试构建及补丁脚本，面向 Freevision / VILTA 云台。使用 AI 辅助分析和修改；本仓库不是原厂 Android 源码或完整 Gradle 工程，也不代表原厂背书。

## 下载

当前最新构建：**2.4.5-a16-compat7**（versionCode 251）。

- [下载 compat7 APK](https://github.com/Aristotlest/FVShare_Andriod16/releases/download/v2.4.5-a16-compat7/FVShare_Android16_compat7.apk)
- [发布说明及校验文件](https://github.com/Aristotlest/FVShare_Andriod16/releases/tag/v2.4.5-a16-compat7)

这是非官方兼容构建，不保证所有手机和云台型号均适用。

用户已反馈真机验证通过：小米14、小米17ultra，澎湃4.0.5.0；扫描、连接、云台控制及拍摄均正常。这是用户提供的测试结果，不是发布助手独立复测，也不代表其他机型或全部功能均已覆盖。

## 安装与限制

- 仅包含 ARM64 原生库；保留 min SDK 21、target SDK 28。面向 Android 16 的兼容修复不等于升级 target SDK 至 36。
- 包名仍为 `com.freevisiontech.fvmobile`，采用本地兼容版签名，不是原厂签名；通常无法直接覆盖原厂版本。
- 如需卸载原厂版才能安装，请先备份应用数据。卸载会清除数据。
- 与相同兼容版证书签名的前版可尝试覆盖安装；不要使用其他来源的同名包来推定签名兼容。
- 按需授予相机、麦克风、精确位置权限，打开蓝牙与系统定位，再进行扫描测试。
- 不要以云台固件更新作为兼容性测试，也不要把发现服务等同于控制协议握手成功。

## compat7 改动

在初始化前检查原 App 已知的三个服务 UUID，仅当实际 GATT 服务表中恰好存在一个已知服务时，更新当前服务配置；不猜测未知 UUID，不修改云台固件或控制指令。

诊断码：5001 表示唯一已知服务被选中，-5001 表示无已知服务，-5002 表示存在多个已知服务而未自动选择。后续需结合 3003、4001、2000 与实际界面/日志判断初始化状态。

## 发布前重新检查

- APK SHA-256：`a153c92b239795f59a2c2a8f3db6bcb9d4dd4f0b4ab1cd3cd0118e7b7f7703c3`
- APK 字节数：149349213；ZIP CRC 检查通过。
- 15 个 ARM64 ELF 的 LOAD 段均满足 16 KB 对齐及地址/偏移同余检查；这不是完整运行兼容性证明。
- uber-apk-signer 1.3.0 的 zipalign 与 v1/v2/v3 签名验证通过。
- 签名工具仍报告 `META-INF/services/javax.annotation.processing.Processor` 条目不受签名保护的警告，未修改现有 APK 消除此警告；请参见 Release 说明。不可将本次验证描述为“无警告”。
- 发布助手本次未连接手机独立复测；用户已确认上述两款手机的扫描、连接、云台控制与拍摄正常。

## 项目内容与恢复构建

仓库仅包含适配脚本、构建说明和相关检查记录。原版 APK/XAPK、反编译树、签名密钥以及其他无关工作区文档不在 Git 仓库内。APK 仅作为 Release 附件分发。

恢复构建需自行准备合法取得的原始 `FVShare_2.4.5_original.apk`、含 OBB 的 `FVShare_2.4.5_APKPure.xapk`、候选 PDFium 库及相应工具。当前本地工作区没有找到原 XAPK，仓库不能单独完成全量重建。

工具：Python 3、JDK、Apktool 3.0.3、uber-apk-signer 1.3.0、`nm`。候选库来源固定为 [appuraja1/PdfiumAndroid-16kb](https://github.com/appuraja1/PdfiumAndroid-16kb/tree/8037a684c47fec2e62ec3e9e89e616eac0d596dd)。候选库文件哈希见 `compat-build-report.json`。

从原包新解码的目录开始，依次执行一次：

```text
prepare_compat.py <decoded> <candidate>
patch_ble.py <decoded>
patch_gatt.py <decoded>
patch_timeout.py <decoded>
patch_gatt_diagnostics.py <decoded>
patch_init_diagnostics.py <decoded>
patch_service_selection.py <decoded>
```

这些补丁并非通用、幂等的改包工具，不应重复应用到已修改的目录。使用 Apktool 强制重建，再使用安全保存在本机的同一签名密钥签名并验证；私钥不得上传。详细历史见：

- [构建说明（含早期版本历史）](docs/fvshare-android16-build.md)
- [各版变更与验证边界](docs/task-progress/fvshare-android16.md)
- [第三方归属与发布边界](NOTICE.md)

## 问题反馈

请提供手机型号、系统版本、兼容版编号、App 显示的阶段码与去除个人信息的 `FVCompatBLE` 日志。不要提交密码、账号令牌、签名密钥或完整私人设备日志。
